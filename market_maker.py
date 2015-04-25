#! /usr/bin/env python

import datetime

from data_model import Market, Stock, Order
import bank

def get_sell_orders(market):
    sell_orders = Order.select().where(
        Order.market == market.id, 
        Order.type == 'sell',
        Order.status == 'pending'
        ).order_by(Order.price.asc())

    return sell_orders

def get_buy_orders(market):
    buy_orders = Order.select().where(
        Order.market == market.id, 
        Order.type == 'buy',
        Order.status == 'pending'
        ).order_by(Order.price.desc())

    return buy_orders

def get_market_clearing_price(market, sell_orders, buy_orders):
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
    while (k < K and unit_sell_orders[k] <= unit_buy_orders[k]):
        k+=1

    if k > 0:
        quantity = k
        last_buy_price = unit_buy_orders[k-1]
        last_sell_price = unit_sell_orders[k-1]
        price = (last_buy_price + last_sell_price)/2

    return price, quantity

def do_sell_stock(market, user, price, quantity):
    # resolve monetary transaction
    bank.execute_transaction(user, price * quantity)

    # attribute stocks
    try:
        stock = Stock.get(Stock.id == market.id, Stock.id == user.id)
    except Stock.DoesNotExist:
        stock = Stock.create(
            market = market.id,
            user = user.id,
            quantity = 0
            )

    # selling short creates new stocks
    if stock.quantity < quantity:
        market.volume += quantity - stock.quantity

    stock.quantity -= quantity
    stock.save()

def do_buy_stock(market, user, price, quantity):
    # resolve monetary transaction
    bank.execute_transaction(user, -price * quantity)

    # attribute stocks
    try:
        stock = Stock.get(Stock.id == market.id, Stock.id == user.id)
    except Stock.DoesNotExist:
        stock = Stock.create(
            market = market.id,
            user = user.id,
            quantity = 0
            )

    stock.quantity += quantity
    stock.save()

def do_clear_sell_orders(market, sell_orders, price, quantity):
    sumq = 0
    for order in sell_orders:
        if order.price <= price:
            # full order is cleared
            if order.quantity + sumq <= quantity:
                do_sell_stock(market, order.user, price, order.quantity)
                order.status = 'cleared'
                order.save()
                sumq += order.quantity
            # parital order clearing
            elif sumq < quantity:
                partial_quantity = quantity - sumq
                remaning_quantity = order.quantity - partial_quantity

                do_sell_stock(market, order.user, price, partial_quantity)
                order.quantity = partial_quantity
                order.status = 'cleared'
                order.save()
                new_order = Order.create(
                    market=market.id, 
                    user=order.user, 
                    price=order.price, 
                    quantity=remaning_quantity,
                    type='sell',
                    status='pending')
                new_order.save()
                sumq = quantity
            else:
                break

def do_clear_buy_orders(market, buy_orders, price, quantity):
    sumq = 0
    for order in buy_orders:
        if order.price >= price:
            # full order is cleared
            if order.quantity + sumq <= quantity:
                do_buy_stock(market, order.user, price, order.quantity)
                order.status = 'cleared'
                order.save()
                sumq += order.quantity
            # parital order clearing
            elif sumq < quantity:
                partial_quantity = quantity - sumq
                remaning_quantity = order.quantity - partial_quantity

                do_buy_stock(market, order.user, price, partial_quantity)
                order.quantity = partial_quantity
                order.status = 'cleared'
                order.save()
                new_order = Order.create(
                    market=market.id, 
                    user=order.user, 
                    price=order.price, 
                    quantity=remaning_quantity,
                    type='buy',
                    status='pending')
                new_order.save()
                sumq = quantity
            else:
                break

def clear_market(market):
    sell_orders = get_sell_orders(market)
    buy_orders = get_buy_orders(market)

    (price, quantity) = get_market_clearing_price(market, sell_orders, buy_orders)
    if not price:
        return

    do_clear_buy_orders(market, buy_orders, price, quantity)
    do_clear_sell_orders(market, sell_orders, price, quantity)

    # update market
    market.price = price
    market.save()
