#! /usr/bin/env/python

from flask import Flask, render_template, redirect, flash, url_for

# data model
import peewee
from flask.ext import admin, login
from flask.ext.admin import AdminIndexView
from flask.ext.admin.contrib.peewee import ModelView

# security
from flask.ext.security import Security, PeeweeUserDatastore, \
    UserMixin, RoleMixin, login_required, roles_required
from flask.ext.login import current_user, current_app

# forms
from flask_wtf import Form
from wtforms import BooleanField, TextField, IntegerField, FloatField, validators

app = Flask(__name__)

# data model
db = peewee.SqliteDatabase('pythia.sqlite', check_same_thread=False)

class BaseModel(peewee.Model):
    class Meta:
        database = db

class User(BaseModel, UserMixin):
    email = peewee.TextField()
    password = peewee.TextField()
    active = peewee.BooleanField(default=True)
    confirmed_at = peewee.DateTimeField(null=True)

    def __unicode__(self):
        return self.email

class Role(BaseModel, RoleMixin):
    name = peewee.CharField(unique=True)
    description = peewee.TextField(null=True)

    def __unicode__(self):
        return self.name

class UserRoles(BaseModel):
    user = peewee.ForeignKeyField(User, related_name='roles')
    role = peewee.ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)

class Market(BaseModel):
    name = peewee.TextField()
    description = peewee.TextField()
    status = peewee.TextField()
    opening_date = peewee.DateTimeField()
    closing_date = peewee.DateTimeField()
    price = peewee.FloatField()
    volume = peewee.FloatField()

    def __unicode__(self):
        return self.name

class MarketHistory(BaseModel):
    market = peewee.ForeignKeyField(Market, related_name='market', null=True)
    date = peewee.DateTimeField()
    price = peewee.FloatField()
    volume = peewee.FloatField()

class Stock(BaseModel):
    market = peewee.ForeignKeyField(Market, related_name='stocks', null=True)
    user = peewee.ForeignKeyField(User, related_name='stocks', null=True)
    quantity = peewee.IntegerField()

class Order(BaseModel):
    market = peewee.ForeignKeyField(Market, related_name='orders', null=True)
    user = peewee.ForeignKeyField(User, related_name='orders', null=True)
    price = peewee.FloatField()
    quantity = peewee.IntegerField()
    type = peewee.TextField()
    status = peewee.TextField()

class Account(BaseModel):
    user = peewee.ForeignKeyField(User, related_name='account', null=True)
    market = peewee.ForeignKeyField(Market, related_name='account', null=True)
    balance = peewee.FloatField()

class Transaction(BaseModel):
    account = peewee.ForeignKeyField(Account, related_name='transactions')
    date = peewee.DateTimeField()
    amount = peewee.FloatField()

def create_tables():
    for Model in (User, Role, UserRoles, Market, MarketHistory, Stock, Order, Account, Transaction):
        Model.create_table(fail_silently=True)

# admin
class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()

class MyAdminIndexView(AuthMixin, AdminIndexView):
    pass

class BaseAdmin(AuthMixin, ModelView):
    pass

class UserAdmin(BaseAdmin):
    column_exclude_list = ['password']

class RoleAdmin(BaseAdmin):
    pass

class UserRolesAdmin(BaseAdmin):
    pass

class MarketAdmin(BaseAdmin):
    pass

admin = admin.Admin(app, name='Pythia admin', index_view=MyAdminIndexView())
admin.add_view(UserAdmin(User))
admin.add_view(RoleAdmin(Role))
admin.add_view(UserRolesAdmin(UserRoles))
admin.add_view(MarketAdmin(Market))

# security
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_HASH'] = 'plaintext'
app.config['SECURITY_PASSWORD_SALT'] = 'super-salt'

user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
security = Security(app, user_datastore)

# forms
class OrderForm(Form):
    price = FloatField('Price', [validators.NumberRange(min=0)])
    quantity = IntegerField('Quantity', [validators.NumberRange(min=1)])
    action = TextField('Action')

# action
@app.route('/')
@login_required
def home():
    markets = Market.select()

    return render_template('home.html', markets=markets)

@app.route('/market/<int:id>', methods=['GET', 'POST'])
@login_required
def market(id):
    market = Market.get(Market.id == id)
    user = current_user
    buy_form = OrderForm()
    sell_form = OrderForm()

    if buy_form.validate_on_submit():
        order = Order.create(
            market=market.id, 
            user=user.id, 
            price=buy_form.price.data, 
            quantity=buy_form.quantity.data,
            type='buy' if buy_form.action.data == 'BUY' else 'sell',
            status='pending')
        flash('Your order have been registered')
        return redirect(url_for('market', id=market.id))

    sell_orders = Order.select().where(Order.market == market.id, Order.type == 'sell').order_by(Order.price.asc())
    buy_orders = Order.select().where(Order.market == market.id , Order.type == 'buy').order_by(Order.price.desc())

    return render_template('market.html', 
        market=market, user=user, buy_form=buy_form, sell_form=sell_form, sell_orders=sell_orders, buy_orders=buy_orders)

@app.route('/market/<int:id>/clear')
@login_required
def market_clear(id):
    market = Market.get(Market.id == id)
    sell_orders = Order.select().where(Order.market == market.id, Order.type == 'sell').order_by(Order.price.asc())
    buy_orders = Order.select().where(Order.market == market.id , Order.type == 'buy').order_by(Order.price.desc())

    unit_sell_orders = list()
    for order in sell_orders:
        for i in range(order.quantity):
            unit_sell_orders.append(order.price)

    unit_buy_orders = list()
    for order in buy_orders:
        for i in range(order.quantity):
            unit_buy_orders.append(order.price)

    price = None;
    quantity = None;
    k = 0
    K = min(len(unit_sell_orders), len(unit_buy_orders))
    while (k < K and unit_sell_orders[k] < unit_buy_orders[k]):
        k+=1

    if k > 0:
        quantity = k
        last_buy_price = unit_buy_orders[k-1]
        last_sell_price = unit_sell_orders[k-1]
        price = (last_buy_price + last_sell_price)/2

    return render_template('market_clear.html', 
        market=market, sell_orders=sell_orders, buy_orders=buy_orders, price=price, quantity=quantity,
        last_buy_price=last_buy_price, last_sell_price=last_sell_price)


if __name__ == '__main__':
    app.debug = True
    app.run()
