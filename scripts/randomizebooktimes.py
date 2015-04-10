#!/usr/bin/python
# Takes one or more bookids on the command line and updates the book in the database

import bibliosaur
import sys
import datetime
import time
import random
import sqlite3


conn = sqlite3.connect(bibliosaur.topleveldirectory + "/" + bibliosaur.db)
c = conn.cursor()
  
c.execute("SELECT id FROM books") 
books = c.fetchall()
i = 0
  
for item in books:
  book = bibliosaur.Book()
  book.get(id = item[0], connection = conn)
  book.lastupdatedprices = datetime.datetime.now() - datetime.timedelta(hours = random.randint(0,6), minutes = random.randint(0,59)) 
  book.lastupdatededitions = datetime.datetime.now() - datetime.timedelta(days = random.randint(0,5), hours = random.randint(0,23)) 
  book.put()


c.execute("SELECT id FROM authors") 
authors = c.fetchall()
i = 0
  
for item in authors:
  author = bibliosaur.Author()
  author.get(id = item[0], connection = conn)
  author.lastupdatedbooks = datetime.datetime.now() - datetime.timedelta(days = random.randint(0,9), hours = random.randint(0,24), minutes = random.randint(0,59)) 
  author.put()


