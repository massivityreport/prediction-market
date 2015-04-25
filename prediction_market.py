#! /usr/bin/env/python

# base flask
from flask import Flask, render_template, redirect, flash, url_for, redirect

# security
from flask.ext import login
from flask.ext.security import Security, PeeweeUserDatastore, login_required, roles_required
from flask.ext.login import current_user, current_app

# forms
from flask_wtf import Form
from wtforms import BooleanField, TextField, IntegerField, FloatField, validators

# pythia
from data_model import db, User, Role, UserRoles, Market, Order
from admin import build_admin
import market_maker

app = Flask(__name__)

# security
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_HASH'] = 'plaintext'
app.config['SECURITY_PASSWORD_SALT'] = 'super-salt'

user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
security = Security(app, user_datastore)

# admin
build_admin(app)

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

    sell_orders = market_maker.get_sell_orders(market)
    buy_orders = market_maker.get_buy_orders(market)

    return render_template('market.html', 
        market=market, user=user, buy_form=buy_form, sell_form=sell_form, sell_orders=sell_orders, buy_orders=buy_orders)

@app.route('/market/<int:id>/clear')
@login_required
def market_clear(id):
    market = Market.get(Market.id == id)
    sell_orders = market_maker.get_sell_orders(market)
    buy_orders = market_maker.get_buy_orders(market)

    (price, quantity) = market_maker.get_market_clearing_price(market, sell_orders, buy_orders)

    return render_template('market_clear.html', 
        market=market, sell_orders=sell_orders, buy_orders=buy_orders, price=price, quantity=quantity)

@app.route('/market/<int:id>/clear_execute')
@login_required
def market_clear_execute(id):
    market = Market.get(Market.id == id)
    market_maker.clear_market(market)

    return redirect(url_for('market', id=id))

if __name__ == '__main__':
    app.debug = True
    app.run()
