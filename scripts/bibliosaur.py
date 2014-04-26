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

# -------------- Definitions and Environment ---------------

toplevelurl = "http://dev.bibliosaur.com"
topleveldirectory = "/var/www/dev.bibliosaur.com"
db = "bibliosaur.db"

jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader('/var/www/dev.bibliosaur.com'))
logger = logging.getLogger()
hdlr = logging.FileHandler('/var/www/dev.bibliosaur.com/bibliosaur.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

DEBUG = 0

UNREALISTICPRICE = int(7777777777777777)

GOOGLE_CLIENT_ID = keys.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = keys.GOOGLE_CLIENT_SECRET

AMAZON_ACCESS_KEY_ID = keys.AMAZON_ACCESS_KEY_ID
AMAZON_SECRET_KEY = keys.AMAZON_SECRET_KEY
AMAZON_ASSOC_TAG = keys.AMAZON_ASSOC_TAG

GOODREADS_ACCESS_KEY_ID = keys.GOODREADS_ACCESS_KEY_ID
GOODREADS_SECRET_KEY = keys.GOODREADS_SECRET_KEY

LINKSHARE_TOKEN = keys.LINKSHARE_TOKEN
LINKSHARE_ID = keys.LINKSHARE_ID
BN_TOKEN = keys.BN_TOKEN


possibleformats = ["hardcover", "paperback", "librarybinding", "kindle", "epub", "audiobook"]
predefinedlabels = ["mybooks", "archived"];

# -------------------- Authentication ----------------------------

class google_login(webapp2.RequestHandler):
    def get(self):
		token_request_uri = "https://accounts.google.com/o/oauth2/auth"
		response_type = "code"
		redirect_uri = toplevelurl + "/login/google/auth"
		scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
		url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
			token_request_uri = token_request_uri,
			response_type = response_type,
			client_id = GOOGLE_CLIENT_ID,
			redirect_uri = redirect_uri,
			scope = scope)
		return self.redirect(url)
    
class google_authenticate(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
		logging.warning("login failed: " + str(exception))
		return self.redirect(toplevelurl)
    def get(self):
		try:
		  code = self.request.get_all('code')
		except:
		  logging.error("Login failed:  'code' not available")
		  return self.redirect(toplevelurl)

		url = 'https://accounts.google.com/o/oauth2/token'
		redirect_uri = toplevelurl + "/login/google/auth"
		values = {'code' : code[0], 
			      'redirect_uri' : redirect_uri,
			      'client_id' : GOOGLE_CLIENT_ID,
			      'client_secret' : GOOGLE_CLIENT_SECRET,
			      'grant_type' : 'authorization_code'}
		data = urllib.urlencode(values)
		headers={'content-type':'application/x-www-form-urlencoded'}
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req).read()
		token_data = json.JSONDecoder().decode(response)
		response = urllib2.urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token={accessToken}".format(accessToken=token_data['access_token'])).read()
# 		logging.info("response:  " + str(response))
		#this gets the google profile!!
		google_profile = json.JSONDecoder().decode(response)
		#log the user in-->
		#HERE YOU LOG THE USER IN, OR ANYTHING ELSE YOU WANT
		#THEN REDIRECT TO PROTECTED PAGE
		session = Session()
		session.user.fetchUser(googleemail = google_profile['email'])
		cookie = session.login()
		
		self.response.set_cookie(key = cookie['key'], value = cookie['value'], expires = cookie['expires'])		
		return self.redirect(toplevelurl)

class logout(webapp2.RequestHandler):
    def get(self):		
		conn = sqlite3.connect(topleveldirectory + "/" + db)
		c = conn.cursor()

		session = LoadSession(self.request.cookies, connection = conn)
		
		with conn:
		  c.execute("INSERT or REPLACE INTO session (id, userid, expire) VALUES (?, ?, ?)", (session.id, session.user.id, datetime.datetime.now()))
		
		conn.close()
		
		self.response.set_cookie(key = 'sessionid', value = session.id, expires = datetime.datetime.now())
		return self.redirect(toplevelurl)

# -------------------------- Session and User Data -------------------------------

def LoadSession(cookies, connection = None):
  session = Session()
  sessionid = ""
  
  try: 
    sessionid = cookies.get('sessionid')
  except:
    pass  
  
  if sessionid:
    session.load(id=sessionid, connection = connection)

  return session
  
