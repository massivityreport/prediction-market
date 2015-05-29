#! /usr/bin/env python

import unittest
import sys
import os
import os.path as osp
import tempfile
import shutil
import peewee

TEST = osp.abspath(osp.dirname(__file__))

ROOT = osp.dirname(TEST)
sys.path.append(ROOT)

import data_model
from data_model import User
import bank

class BankUnittests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        db = peewee.SqliteDatabase(osp.join(self.temp_dir, 'pythia.sqlite'), check_same_thread=False)

        data_model.set_database(db)
        data_model.create_tables()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_execute_transaction(self):

        user = User.create(
            email = 'unitest',
            password = 'unittest'
            )
        user.save()

        bank.execute_transaction(user, 100)
        bank.execute_transaction(user, 200)

        account = user.account.get()
        self.assertEqual(account.balance, 300)

        n = 0
        s = 0
        for transaction in account.transactions:
            n += 1
            s += transaction.amount

        self.assertEqual(n, 2)
        self.assertEqual(s, 300)

if __name__ == '__main__':
    unittest.main()    
