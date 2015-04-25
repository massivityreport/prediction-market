#! /usr/bin/env python 

import peewee
from flask.ext.security import UserMixin, RoleMixin

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
    balance = peewee.FloatField()

class Transaction(BaseModel):
    account = peewee.ForeignKeyField(Account, related_name='transactions')
    date = peewee.DateTimeField()
    amount = peewee.FloatField()

def create_tables():
    for Model in (User, Role, UserRoles, Market, MarketHistory, Stock, Order, Account, Transaction):
        Model.create_table(fail_silently=True)
