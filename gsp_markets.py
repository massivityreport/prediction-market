#! /usr/bin/env python

import datetime

def get_opening_date():
    now = datetime.datetime.now()
    current_hour = datetime.datetime(now.year, now.month, now.day, now.hour)

    return current_hour

def get_closing_date():
    now = datetime.datetime.now()
    next_hour = datetime.datetime(now.year, now.month, now.day, now.hour + 1)

    return next_hour
    
def get_resolution_date():
    now = datetime.datetime.now()
    next_hour = datetime.datetime(now.year, now.month, now.day, now.hour + 2)

    return next_hour
    
def time_to_live():
    now = datetime.datetime.now()
    closing_date = get_closing_date()

    return (closing_date - now).seconds / 60