class Session():
  def __init__(self, id = None):
    self.id = id
    self.user = User()
  
  def load(self, id, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    c.execute("select count(*) from session where id = ?", (id,))
    count = c.fetchall()[0][0]
    
    if count == 0:
      pass
    elif count == 1:
      c.execute("select id, userid, expire from session where id = ?", (id,))
      result = c.fetchall()[0]
      if (result[2]) > str(datetime.datetime.now()):
        self.id = result[0]
        self.user.fetchUser(id = result[1])
    else:
      logging.error("USER ERROR:  More than one user with gmail: " + self.googleemail)
    
    if not connection:
      conn.close()
    return
  
  def login(self, connection = None):
    self.id = self.user.preferredemail.split('@')[0] + str(random.getrandbits(128))
    cookie = {}
    cookie['key'] = "sessionid"
    cookie['value'] = self.id
    cookie['expires'] = datetime.datetime.now() + datetime.timedelta(days=7) 
    
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    with conn:
      c.execute("INSERT or REPLACE INTO session (id, userid, expire) VALUES (?, ?, ?)", (self.id, self.user.id, cookie['expires']))
    
    if not connection:
      conn.close()
    
    return cookie
  
  def logout(self):
    return
    
class User():
  def __init__(self, id=None):
    self.id = id
    self.preferredemail = None
    self.googleemail = None
    self.notificationwaittime = 7
    self.defaultformats = []
    self.defaultprice = 0
    self.preferredsort = None
    self.ascending = True
    self.labels =[]
  
  def fetchUser(self, id = None, googleemail = None, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    if googleemail:
      self.googleemail = str(googleemail)
      c.execute("select count(*) from users where googleemail = ?", (self.googleemail,))
      count = c.fetchall()[0][0]
      if count == 0:
        self.put(connection = conn)
      elif count == 1:
        self.get(googleemail = self.googleemail, connection = conn)
      else:
        logging.error("USER ERROR:  More than one user with gmail: " + self.googleemail)
    if id:
      self.id = id
      c.execute("select count(*) from users where id = ?", (self.id,))
      count = c.fetchall()[0][0]
      if count == 0:
        self.put(connection = conn)
      elif count == 1:
        self.get(id = self.id, connection = conn)
      else:
        logging.error("USER ERROR:  More than one user with id: " + self.id)

    if not connection:
      conn.close()
    
    return
  
  def get(self, id = None, googleemail = None, connection = None):
    er = False
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    if id:
      c.execute("select count(*) from users where id = ?", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        c.execute("select id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels  from users where id = ?", (id,))
      else:
        logging.error("USER ERROR:  user not found: " + id)
        er = True
    elif googleemail:
      c.execute("select count(*) from users where googleemail = ?", (googleemail,))
      count = c.fetchall()[0][0]
      if count == 1:
        c.execute("select id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels  from users where googleemail = ?", (googleemail,))
      else:
        logging.error("USER ERROR:  user not found: " + googleemail)
        er = True

    if not er:
      user = c.fetchall()[0]
      self.id = user[0]
      if user[1]:
        self.preferredemail = user[1]
      if user[2]:
        self.googleemail = user[2]
      if user[3]:
        self.notificationwaittime = user[3]
      if user[4]:
        self.defaultformats = pickle.loads(str(user[4]))
      if user[5]:
        self.defaultprice = user[5]
      if user[6]:
        self.preferredsort = user[6]
      if user[7]:
        self.ascending = user[7]
      if user[8]:
        self.labels = pickle.loads(str(user[8]))
    if not connection:
      conn.close()
    
    return

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    
    c = conn.cursor()
    
    if not self.preferredemail:
      self.preferredemail = self.googleemail
    with conn:
      c.execute("INSERT INTO users (preferredemail, googleemail, notificationwaittime) VALUES (?, ?, ?)", (self.preferredemail, self.googleemail, self.notificationwaittime))
    c.execute("select id from users where googleemail = ?", (self.googleemail,))
    result = c.fetchall()
    self.id = result[0][0]
    
    if not connection:
      conn.close()    
      
    return
  
  def update(self, request, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    self.preferredemail = request.get('preferredemail')
    price = request.get('defaultprice')
    try:
      self.defaultprice = int(float(price) * 100)
    except ValueError:
      self.defaultprice = None
    self.defaultformats = request.get_all('format')
    self.notificationwaittime = int(request.get('wait'))
    self.preferredsort = request.get('sortorder')
    if (request.get_all('ascdesc')[0] == "ascending"):
      self.ascending = True
    else:
      self.ascending = False

    labels = Set()
    tabs = Set()
    self.labels = []
    self.tabs = []
    for i in range(20):
      label = str(request.get('label' + str(i)))
      if (label):
        labels.add(label)
    for label in labels:
      self.labels.append(label)
    self.labels.sort() 
    
    if not self.preferredemail:
      self.preferredemail = self.googleemail
    with conn:
      c.execute("REPLACE INTO users (id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.preferredemail, self.googleemail, self.notificationwaittime, pickle.dumps(self.defaultformats), self.defaultprice, self.preferredsort, self.ascending, pickle.dumps(self.labels)))

    if not connection:
      conn.close()    
      
    return
  
  def delete(self):
    return

# --------------------- Book Data ----------------------------

class Book():
  id = None
  goodreadsid = ""
  title = ""
  author = ""
  small_img_url = ""
  date = datetime.datetime.now()
  lastupdatedprices = ""
  lastupdatededitions = ""
  editions = []
  prices = {} # {format:(price, url)}
  
  def get(self, goodreadsid = goodreadsid, id = id, connection = None, addbook = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    if goodreadsid:
      c.execute("select count(*) from books where goodreadsid = ?", (goodreadsid,))
    elif id:
      c.execute("select count(*) from books where id = ?", (id,))
    count = c.fetchall()[0][0]
    if count == 1:
      if goodreadsid:
        c.execute("select id, goodreadsid, title, author, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices from books where goodreadsid = ?", (goodreadsid,))
      elif id:
        c.execute("select id, goodreadsid, title, author, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices from books where id = ?", (id,))
      book = c.fetchall()[0]
      self.id = book[0]
      if book[1]:
        self.goodreadsid = str(book[1])
      if book[2]:
        self.title = book[2]
      if book[3]:
        self.author = book[3]
      if book[4]:
        self.small_img_url = book[4]
      if book[5]:
        self.date = book[5]
      if book[6]:
        self.lastupdatedprices = book[6]
      if book[7]:
        self.lastupdatededitions = book[7]
      if book[8]:
        self.editions = pickle.loads(str(book[8]))
      if book[9]:
        self.prices = pickle.loads(str(book[9]))
    if addbook and not self.goodreadsid:
      self.goodreadsid = goodreadsid
      self.put()
    elif addbook and not (self.author and self.title):
      self.fix()
      
    if not connection:
      conn.close()

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      if self.id:
        c.execute("REPLACE INTO books (id, goodreadsid, title, author, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.goodreadsid, self.title, self.author, self.small_img_url, self.date, self.lastupdatedprices, self.lastupdatededitions, pickle.dumps(self.editions), pickle.dumps(self.prices)))
      else:
        c.execute("REPLACE INTO books (goodreadsid, title, author, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.goodreadsid, self.title, self.author, self.small_img_url, self.date, self.lastupdatedprices, self.lastupdatededitions, pickle.dumps(self.editions), pickle.dumps(self.prices)))
        c.execute("select id from books where goodreadsid = ?", (self.goodreadsid,))
        result = c.fetchall()
        self.id = result[0][0]
    
    if not connection:
      conn.close()

  def fix(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
  
    editionurl = "http://www.goodreads.com/work/editions/" + book.goodreadsid
    content = urllib.urlopen(editionurl).read()
    splitcontent = content.split('\n')
	
    gottitle = False
    gotauthor = False
    gotimage = False
	
    for line in splitcontent:
      title = re.findall('.*Editions\s+of\s+(.*)\s+by\s+.*', line)
      author = re.findall('.*Editions\s+of\s+.*\s+by\s+(.*)\<.*', line)
      image = re.findall('.*(http://d.gr-assets.com/books/.*jpg).*', line)
		
      if title and author:
        self.title = title[0]
        self.author = author[0]
        gottitle = True
        gotauthor = True
      elif title:
        self.title = title[0]
        gottitle = True
      elif author:
        self.author = author[0]
        gotauthor = True
      elif image:
        self.small_img_url = image[0]
        gotimage = True
		
      if gottitle and gotimage:
			  return
	
	  if gottitle is False:
		  self.title = "missing - please contact lis@bibliosaur.com"
	
	  if gotauthor is False:
		  self.title = "missing - please contact lis@bibliosaur.com"
	
	  if gotimage is False:
		  self.small_img_url = ""
    
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("DELETE FROM books WHERE id = ?", (self.id,))
    
    if not connection:
      conn.close()
  
  def addtoqueue(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    logging.info(self.id)
    with conn:
      c.execute("REPLACE INTO bookupdatequeue (bookid) VALUES (?)", (self.id,))
    
    if not connection:
      conn.close()
  
  def updatePrices(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    for isbn in self.editions:
      edition = Edition()
      try:
        if not edition.get(isbn = isbn, connection = conn):
          self.editions.remove(isbn)
          continue
        edition.updatePrice(connection = conn)
      except:
        pass
      if edition.format not in self.prices:
        self.prices[edition.format] = (UNREALISTICPRICE, "") 
      if int(edition.lowestprice) < int(self.prices[edition.format][0]):
        logging.info(str(edition.lowestprice) + " " + str(self.prices[edition.format][0]))
        self.prices[edition.format] = (edition.lowestprice, edition.lowestpriceurl)
        # this gets put() in the calling function
    
    if not connection:
      self.put( connection = conn)
      conn.close()
  
  def updateEditions(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    currenttime = datetime.datetime.now()
    timeforeditionupdate = datetime.timedelta(days=7) 
    timeforpriceupdate = datetime.timedelta(hours=8)
  
    c.execute("select count(*) from userbooks where bookid = ?", (self.id,))
    count = c.fetchall()[0][0]
    if count == 0:
      self.delete()
      return
      
    if not (self.lastupdatededitions) or not (str(self.lastupdatededitions) > str(currenttime - timeforeditionupdate)):
      self.insertEditions(connection = conn)
      self.lastupdatededitions = currenttime
      self.lastupdatedprices = currenttime - 2*timeforpriceupdate # we need to make sure we update prices since we updated the editions
      # this gets put() in the next if statement

    if not (self.lastupdatedprices) or not (str(self.lastupdatedprices) > str(currenttime - timeforpriceupdate)):
      self.updatePrices(connection = conn)
      self.lastupdatedprices = currenttime
      self.put()
    
    if not connection:
      conn.close()
  
  def insertEditions(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    editionurl = "http://www.goodreads.com/work/editions/" + self.goodreadsid
    content = urllib.urlopen(editionurl).read()
    splitcontent = content.split('\n')
  
    isbnlast = True
  
    for line in splitcontent:
      format = re.findall('\s+([\w\s]+), \d+ pages', line)
      isbn = re.findall('^\s*(\d\d\d\d\d\d\d\d\d\d)\s*$', line)
      asin = re.findall('^\s*([\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w])\s*$', line)
      kindle = re.findall('(Kindle Edition)', line)
    
      try:
        if (format[0] == "Paperback") or (format[0] == "Mass Market Paperback"):
          lastformat = "paperback"
        elif (format[0] == "Kindle") or (format[0] == "Kindle Edition"):
          lastformat = "kindle"
        elif (format[0] == "ebook"):
          lastformat = "epub"
        elif (format[0] == "Library Binding"):
          lastformat = "librarybinding"
        elif (format[0] == "Hardcover"):
          lastformat = "hardcover"
        elif (format[0] == "Audio") or (format[0] == "Audio Book") or (format[0] == "Audio CD") or (format[0] == "Audio book") or (format[0] == "Audiobook"):
          lastformat = "audiobook"
        else:
          isbnlast = True
        isbnlast = False
      except IndexError:
        pass
       
      try:
        if (kindle[0] == "Kindle Edition"):
          lastformat = "kindle"
          isbnlast = False
      except IndexError:
        pass
        
      try:
        isbn = isbn[0]
        if not isbnlast:
          edition = Edition()
          edition.isbn = isbn
          edition.format = lastformat
          edition.bookid = self.id
          edition.put(connection = conn)
          self.editions.append(isbn)
          isbnlast = True
      except IndexError:
        pass
    
      try:
        isbn = asin[0]
        if not isbnlast:
          edition = Edition()
          edition.isbn = isbn
          edition.format = lastformat
          edition.bookid = self.id
          edition.put(connection = conn)
          self.editions.append(isbn)
          isbnlast = True
      except IndexError:
        pass
    
    self.editions = list(set(self.editions))
    self.put(connection = conn)
    
    if not connection:
      conn.close()
  
class Edition():
  isbn = "" # or ASIN, et al
  format = ""
  lowestprice = UNREALISTICPRICE
  lowestpriceurl = ""
  bookid = None

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("REPLACE INTO editions (isbn, lowestprice, lowestpriceurl, format, bookid) VALUES (?, ?, ?, ?, ?)", (self.isbn, self.lowestprice, self.lowestpriceurl, self.format, self.bookid))
    
    if not connection:
      conn.close()

  def get(self, isbn = None, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    c.execute("select count(*) from editions where isbn = ?", (isbn,))
    count = c.fetchall()[0][0]
    if count == 1:
      c.execute("select isbn, lowestprice, lowestpriceurl, format, bookid from editions where isbn = ?", (isbn,))
      edition = c.fetchall()[0]
      self.isbn = edition[0]
      if edition[1]:
        self.lowestprice = edition[1]
      if edition[2]:
        self.lowestpriceurl = edition[2]
      if edition[3]:
        self.format = edition[3]
      if edition[4]:
        self.bookid = edition[4]
    elif count == 0:
      return False
      
    if not connection:
      conn.close()
      
    return True

  def updatePrice(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    currentlowestprice = UNREALISTICPRICE
    currenturl = ""
    prices = {}
    
    if (self.format == "kindle"):
      prices['kindle'] = GetKindlePrice(self.isbn)
    elif (self.format == "hardcover") or (self.format == "paperback") or (self.format == "librarybinding"):
      prices['amazon'] = GetAmazonPrice(self.isbn)
#       prices['bn'] = GetBNPrice(edition.isbn)
    elif (self.format == "epub"):
      prices['bn'] = GetBNPrice(self.isbn)
      prices['google'] = GetGooglePrice(self.isbn)
    elif (self.format == "audiobook"):
      prices['amazon'] = GetAmazonPrice(self.isbn)
      prices['bn'] = GetBNPrice(self.isbn)
    else:
      return
  
    for key in prices.keys():
      if (int(prices[key][0]) < int(currentlowestprice)):
        currentlowestprice = int(prices[key][0])
        currenturl = prices[key][1]
  
    self.lowestprice = currentlowestprice  
    self.lowestpriceurl = currenturl
    
    if (self.lowestprice == UNREALISTICPRICE):
      self.delete()
      return
  
    self.put()
    
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    book = Book()
    book.get(id = self.bookid, connection = conn)
    book.editions.remove(self.isbn)
    book.put(connection = conn)
    
    with conn:
      c.execute("DELETE FROM editions WHERE isbn = ?", (self.isbn,))
        
    if not connection:
      conn.close()

class UserBook():
  userid = None
  bookid = None
  acceptedformats = []
  price = 0
  date = datetime.datetime.now()
  archived = False
  notified = datetime.datetime.now()
  labels = []

  def get(self, bookid, userid, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    c.execute("SELECT userid, bookid, acceptedformats, price, date, archived, notified FROM userbooks where bookid = ? and userid = ?", (bookid, userid)) 
    logging.info("SELECT userid, bookid, acceptedformats, price, date, archived, notified FROM userbooks where bookid = %s and userid = %s" % (str(bookid), str(userid)))
    userbook = c.fetchall()[0]
  
    if userbook[0]:
      self.userid = userbook[0]
    if userbook[1]:
      self.bookid = userbook[1]
    if userbook[2]:
      self.acceptedformats = pickle.loads(str(userbook[2]))
    if userbook[3]:
      self.price = userbook[3]
    if userbook[4]:
      self.date = userbook[4]
    if userbook[5]:
      self.archived = userbook[5]
    if userbook[6]:
      self.notified = userbook[6]
    
    if not connection:
      conn.close()

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      c.execute("REPLACE INTO userbooks (userid, bookid, acceptedformats, price, date, archived, notified, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (self.userid, self.bookid, pickle.dumps(self.acceptedformats), self.price, self.date, self.archived, self.notified, pickle.dumps(self.labels)))
    
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    if not connection:
      conn.close()

class Coupon():
  offer = str
  merchant = str
  url = str

class DisplayBook():
  goodreadsid = ""
  bookid = ""
  title = ""
  author = ""
  small_img_url = ""
  price = ""
  acceptedformats = []
  formatprices = {}
  formaturls = {}
  priceavailable = False
  free = False
  labels = []
  dateadded = str
  
  def xml(self):
    xmlstring = "<DisplayBook>"
    xmlstring = xmlstring + "<goodreadsid>" + self.goodreadsid + "</goodreadsid>"
    xmlstring = xmlstring + "<bookid>" + self.bookid + "</bookid>"
    xmlstring = xmlstring + "<title>" + self.title.replace('<', '&lt;').replace('>', '&gt;') + "</title>"
    xmlstring = xmlstring + "<author>" + self.author.replace('<', '&lt;').replace('>', '&gt;') + "</author>"
    xmlstring = xmlstring + "<price>" + self.price + "</price>"
    xmlstring = xmlstring + "<small_img_url>" + self.small_img_url + "</small_img_url>"
    xmlstring = xmlstring + "<dateadded>" + self.dateadded + "</dateadded>"
    xmlstring = xmlstring + "<priceavailable>" + str(self.priceavailable) + "</priceavailable>"
    xmlstring = xmlstring + "<free>" + str(self.free) + "</free>"
    xmlstring = xmlstring + "<formatprices>"
    for format in self.formatprices:
      xmlstring = xmlstring + "<" + format + ">" + self.formatprices[format] + "</" + format + ">"
    xmlstring = xmlstring + "</formatprices>"
    xmlstring = xmlstring + "<formaturls>"
    for format in self.formaturls:
      xmlstring = xmlstring + "<" + format + ">" + self.formaturls[format] + "</" + format + ">"
    xmlstring = xmlstring + "</formaturls>"
    for label in self.labels:
      xmlstring = xmlstring + "<label>" + label.encode('utf-8').replace('<', '&lt;').replace('>', '&gt;') + "</label>"
    xmlstring = xmlstring + "</DisplayBook>"
    return xmlstring.encode('utf-8')

  def get(self, userbook, user = None, connection = None):
    book = Book()
    book.get(id = userbook.bookid, connection = connection)
    self.goodreadsid = book.goodreadsid
    self.bookid = str(book.id)
    self.acceptedformats = userbook.acceptedformats
    self.formatprices = dict.fromkeys(self.acceptedformats)
    self.formaturls = dict.fromkeys(self.acceptedformats)
    self.price = FormatPrice(userbook.price)
    self.dateadded = str(userbook.date)
    self.labels = []
  
    self.author = book.author
    self.title  = book.title
    self.small_img_url = book.small_img_url
    if (user):
      self.labels = list(set(userbook.labels) & set(user.labels))
    if userbook.archived:
      self.labels.append('archived')

    for format in self.acceptedformats:
      if format in book.prices:
        priceandurl = book.prices[format]
      else:
        priceandurl = (UNREALISTICPRICE, "")
      if (priceandurl[0] <= userbook.price):
        self.priceavailable = True
        if (priceandurl[0] <= 0):
          self.free = True
      self.formatprices[format] = FormatPrice(priceandurl[0])
      self.formaturls[format] = priceandurl[1]

def FormatPrice(price):
  if (price == UNREALISTICPRICE):
    return ""
  try:
    return "$%d.%2.2d" % (price/100, price%100)
  except TypeError:
    return 
  
# ----------------------Price Getting and Comparing ----------------

def GetAmazonPrice(isbn):
# return list with first element as price and second as url
  associateinfo = bottlenose.Amazon(AMAZON_ACCESS_KEY_ID, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
  response = associateinfo.ItemLookup(ItemId=isbn, ResponseGroup="Offers", SearchIndex="Books", IdType="ISBN", MerchantId = "Amazon")
  bookinfo = xmlparser.xml2obj(response)
  
  price = UNREALISTICPRICE
  url = "amazon"

  try:
    price = bookinfo.Items.Item.Offers.Offer.OfferListing.Price.Amount
    response = associateinfo.ItemLookup(ItemId=isbn, ResponseGroup="ItemAttributes", SearchIndex="Books", IdType="ISBN", MerchantId = "Amazon")
    bookinfo = xmlparser.xml2obj(response)
    url = bookinfo.Items.Item.DetailPageURL
  except AttributeError:
    pass
  
  return [int(price), url]

def GetBNPrice(isbn):
# return list with first element as price and second as url
  bookurl = "http://services.barnesandnoble.com/v03_00/ProductLookup?Ean=" + isbn + "&ProductCode=Book&AppId=" + BN_TOKEN
  price = UNREALISTICPRICE
  url = "bn"
  
  try:
    response = urllib.urlopen(bookurl).read()
    bookinfo = xmlparser.xml2obj(response)
    price = bookinfo.ProductLookupResult.Product[0].Prices.BnPrice
    encodedurl = bookinfo.ProductLookupResult.Product[0].Url.replace("/", "%2f").replace(":", "%3a")
    url = "http://click.linksynergy.com/deeplink?mid=36889&id=" + LINKSHARE_ID + "&murl=" + encodedurl
    price = int(float(price) * 100)
    deliverymessage = bookinfo.ProductLookupResult.Product[0].ShippingOptions.DeliveryMessage
  except: 
    if (DEBUG > 0):
      logging.warning("-------------- BN couldn't open url: " + bookurl)
    return [int(price), url]

  return [int(price), url]
      
def GetKindlePrice(isbn):
# return list with first element as price and second as url
  associateinfo = bottlenose.Amazon(AMAZON_ACCESS_KEY_ID, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
  response = associateinfo.ItemLookup(ItemId=isbn, ResponseGroup="ItemAttributes", SearchIndex="Books", IdType="ISBN", MerchantId = "Amazon")
  bookinfo = xmlparser.xml2obj(response)
  
  price = UNREALISTICPRICE 
  url = "kindle"

  try:
    url = bookinfo.Items.Item.DetailPageURL
    content = urllib.urlopen(url).read()
    prices = re.findall('<input type="hidden" name="displayedPrice" value="(\d+\.\d\d)"/>', content)
    price = int(float(prices[0]) * 100)
  except (AttributeError, IndexError):
    pass
  
  if (price == UNREALISTICPRICE):
	  try:
	    url = "http://www.amazon.com/dp/" + isbn
	    content = urllib.urlopen(url).read()
	    prices = re.findall('Kindle Price:\s+</td>\s+<td>\s+<b class="priceLarge">\s+\$(\d+\.\d\d)\s+</b>', content)
	    price = int(float(prices[0]) * 100)
	  except (AttributeError, IndexError):
	    pass
  
  return [int(price), url]
  
def GetGooglePrice(isbn):
# return list with first element as price and second as url
  isbnurl = "https://www.googleapis.com/books/v1/volumes?q=" + isbn + "+isbn"
  content = urllib.urlopen(isbnurl).read()
  decoder = json.JSONDecoder()
  price = UNREALISTICPRICE
  url="google"
  
  try:
	id = decoder.decode(content)['items'][0]['id']
	idurl = "https://www.googleapis.com/books/v1/volumes/" + id
	
	content = urllib.urlopen(idurl).read()
	price = int(decoder.decode(content)['saleInfo']['retailPrice']['amount']*100)
	url = "https://play.google.com/store/books/details?id=" + id
  except KeyError:
    pass
  
  return [int(price), url]
                    
# --------------- Main Page -------------------

class MainPage(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      myuser = currentsession.user
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      myuser = []

    template_values = {
      'myuser': myuser,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': url,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

# ------------ Book Operations ------------------------

class SearchBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    if currentsession.user.id:
      user = currentsession.user
      logurl = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
      currenttime = datetime.datetime.now()
      timedelta = datetime.timedelta(days=30)
      timedeltatiny = datetime.timedelta(seconds=15)
      query = self.request.get('query')
    
      query = urllib.quote_plus(query)
      url = "http://www.goodreads.com/search.xml?key=" + GOODREADS_ACCESS_KEY_ID + "&q=" + query
    
      u = urllib.urlopen(url)
      response = u.read()
      results = xmlparser.xml2obj(response)
    
      books = []
    
      try:    
        for work in results.search.results.work:
          goodreadsid = str(work.id.data)
          if goodreadsid:
            book = Book()
            book.get(goodreadsid, connection = conn, addbook = False)
            if (str(book.date) < str(currenttime - timedelta)) or (str(book.date) > str(currenttime - timedeltatiny)):
              book.goodreadsid = goodreadsid
              book.title  = work.best_book.title
              book.author = work.best_book.author.name
              book.small_img_url = work.best_book.small_image_url
              book.date = currenttime
              book.put(connection = conn)
            books.append(book)
      except AttributeError as er:
        pass
    
    else:
      logurl = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      user = []
      books = []

    template_values = {
      'myuser': user,
      'books': books,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': logurl,
      'url_linktext': url_linktext,
    }
    
    conn.close()
    template = jinja_environment.get_template('search.html')
    self.response.out.write(template.render(template_values))

class AddBook(webapp2.RequestHandler):  
  def post(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    session = LoadSession(self.request.cookies, connection = conn)
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=session.user.notificationwaittime)

    goodreadsids = self.request.get_all('bookid')
    formats = self.request.get_all('format')
    labels = self.request.get_all('label')
    price = self.request.get('price')
    acceptedformats = []
    
    for goodreadsid in goodreadsids:
      goodreadsid = str(goodreadsid)
      book = Book()
      book.get(goodreadsid = goodreadsid, connection = conn)
      userbook = UserBook()
      userbook.userid = session.user.id
      userbook.bookid = book.id
      userbook.price = int(float(price) * 100)
      userbook.acceptedformats = formats
      userbook.labels = labels
      userbook.archived = False
      userbook.date = currenttime
      userbook.notified = currenttime - notifieddelta
      userbook.put(connection = conn)
      book.addtoqueue()

    conn.close()
    self.redirect('/search')

class ArchiveBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.archived = True
    userbook.date = datetime.datetime.now()
    userbook.put()
    self.redirect('/')
  
class RestoreBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.archived = False
    userbook.date = datetime.datetime.now()
    userbook.put()
    self.redirect('/')
  
class DeleteBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.delete()
    self.redirect('/')
    
class EditBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    book = Book()
    book.get(id = bookid, connection = conn)

    template_values = {
    	'book': book,
    	'myuser': currentsession.user,
    	'userbook': userbook,
    	'possibleformats': possibleformats,
    }
    
    template = jinja_environment.get_template('edit.html')
    self.response.out.write(template.render(template_values))

class ProduceDisplayBooksXML(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
  
    c.execute("SELECT bookid FROM userbooks WHERE userid = ?", (currentsession.user.id,)) 
    userbooks = c.fetchall()
    
    xmlfile = "<?xml version= \"1.0\"?><content>"
    for item in userbooks:
      userbook = UserBook()
      userbook.get(bookid = item[0], userid = currentsession.user.id, connection = conn)
      displaybook = DisplayBook()
      displaybook.get(userbook, currentsession.user, connection = conn)
      xmlfile = xmlfile + displaybook.xml()
    xmlfile = xmlfile + "</content>"
    xmlfile = xmlfile.replace("&", "&amp;")
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(xmlfile)

class BatchEdit(webapp2.RequestHandler):
  def get(self):
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)

    bookids = self.request.get_all('bookid')
    action = self.request.get('action')
    format = self.request.get('format')
    label = self.request.get('label')
    price = self.request.get('price')
    
    for bookid in bookids:
      userbook = UserBook()
      userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
      if (action == "addlabel"):
        if (label not in set(userbook.labels)):
          userbook.labels.append(label)
          userbook.labels.sort()
      elif (action == "removelabel"):
        if (label in set(userbook.labels)):
          userbook.labels.remove(label)
      elif (action == "addformat"):
        if (format not in set(userbook.acceptedformats)):
          userbook.acceptedformats.append(format)
          userbook.acceptedformats.sort()
          userbook.date = currenttime
          userbook.notified = currenttime - notifieddelta
          book = Book()
          book.get(id = userbook.bookid)
          book.updateEditions()
      elif (action == "removeformat"):
        if (format in set(userbook.acceptedformats)):
          userbook.acceptedformats.remove(format)
      elif (action == "price"):
        userbook.price = int(float(price) * 100)
        userbook.date = currenttime
        userbook.notified = currenttime - notifieddelta
      elif (action == "archive"):
        userbook.archived = True
        userbook.date = datetime.datetime.now()
      elif (action == "restore"):
        userbook.archived = False
        userbook.notified = currenttime - notifieddelta
        userbook.date = datetime.datetime.now()
      userbook.myput()

# --------------------------- Info Pages -------------------------

class About(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False

    template_values = {
      'loggedin': loggedin,
      'url': url,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('about.html')
    self.response.out.write(template.render(template_values))

class AccountSettings(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      user = currentsession.user
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      user = []

    template_values = {
      'myuser': user,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': url,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('accountsettings.html')
    self.response.out.write(template.render(template_values))

class CurrentDeals(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)
    
    if currentsession.user.id:
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      
#     books_query = db.GqlQuery("SELECT * FROM UserBook WHERE notified > :1 ORDER BY notified DESC", currenttime-notifieddelta)
#     userbooks = books_query.fetch(100)
#     
    displaybooks=[]
#     for userbook in userbooks:
#       userbook.acceptedformats = possibleformats  # Do not .put() this!
#       displaybooks.append(GetDisplayBook(userbook))

    template_values = {
      'books': displaybooks,
      'loggedin': loggedin,
      'url': url,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('currentdeals.html')
    self.response.out.write(template.render(template_values))

class Coupons(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)

    if currentsession.user.id:
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      
    dealsurl = "http://couponfeed.linksynergy.com/coupon?token=" + LINKSHARE_TOKEN
    u = urllib.urlopen(dealsurl)
    response = u.read()
    results = xmlparser.xml2obj(response)
    
    coupons=[]
    for deal in results.link:
      coupon = Coupon()
      coupon.offer = deal.offerdescription
      coupon.merchant = deal.advertisername
      coupon.url = deal.clickurl
      coupons.append(coupon)

    template_values = {
      'coupons': coupons,
      'loggedin': loggedin,
      'url': url,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('coupons.html')
    self.response.out.write(template.render(template_values))

class UpdateSettings(webapp2.RequestHandler):  
  def post(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    session = LoadSession(self.request.cookies, connection = conn)
    session.user.update(self.request, connection = conn)
    conn.close()
    self.redirect('/accountsettings')

# ----------------------------- CRON --------------------------------
    
def UpdateAllBooks(connection = ""):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  c.execute("SELECT id FROM books") 
  books = c.fetchall()
  
  for item in books:
    book = Book()
    book.get(id = item[0], connection = conn)
    book.updateEditions(connection = conn)
  
  if not connection:
    conn.close()

def UpdatePriceCron(connection = ""):
  currenttime = datetime.datetime.now()
  useremail = {}
  lowpricebooks = []
  notify = False
  
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  UpdateAllBooks(connection = conn)
  
  c.execute("SELECT bookid, userid FROM userbooks") 
  userbooks = c.fetchall()
  
  for item in userbooks:
    userbook = UserBook()
    userbook.get(bookid = item[0], userid = item[1], connection = conn)
    
    if userbook.archived:
      continue
    
    user = User()
    user.get(id = userbook.userid)
    notifieddelta = datetime.timedelta(days = int(user.notificationwaittime or 7))
    if (userbook.notified and (str(userbook.notified) > str(currenttime - notifieddelta))):
      continue

    book = Book()
    book.get(id = userbook.bookid, connection = conn)
    for format in userbook.acceptedformats:
      try:
        priceandurl = book.prices[format]
      except:
        continue
      if (priceandurl[0] != "") and (priceandurl[0] <= userbook.price):
        lowpricebook = LowPriceBooks()
        lowpricebook.email = userbook.email
        lowpricebook.email = myuser.preferredemail or userbook.email
        lowpricebook.title = book.title
        lowpricebook.author = book.author
        lowpricebook.format = format
        lowpricebook.price = FormatPrice(priceandurl[0])
        lowpricebook.url = priceandurl[1]
        lowpricebooks.append(lowpricebook)
        notify = True
      if notify:
        userbook.notified = currenttime
        userbook.put(connection = conn)
        notify = False
    
  for book in lowpricebooks:
    email = []
    if (book.email in useremail):
      email.append(useremail[book.email])
    else:
      email.append("The following book(s) have become available in your price range: \n\n")
    email.append(book.title)
    email.append("\n")
    email.append(book.author)
    email.append("\n")
    email.append(book.format)
    email.append(": ")
    email.append(book.price)
    email.append("\n")
    email.append(book.url)
    email.append("\n")
    email.append("\n")
    useremail[book.email] = "".join(email)
	
#     message = mail.EmailMessage(sender="Bibliosaur <lis@bibliosaur.com>", subject="You have new books available")
#                             
#   for key in useremail:
#     message.to = key
#     message.body = useremail[key]
#     message.bcc = "lis@bibliosaur.com"
#     message.send()
          
  if not connection:
    conn.close()
  
# -----------------------------  Final Stuff ---------------------


application = webapp2.WSGIApplication([('/', MainPage),
                               ('/search', SearchBook),
                               ('/login/google', google_login),
                               ('/logout', logout),
                               ('/login/google/auth', google_authenticate),
                               ('/archive', ArchiveBook),
                               ('/getdisplaybooks.xml', ProduceDisplayBooksXML),
                               ('/restore', RestoreBook),
                               ('/delete', DeleteBook),
                               ('/edit', EditBook),
                               ('/batchedit', BatchEdit),
                               ('/about', About),
                               ('/currentdeals', CurrentDeals),
                               ('/coupons', Coupons),
                               ('/accountsettings', AccountSettings),
                               ('/updatesettings', UpdateSettings),
                               ('/updatepricecron', UpdatePriceCron),
                               ('/add', AddBook)],
                              debug=True)


