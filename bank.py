#! /usr/bin/env

import datetime

from data_model import Account, Transaction

def create_account(user):
    account = Account.create(
        user=user,
        balance=0
        )
    return account

def execute_transaction(user, price):
    try:
        account = user.account.get()
    except Account.DoesNotExist:
        account = create_account(user)

    transaction = Transaction.create(
        account = account,
        date = datetime.datetime.now(),
        amount = price
        )
    transaction.save()

    account.balance += transaction.amount
    account.save()

