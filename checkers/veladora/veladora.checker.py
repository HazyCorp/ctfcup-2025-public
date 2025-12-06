#!/usr/bin/env python3
import sys
import os
import random
import traceback
from typing import Callable, List
import requests

from api_client import VeladoraClient, get_drink_price
import gornilo 

checker = gornilo.NewChecker()

def gen_username() -> str:
    return os.urandom(random.randint(8, 16)).hex()

def gen_password() -> str:
    return os.urandom(random.randint(12, 24)).hex()

def do_put_bill(request: gornilo.PutRequest) -> gornilo.Verdict:
    username = gen_username()
    password = gen_password()

    client = VeladoraClient(f"http://{request.hostname}")
    client.register(username, password)
    client.login(username, password)

    drink = random.choice(['beer', 'wine', 'cocktail', 'champagne'])
    client.order_drink(drink)
    res = client.pay_bill()

    drink = random.choice(['beer', 'wine', 'cocktail', 'whiskey', 'champagne'])
    client.order_drink(drink)
    comment = request.flag
    res = client.pay_bill(comment)
    payment_id = res.get('payment_id')
    bill = client.get_bill_by_id(payment_id)

    if bill.get('bill').get('comment') != comment:
        return gornilo.Verdict.MUMBLE('can\'t store flag')

    return gornilo.Verdict.OK_WITH_FLAG_ID(username, password)

def do_get_bill(request: gornilo.GetRequest) -> gornilo.Verdict:
    username = request.public_flag_id
    password = request.flag_id

    client = VeladoraClient(f"http://{request.hostname}")
    client.login(username, password)
    profile = client.get_profile()
    bill_id = profile.get('payment_links')[1]
    bill = client.get_bill_by_id(bill_id)
    if bill.get('bill').get('comment') != request.flag:
        return gornilo.Verdict.CORRUPT('can\'t get flag from bill')

    return gornilo.Verdict.OK()

def do_put_conversation(request: gornilo.PutRequest) -> gornilo.Verdict:
    username = gen_username()
    password = gen_password()
    client = VeladoraClient(f"http://{request.hostname}")
    client.register(username, password)
    client.login(username, password)
    client.talk(request.flag, username)

    return gornilo.Verdict.OK_WITH_FLAG_ID(username, password)

def do_get_conversation(request: gornilo.GetRequest) -> gornilo.Verdict:
    username = request.public_flag_id
    password = request.flag_id
    client = VeladoraClient(f"http://{request.hostname}")
    client.login(username, password)

    unique_token = request.flag.split('_')[1]
    conversations = client.remember(unique_token, username)
    if request.flag not in conversations.get('conversations')[0].get('content'):
        return gornilo.Verdict.CORRUPT('can\'t get flag from bartender')
    return gornilo.Verdict.OK()

def do_check(request: gornilo.CheckRequest) -> gornilo.Verdict:
    username = gen_username()
    password = gen_password()
    client = VeladoraClient(f"http://{request.hostname}")

    client.register(username, password)
    client.login(username, password)
    
    profile = client.get_profile()

    if profile.get('balance') != 2500:
        return gornilo.Verdict.MUMBLE('balance mismatch')

    # choose random drink
    drink = random.choice(['beer', 'wine', 'cocktail', 'whiskey', 'champagne'])
    client.order_drink(drink)
    bill = client.get_active_bill()
    drink_price = get_drink_price(drink)

    if bill.get('bill').get('orders')[0].get('drink_name') != drink:
        print('drink name mismatch')
        return gornilo.Verdict.MUMBLE('drink name mismatch')

    if bill.get('bill').get('amount') != drink_price:
        return gornilo.Verdict.MUMBLE('bill amount mismatch')

    # conversation with bartender
    random_phrase = random.choice(['Hello', 'Hi', 'How are you?', 'What is your name?', 'What is your favorite drink?', 'What is your favorite food?', 'What is your favorite color?', 'What is your favorite animal?', 'What is your favorite book?', 'What is your favorite movie?', 'What is your favorite song?', 'What is your favorite place?', 'What is your favorite thing to do?', 'What is your favorite thing to eat?', 'What is your favorite thing to drink?', 'What is your favorite thing to do?', 'What is your favorite thing to eat?', 'What is your favorite thing to drink?'])
    client.talk(random_phrase, username)
    
    # get conversations
    conversations = client.get_conversations()

    if random_phrase not in conversations.get('conversations')[0].get('content'):
        return gornilo.Verdict.MUMBLE('conversation content mismatch')

    # add 32 bytes random token to conversation
    context_token = os.urandom(16).hex()
    client.talk("Remember this conversation: " + context_token, username)

    # remember conversation
    remember_result = client.remember(context_token, username)

    if len(remember_result.get('conversations')) == 0:
        return gornilo.Verdict.MUMBLE('remember result mismatch')

    if random_phrase not in remember_result.get('conversations')[0].get('content'):
        return gornilo.Verdict.MUMBLE('remember content mismatch')

    # pay bill
    comment = os.urandom(16).hex()
    pay_result = client.pay_bill(comment)
    payment_id = pay_result.get('payment_id')
    payed_bill = client.get_bill_by_id(payment_id)
    
    if payed_bill.get('bill').get('status') != 'paid':
        return gornilo.Verdict.MUMBLE('bill status mismatch')

    if payed_bill.get('bill').get('amount') != drink_price:
        return gornilo.Verdict.MUMBLE('bill amount mismatch')

    if payed_bill.get('bill').get('comment') != comment:
        return gornilo.Verdict.MUMBLE('bill comment mismatch')

    if payed_bill.get('username') != username:
        return gornilo.Verdict.MUMBLE('username mismatch')

    return gornilo.Verdict.OK()

def wrap_exceptions(
        action: Callable[[gornilo.CheckRequest], gornilo.Verdict],
        request: gornilo.CheckRequest,
) -> gornilo.Verdict:
    try:
        return action(request)
    except requests.ConnectionError:
        return gornilo.Verdict.DOWN('connection error')
    except requests.Timeout:
        return gornilo.Verdict.DOWN('timeout error')
    except requests.RequestException:
        return gornilo.Verdict.MUMBLE('http error')

@checker.define_vuln('flag_id is username')
class VeladoraBillChecker(gornilo.VulnChecker):
    @staticmethod
    def put(request: gornilo.PutRequest) -> gornilo.Verdict:
        return wrap_exceptions(do_put_bill, request)

    @staticmethod
    def get(request: gornilo.GetRequest) -> gornilo.Verdict:
        return wrap_exceptions(do_get_bill, request)

    @checker.define_check
    def check(request: gornilo.CheckRequest) -> gornilo.Verdict:
        return wrap_exceptions(do_check, request)

@checker.define_vuln('flag_id is username')
class VeladoraConversationChecker(gornilo.VulnChecker):
    @staticmethod
    def put(request: gornilo.PutRequest) -> gornilo.Verdict:
        return wrap_exceptions(do_put_conversation, request)

    @staticmethod
    def get(request: gornilo.GetRequest) -> gornilo.Verdict:
        return wrap_exceptions(do_get_conversation, request)

if __name__ == '__main__':
    checker.run()