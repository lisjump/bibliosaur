#!/usr/bin/python

import sys
sys.path.append('/var/www/dev.bibliosaur.com/scripts')

import cgi
import datetime
import time
import urllib
import urllib2
import bottlenose
import webapp2
import jinja2
import os
import re
import xmlparser
import json
import logging
import logging.config
import Cookie
import sqlite3
import random
import keys
import pickle
import threading
import bibliosaur

# -------------- Definitions and Environment ---------------

toplevelurl = "http://dev.bibliosaur.com"
topleveldirectory = "/var/www/dev.bibliosaur.com"
db = "bibliosaur.db"
tempdb = "biblioimport.db"

conn = sqlite3.connect(topleveldirectory + "/" + db)
c = conn.cursor()
  
connt = sqlite3.connect(topleveldirectory + "/" + tempdb)
ct = connt.cursor()
  
# ct.execute("SELECT notificationwaittime, preferredemail, preferredsort, defaultformats, labels, ascending, key, registeredemail, defaultprice FROM myusers") 
# oldusers = ct.fetchall()
# 
# for u in oldusers:
#   user = bibliosaur.User()
#   user.preferredemail = u[1]
#   user.googleemail = u[6]
#   if u[3]:
#     formats = re.split('\[u\'', str(u[3]))[1]
#     formats = re.split('\'\]', formats)[0]
#     formats = re.split('\', u\'', formats)
#     user.defaultformats = formats
#   if u[8]:
#     user.defaultprice = int(u[8])
#   user.put()
# 
ct.execute("SELECT archived, notified, acceptedformats, labels, goodreadsid, price, key, date, email FROM userbooks") 
olduserbooks = ct.fetchall()

i = 0

for ub in olduserbooks:
  i = i + 1
  goodreadsid = ub[4]
  userbook = bibliosaur.UserBook()
  book = bibliosaur.Book()
  book.get(goodreadsid = goodreadsid, connection = conn, addbook = True)
  user = bibliosaur.User()
  user.get(googleemail = ub[8], connection = conn)
  print user.googleemail + ": " + book.title + " by " + book.author
  userbook.bookid = book.id
  userbook.userid = user.id
  acceptedformats = re.split('\[u\'', str(ub[2]))[1]
  acceptedformats = re.split('\'\]', acceptedformats)[0]
  acceptedformats = re.split('\', u\'', acceptedformats)
  userbook.acceptedformats = acceptedformats
  userbook.price = int(ub[5])
  ubt = str(ub[7])
  ubtime = str(ubt[0:10]) + " " + str(ubt[11:19]) + ".000000"
  userbook.date = ubtime
  if ub[0] == "False":
    userbook.archived = False
  else:
    userbook.archived = True
  nt = str(ub[1])
  ntime = nt[0:10] + " " + nt[11:19] + ".000000"
  userbook.notified = ntime
  try:
    labels = re.split('\[u\'', str(ub[3]))[1]
    labels = re.split('\'\]', labels)[0]
    labels = re.split('\', u\'', labels)
  except:
    labels = []
  userbook.labels = labels
  userbook.put()
#   time.sleep(1)
#   if i == 100:
#     break
