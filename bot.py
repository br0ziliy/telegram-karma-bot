# -*- coding: utf-8 -*-

import sys
import time
import random
import datetime, time
import telepot
import redis
import operator

BOT_TOKEN =  '123456789:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

help_msg = """
/+ str - increase karma for "str"
/- str - decrease karma for "str"
/rank str - get rankings for "str"
/roll - roll a dice
/help - get help

All other commands will be ignored.

My source code: https://github.com/br0ziliy/telegram-karma-bot
"""

try:
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
except ConnectionError:
    print "Redis connection failed"
    raise SystemExit(1)

def handle_karma(msg,direction):
    duser = msg['text'].split()[1]
    suser = msg['from']['id']
    sname = msg['from']['username']
    if duser.startswith('@'): duser = duser[1:]
    now = time.time()
    last = r.hget(duser, suser)
    delta = 31337
    if last: delta = now - float(last)

    print "Handling karma {} from {} to {} (last handled: {} seconds ago)".format(direction, sname.encode('utf8'), duser, delta)
    if duser.lower() == sname:
        return "@{} public masturbation is not allowed.".format(sname)
    if delta < 120:
        return "@{} cooldown: {} seconds left".format(sname, 120 - int(delta))
    r.hset(duser,suser,time.time())
    if direction == 'up':
        r.hincrby(duser,'0karma_',1)
    elif direction == 'down':
        r.hincrby(duser,'0karma_',-1)
    return "{} karma is now {}".format(duser, r.hget(duser,'0karma_'))

def get_rank(_for):
    vals = None
    rank = "not found"
    limiter = 10
    if _for:
        if _for.startswith('@'): _for = _for[1:]
        keys = r.keys(u'*{0}*'.format(_for))
    if len(keys) > 0: rank = ''
    for key in keys:
        if r.type(key) == 'hash':
            vals = r.hgetall(key)
            rank = ''.join([rank, key, ": ", vals['0karma_'], "\r\n"])
            limiter -= 1
        if limiter == 0:
            break
    result = '=== Rating for "{0}" ===\r\n{1}'.format(_for.encode('utf8'), rank)
    return result

def handle(msg):
    chat_id = msg['chat']['id']
    chat_type = msg['chat']['type']
    try:
        command = msg['text'].split()[0]
    except KeyError: # not a text message?
        print "Not text message - ignoring: %s" % msg
        return
    param = None
    try:
        param = msg['text'].split()[1]
    except IndexError:
        print "Command with no parameter"
        param = None
    command = command.split('@')[0]
    print "Got command: {} {} from: {}".format(command,param,msg['from']['username'].encode('utf8'))

    if command == '/roll':
        bot.sendMessage(chat_id, random.randint(1,6))
    if command == '/rank':
        if param: bot.sendMessage(chat_id, get_rank(param))
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/+' or command == '/plus':
        if param: bot.sendMessage(chat_id, handle_karma(msg, 'up'))
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/-' or command == '/minus':
        if param: bot.sendMessage(chat_id, handle_karma(msg, 'down'))
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/help':
        if chat_type == "private":
            bot.sendMessage(chat_id, help_msg)
        else:
            bot.sendMessage(chat_id, "Talk to me privately for help.")

bot = telepot.Bot(BOT_TOKEN)
bot.notifyOnMessage(handle)
print 'I am listening ...'

while 1:
    time.sleep(10)
