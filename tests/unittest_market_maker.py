#! /usr/bin/env python

import unittest
import sys
import os
import os.path as osp
import tempfile
import shutil
import peewee
import datetime

TEST = osp.abspath(osp.dirname(__file__))

ROOT = osp.dirname(TEST)
sys.path.append(ROOT)

import data_model
from data_model import User, Market, Order, Stock
import market_maker

class MarketMakerUnittests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        db = peewee.SqliteDatabase(osp.join(self.temp_dir, 'pythia.sqlite'), check_same_thread=False)

        data_model.set_database(db)
        data_model.create_tables()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_get_market_clearing_price(self):

        market = Market.create(
            name= 'unittest',
            description = 'unittest',
            status = 'open',
            opening_date = datetime.datetime.now(),
            closing_date = datetime.datetime.now() + datetime.timedelta(1),
            price = 0,
            volume = 0
            )
        market.save()

        user = User.create(
            email = 'unitest',
            password = 'unittest'
            )
        user.save()

        market_maker.put(market, user, 10, 1)
        market_maker.call(market, user, 10, 1)

        (price, quantity) = market_maker.get_market_clearing_price(market)
        self.assertEqual(price, 10)
        self.assertEqual(quantity, 1)

        market_maker.call(market, user, 10, 1)

        (price, quantity) = market_maker.get_market_clearing_price(market)
        self.assertEqual(price, 10)
        self.assertEqual(quantity, 1)

    def test_get_market_clearing_price_2(self):

        market = Market.create(
            name= 'unittest',
            description = 'unittest',
            status = 'open',
            opening_date = datetime.datetime.now(),
            closing_date = datetime.datetime.now() + datetime.timedelta(1),
            price = 0,
            volume = 0
            )
        market.save()

        user = User.create(
            email = 'unitest',
            password = 'unittest'
            )
        user.save()

        market_maker.put(market, user, 10, 1)
        market_maker.put(market, user, 20, 2)
        market_maker.put(market, user, 30, 3)
        market_maker.put(market, user, 40, 4)

        market_maker.call(market, user, 20, 5)
        market_maker.call(market, user, 30, 4)
        market_maker.call(market, user, 40, 3)
        market_maker.call(market, user, 50, 2)

        (price, quantity) = market_maker.get_market_clearing_price(market)
        self.assertEqual(price, 30)
        self.assertEqual(quantity, 6)

    def test_clear_market(self):

        market = Market.create(
            name= 'unittest',
            description = 'unittest',
            status = 'open',
            opening_date = datetime.datetime.now(),
            closing_date = datetime.datetime.now() + datetime.timedelta(1),
            price = 0,
            volume = 0
            )
        market.save()

        user = User.create(
            email = 'unitest',
            password = 'unittest'
            )
        user.save()

        market_maker.put(market, user, 10, 1)
        market_maker.put(market, user, 20, 2)
        market_maker.put(market, user, 30, 3)
        market_maker.put(market, user, 40, 4)

        market_maker.call(market, user, 20, 5)
        market_maker.call(market, user, 30, 4)
        market_maker.call(market, user, 40, 3)
        market_maker.call(market, user, 50, 2)

        market_maker.clear_market(market)
        self.assertEqual(market.price, 30)
        self.assertEqual(market.volume, 0)

        account = user.account.get()
        self.assertEqual(0, account.balance)

        stock = Stock.get(Stock.market==market, Stock.user==user)

        c = 0
        p = 100
        q = 0
        for order in market_maker.get_sell_orders(market):
            c += 1
            p = min(p, order.price)
            q += order.quantity

        self.assertEqual(1, c)   
        self.assertEqual(40, p)        
        self.assertEqual(4, q)        

        c = 0
        p = 0
        q = 0
        for order in market_maker.get_buy_orders(market):
            c += 1
            p = max(p, order.price)
            q += order.quantity

        buy_orders = market_maker.get_buy_orders(market)
        self.assertEqual(2, c)        
        self.assertEqual(30, p)      
        self.assertEqual(8, q)  

    def test_clear_market_2(self):

        market = Market.create(
            name= 'unittest',
            description = 'unittest',
            status = 'open',
            opening_date = datetime.datetime.now(),
            closing_date = datetime.datetime.now() + datetime.timedelta(1),
            price = 0,
            volume = 0
            )
        market.save()

        user1 = User.create(
            email = 'unitest1',
            password = 'unittest1'
            )
        user1.save()

        user2 = User.create(
            email = 'unitest2',
            password = 'unittest2'
            )
        user2.save()

        market_maker.put(market, user1, 10, 1)
        market_maker.put(market, user1, 20, 2)
        market_maker.put(market, user1, 30, 3)
        market_maker.put(market, user1, 40, 4)

        market_maker.call(market, user2, 20, 5)
        market_maker.call(market, user2, 30, 4)
        market_maker.call(market, user2, 40, 3)
        market_maker.call(market, user2, 50, 2)

        market_maker.clear_market(market)
        self.assertEqual(market.price, 30)
        #self.assertEqual(market.volume, 6)

        account1 = user1.account.get()
        self.assertEqual(180, account1.balance)

        account2 = user2.account.get()
        self.assertEqual(-180, account2.balance)

        stock1 = Stock.get(Stock.market==market, Stock.user==user1)
        self.assertEqual(-6, stock1.quantity)

        stock2 = Stock.get(Stock.market==market, Stock.user==user2)
        self.assertEqual(6, stock2.quantity)

if __name__ == '__main__':
    unittest.main()    
