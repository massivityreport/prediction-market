#! /usr/bin/env python

import datetime

from data_model import Market, Stock, Order, MarketHistory
import bank

def call(market, user, price, quantity):
    order = Order.create(
        market=market, 
        user=user,
        type='buy',
        status='pending',
        price=price,
        quantity=quantity)
    order.save()

    return order

def put(market, user, price, quantity):
    order = Order.create(
        market=market, 
        user=user,
        type='sell',
        status='pending',
        price=price,
        quantity=quantity)
    order.save()

    return order

def get_sell_orders(market):
    sell_orders = Order.select().where(
        Order.market == market, 
        Order.type == 'sell',
        Order.status == 'pending'
        ).order_by(Order.price.asc())

    return sell_orders

def get_buy_orders(market):
    buy_orders = Order.select().where(
        Order.market == market, 
        Order.type == 'buy',
        Order.status == 'pending'
        ).order_by(Order.price.desc())

    return buy_orders

def get_market_clearing_price(market, sell_orders=None, buy_orders=None):
    if not sell_orders:
        sell_orders = get_sell_orders(market)
    if not buy_orders:
        buy_orders = get_buy_orders(market)

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

def do_sell_stock(order, price, quantity):
    # resolve monetary transaction
    bank.execute_transaction(order.user, price * quantity)

    # attribute stocks
    try:
        stock = Stock.get(Stock.market == order.market, Stock.user == order.user)
    except Stock.DoesNotExist:
        stock = Stock.create(
            market = order.market,
            user = order.user,
            quantity = 0
            )

    # selling short creates new stocks
    if stock.quantity < quantity:
        order.market.volume += quantity - stock.quantity

    stock.quantity -= quantity
    stock.save()

def do_buy_stock(order, price, quantity):
    # resolve monetary transaction
    bank.execute_transaction(order.user, -price * quantity)

    # attribute stocks
    try:
        stock = Stock.get(Stock.market == order.market, Stock.user == order.user)
    except Stock.DoesNotExist:
        stock = Stock.create(
            market = order.market,
            user = order.user,
            quantity = 0
            )

    stock.quantity += quantity
    stock.save()

def do_clear_order(order, price, clearing_quantity):
    if clearing_quantity < order.quantity:
        new_order = Order.create(
            market=order.market, 
            user=order.user, 
            price=order.price, 
            quantity=order.quantity - clearing_quantity,
            type=order.type,
            status='pending')
        new_order.save()

    order.price = price
    order.quantity = clearing_quantity
    order.status = 'cleared'
    order.save()   

def do_clear_sell_orders(sell_orders, price, quantity):
    sumq = 0
    for order in sell_orders:
        if order.price <= price and sumq < quantity:
            clearing_quantity = min(quantity - sumq, order.quantity)
            do_sell_stock(order, price, clearing_quantity)
            do_clear_order(order, price, clearing_quantity)
            sumq += clearing_quantity
        else:
            break

def do_clear_buy_orders(buy_orders, price, quantity):
    sumq = 0
    for order in buy_orders:
        if order.price >= price and sumq < quantity:
            clearing_quantity = min(quantity - sumq, order.quantity)
            do_buy_stock(order, price, clearing_quantity)
            do_clear_order(order, price, clearing_quantity)
            sumq += clearing_quantity
        else:
            break

def clear_market(market):
    sell_orders = get_sell_orders(market)
    buy_orders = get_buy_orders(market)

    (price, quantity) = get_market_clearing_price(market, sell_orders, buy_orders)
    if not price:
        return

    # always clear buy order first because of sell short stock creation
    do_clear_buy_orders(buy_orders, price, quantity)
    do_clear_sell_orders(sell_orders, price, quantity)

    # update market
    market.price = price
    market.save()

    # save market history
    market_history = MarketHistory.create(
        market=market,
        price=price,
        volume=quantity,
        date=datetime.datetime.now()
        )

def get_market_history(market):
    history = MarketHistory.select().where(MarketHistory.market == market).order_by(MarketHistory.date.desc())

    return history

def close_market(market):
    now = datetime.datetime.now()
    if market.closing_date < now:
        market.status = 'closed'
        market.save()
        return True

    return False


