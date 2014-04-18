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

from sets import Set

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

GOOGLE_CLIENT_ID = "507497402664-k5r3h55tp2jvo0gc6s3vfu18a595k3mj.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "WUK3lud8Vmba67QTV3ZN2u65"

AMAZON_ACCESS_KEY_ID = "AKIAJLACG3YUCMD6J6VA"
AMAZON_SECRET_KEY = "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"
AMAZON_ASSOC_TAG = "bibliosaur-20"

GOODREADS_ACCESS_KEY_ID = "lPcMn63rHnsLm68Z0rJ7JA"
GOODREADS_SECRET_KEY = "Wao8bdLUhd6xV7buxu0wsVEPp44PiwJPrhR6fxuhQ"

LINKSHARE_TOKEN = "b917e3ab2eca8c51d4900d42b6670b964c1fcfa66b86b532f032d587b7bf4b3d"
LINKSHARE_ID = "ZwPyGgVrkHA"
BN_TOKEN = "LS2983889"

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
    def post(self):
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

# -------------------------- Session and User Data -------------------------------

def LoadSession(cookies):
  session = Session()
  sessionid = ""
  
  try: 
    sessionid = cookies.get('sessionid')
  except:
    pass  
  
  if sessionid:
    session.load(id=sessionid)

  return session
  

class Session():
  def __init__(self, id = None):
    self.id = id
    self.user = User()
  
  def load(self, id, cursor = None):
    if cursor:
      c = cursor
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
    
    if not cursor:
      conn.close()
    return
  
  def login(self):
    self.id = self.user.preferredemail.split('@')[0] + str(random.getrandbits(128))
    cookie = {}
    cookie['key'] = "sessionid"
    cookie['value'] = self.id
    cookie['expires'] = datetime.datetime.now() + datetime.timedelta(days=7) 
    
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    with conn:
      c.execute("INSERT or REPLACE INTO session (id, userid, expire) VALUES (?, ?, ?)", (self.id, self.user.id, cookie['expires']))
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
  
  def fetchUser(self, id = None, googleemail = None, cursor = None):
    if cursor:
      c = cursor
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
      c = conn.cursor()

    if googleemail:
      self.googleemail = str(googleemail)
      c.execute("select count(*) from users where googleemail = ?", (self.googleemail,))
      count = c.fetchall()[0][0]
      conn.close()
      if count == 0:
        self.put()
      elif count == 1:
        self.get(googleemail = self.googleemail)
      else:
        logging.error("USER ERROR:  More than one user with gmail: " + self.googleemail)
    if id:
      self.id = id

    if not cursor:
      conn.close()
    
    return
  
  def get(self, id = None, googleemail = None, cursor = None):
    er = False
    if cursor:
      c = cursor
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
      c = conn.cursor()

    if id:
      c.execute("select count(*) from users where id = ?", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        c.execute("select id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels  from users where googleemail = ?", (id,))
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
    
    if not cursor:
      conn.close()
    
    return

  def put(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    if not self.preferredemail:
      self.preferredemail = self.googleemail
    with conn:
      c.execute("INSERT INTO users (preferredemail, googleemail, notificationwaittime) VALUES (?, ?, ?)", (self.preferredemail, self.googleemail, self.notificationwaittime))
    c.execute("select id from users where googleemail = ?", (self.googleemail,))
    result = c.fetchall()
    self.id = result[0][0]
    conn.close()    
  def mydelete(self):
    if (DEBUG >=10):
      logging.info("------- deleted myuser: " + self.registeredemail)
    self.delete()


# --------------------- Book Data ----------------------------
# class Book(db.Model):
#   goodreadsid = db.StringProperty()
#   title = db.StringProperty()
#   author = db.StringProperty()
#   small_img_url = db.StringProperty()
#   date = db.DateTimeProperty(auto_now_add=True)
#   lastupdatedprices = db.DateTimeProperty()
#   lastupdatededitions = db.DateTimeProperty()
#   editions = db.StringListProperty()
#   def myput(self):
#     self.put()
#     if (DEBUG >=10):
#       logging.info("------- put book: " + self.goodreadsid)
#   def mydelete(self):
#     if (DEBUG >=10):
#       logging.info("------- deleted book: " + self.goodreadsid)
#     self.delete()
#   
# class Edition(db.Model):
#   isbn = db.StringProperty() # or ASIN, et al
#   format = db.StringProperty()
#   lowestprice = db.IntegerProperty()
#   lowestpriceurl = db.StringProperty()
#   def myput(self):
#     self.put()
#     if (DEBUG >=10):
#       logging.info("------- put edition: " + self.isbn)
#   def mydelete(self):
#     if (DEBUG >=10):
#       logging.info("------- put edition: " + self.isbn)
#     self.delete()
#   
# class UserBook(db.Model):
#   email = db.StringProperty()
#   goodreadsid = db.StringProperty()
#   acceptedformats = db.StringListProperty()
#   price = db.IntegerProperty()
#   date = db.DateTimeProperty()
#   archived = db.BooleanProperty()
#   notified = db.DateTimeProperty()
#   labels = db.StringListProperty()
#   def myput(self):
#     self.put()
#     if (DEBUG >=10):
#       logging.info("------- put userbook: " + self.goodreadsid)
#   def mydelete(self):
#     if (DEBUG >=10):
#       logging.info("------- deleted userbook: " + self.goodreadsid)
#     self.delete()
  
class Coupon():
  offer = str
  merchant = str
  url = str

class DisplayBook():
  goodreadsid = str
  title = str
  author = str
  small_img_url = str
  price = str
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
    return xmlstring

class LowPriceBooks():
  email = str
  title = str
  author = str
  format = str
  price = str
  url = str
    
def booklist_key(booklist_name=None):
#   return db.Key.from_path('booklist', booklist_name or 'default_booklist')
  return

def book_key(book_id=None):
#   return db.Key.from_path('Book', book_id or 'default_booklist')
  return

def user_key(email=None):
#   return db.Key.from_path('MyUser', email or 'default_user')
  return

def FormatPrice(price):
  if (price == UNREALISTICPRICE):
    return ""
  try:
    return "$%d.%2.2d" % (price/100, price%100)
  except TypeError:
    return 
  
def GetBook(goodreadsid, addbook=True):
  book = Book.get_or_insert(parent=booklist_key(), key_name=goodreadsid)
  if addbook and not book.goodreadsid:
    book.goodreadsid = goodreadsid
  if addbook and not book.author:
    book = FixBook(book)
    book.myput()
  return book

def GetUserBook(goodreadsid, email):
  userbook = UserBook.get_or_insert(parent=user_key(email), key_name=goodreadsid)
  return userbook

def GetDisplayBookXML(userbook, myuser):
  displaybook = GetDisplayBook(userbook, myuser)
  xmlbook = displaybook.xml().encode('utf-8')
  return xmlbook

def GetDisplayBook(userbook, myuser=None):
  displaybook = DisplayBook()
  displaybook.goodreadsid = userbook.goodreadsid
  displaybook.acceptedformats = userbook.acceptedformats
  displaybook.formatprices = dict.fromkeys(displaybook.acceptedformats)
  displaybook.formaturls = dict.fromkeys(displaybook.acceptedformats)
  displaybook.price = FormatPrice(userbook.price)
  displaybook.dateadded = str(userbook.date)
  displaybook.labels = []
  
  book = GetBook(userbook.goodreadsid)
  displaybook.author = book.author
  displaybook.title  = book.title
  displaybook.small_img_url = book.small_img_url
  if (myuser):
    displaybook.labels = list(set(userbook.labels) & set(myuser.labels))
  if userbook.archived:
    displaybook.labels.append('archived')

  for format in displaybook.acceptedformats:
    priceandurl = LowestFormatPrice(displaybook.goodreadsid, format)
    if (priceandurl[0] <= userbook.price):
      displaybook.priceavailable = True
      if (priceandurl[0] <= 0):
        displaybook.free = True
    displaybook.formatprices[format] = FormatPrice(priceandurl[0])
    displaybook.formaturls[format] = priceandurl[1]
    
  return displaybook

def GetEditionsByAncestor(goodreadsid, format=None):
    equery = Edition.all()
    equery.ancestor(book_key(goodreadsid))
    if format:
      equery.filter("format =", format)
    editions = equery.fetch(limit=1000)
    return editions

def FixBook(book):
	editionurl = "http://www.goodreads.com/work/editions/" + book.goodreadsid
	content = urllib.urlopen(editionurl).read()
	splitcontent = content.split('\n')
	
	gottitle = False
	gotimage = False
	
	for line in splitcontent:
		title = re.findall('.*Editions\s+of\s+(.*)\s+by\s+.*', line)
		author = re.findall('.*Editions\s+of\s+.*\s+by\s+(.*)\<.*', line)
		image = re.findall('.*(http://d.gr-assets.com/books/.*jpg).*', line)
		
		if title and author:
			book.title = title[0]
			book.author = author[0]
			gottitle = True
		elif image:
			book.small_img_url = image[0]
			gotimage = True
		
		if gottitle and gotimage:
			break
	
	if gottitle is False:
		book.title = "missing - please contact lis@bibliosaur.com"
		book.author = "missing - please contact lis@bibliosaur.com"
	
	if gotimage is False:
		book.small_img_url = ""
		  
	return book

# ----------------------Price Getting and Comparing ----------------

def UpdateAllPrices(goodreadsid, queue=False):
    editions = GetEditionsByAncestor(goodreadsid)
    
    if (DEBUG >= 5):
      logging.info("-------- UPDATING prices on " + str(len(editions)) + " editions for id " + goodreadsid)

    for edition in editions:
      try:
        UpdatePrice(edition)
        if (DEBUG >=5):
          logging.info("----------- updated " + str(edition.isbn) + "price: " + str(edition.lowestprice))
        if queue:
          time.sleep(1)
      except urllib2.HTTPError:
        time.sleep(.5)
        pass
      except:
        logging.info("-UPDATE Failed for isbn " +  str(edition.isbn) + " for id " + goodreadsid)
    
def LowestFormatPrice(goodreadsid, format):
# return list with first element as price and second as url
    editions = GetEditionsByAncestor(goodreadsid, format)
    
    currentlowestprice = UNREALISTICPRICE
    currenturl = format

    for edition in editions:
      if (edition.lowestprice != None) and (edition.lowestprice < currentlowestprice):
        currentlowestprice = edition.lowestprice
        currenturl = edition.lowestpriceurl
    
    return [currentlowestprice, currenturl]
    
def UpdatePrice(edition):
  currentlowestprice = UNREALISTICPRICE
  currenturl = ""
  prices = {}

  if (edition.format == "kindle"):
    prices['kindle'] = GetKindlePrice(edition.isbn)
  elif (edition.format == "hardcover") or (edition.format == "paperback") or (edition.format == "librarybinding"):
    prices['amazon'] = GetAmazonPrice(edition.isbn)
#     prices['bn'] = GetBNPrice(edition.isbn)
  elif (edition.format == "epub"):
    prices['bn'] = GetBNPrice(edition.isbn)
    prices['google'] = GetGooglePrice(edition.isbn)
  elif (edition.format == "audiobook"):
    prices['amazon'] = GetAmazonPrice(edition.isbn)
    prices['bn'] = GetBNPrice(edition.isbn)
  else:
    return
  
  for key in prices.keys():
    if (int(prices[key][0]) < int(currentlowestprice)):
      currentlowestprice = int(prices[key][0])
      currenturl = prices[key][1]
  
  if (edition.lowestprice == currentlowestprice):
    return
    
  edition.lowestprice = currentlowestprice  
  edition.lowestpriceurl = currenturl
  
  if (edition.lowestprice == UNREALISTICPRICE):
    edition.mydelete()
    return
  
  edition.myput()
  
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
  
# -------------------- Edition Stuff -------------------------------  

class InsertAndUpdateEditionsQueue(webapp2.RequestHandler):
    def post(self):
      goodreadsid = self.request.get('goodreadsid')
      InsertAndUpdateEditions(goodreadsid, True)

def InsertAndUpdateEditions(goodreadsid, queue=False):
  currenttime = datetime.datetime.now()
  timeforeditionupdate = datetime.timedelta(days=7) 
  timeforpriceupdate = datetime.timedelta(hours=8)
  book = GetBook(goodreadsid)
  
#   if True:
  if not (book.lastupdatededitions) or not (book.lastupdatededitions > currenttime - timeforeditionupdate):
#     userbooks_query = db.GqlQuery("SELECT * FROM UserBook WHERE goodreadsid = :1", goodreadsid)
    userbook = userbooks_query.fetch(1)
    if not userbook:
      book.mydelete()
      return
    InsertGoodreadsEditions(goodreadsid)
    book.lastupdatededitions = currenttime
    book.lastupdatedprices = currenttime - 2*timeforeditionupdate # we need to make sure we update prices since we updated the editions
    book.myput()
  
#   if True:
  if not (book.lastupdatedprices) or not (book.lastupdatedprices > currenttime - timeforpriceupdate):
    UpdateAllPrices(goodreadsid, queue)
    book.lastupdatedprices = currenttime
    book.myput()

def InsertGoodreadsEditions(goodreadsid):
  editionurl = "http://www.goodreads.com/work/editions/" + goodreadsid
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
        edition = Edition.get_or_insert(parent=book_key(goodreadsid), key_name=isbn)
        edition.isbn = isbn
        edition.format = lastformat
        edition.myput() # optimize by checking date here
        isbnlast = True
    except IndexError:
      print isbn
      pass
    
    try:
      isbn = asin[0]
      if not isbnlast:
        edition = Edition.get_or_insert(parent=book_key(goodreadsid), key_name=isbn)
        edition.isbn = isbn
        edition.format = lastformat
        edition.myput() # optimize by checking date here
        isbnlast = True
    except IndexError:
      print isbn
      pass
                  
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
#     if users.get_current_user():
#       myuser = GetMyUser(users.get_current_user().email())
#       url = users.create_logout_url(self.request.uri)
#       url_linktext = 'Logout'
#       loggedin = True 
#       
#       currenttime = datetime.datetime.now()
#       timedelta = datetime.timedelta(days=30)
#       timedeltatiny = datetime.timedelta(seconds=15)
#       query = self.request.get('query')
#     
#       query = urllib.quote_plus(query)
#       url = "http://www.goodreads.com/search.xml?key=" + GOODREADS_ACCESS_KEY_ID + "&q=" + query
#     
#       u = urllib.urlopen(url)
#       response = u.read()
#       results = xmlparser.xml2obj(response)
#     
#       books = []
#     
#       try:    
#         for work in results.search.results.work:
#           goodreadsid = work.id.data
#           if goodreadsid:
#             book = GetBook(goodreadsid, False)
#             if (book.date < currenttime - timedelta) or (book.date > currenttime - timedeltatiny):
#               book.goodreadsid = goodreadsid
#               book.title  = work.best_book.title
#               book.author = work.best_book.author.name
#               book.small_img_url = work.best_book.small_image_url
#               book.date = currenttime
#               book.myput()
#             books.append(book)
#       except AttributeError:
#         pass
#     
#     else:
#       myuser = ""
#       url = users.create_login_url(self.request.uri)
#       url_linktext = 'Login'
#       loggedin = False
#       books = []
          
    template_values = {
    	'books': books,
    	'myuser': myuser,
    	'possibleformats': possibleformats,
        'loggedin': loggedin,
        'url': url,
        'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('search.html')
    self.response.out.write(template.render(template_values))

class AddBook(webapp2.RequestHandler):  
  def get(self):
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)

    bookids = self.request.get_all('bookid')
    formats = self.request.get_all('format')
    labels = self.request.get_all('label')
    price = self.request.get('price')
#     u_key = user_key(users.get_current_user().email())
    acceptedformats = []
    
    for bookid in bookids:
#       userbook = GetUserBook(bookid, users.get_current_user().email())
#       userbook.email = users.get_current_user().email()
      userbook.goodreadsid = bookid
      userbook.price = int(float(price) * 100)
      userbook.acceptedformats = formats
      userbook.labels = labels
      userbook.archived = False
      userbook.date = currenttime
      userbook.notified = currenttime - notifieddelta
      userbook.myput()
      book = GetBook(userbook.goodreadsid)
      book.myput()
#       taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})

  def post(self):
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)

    bookids = self.request.get_all('bookid')
    formats = self.request.get_all('format')
    labels = self.request.get_all('label')
    price = self.request.get('price')
#     u_key = user_key(users.get_current_user().email())
    acceptedformats = []
    
    for bookid in bookids:
#       userbook = GetUserBook(bookid, users.get_current_user().email())
#       userbook.email = users.get_current_user().email()
      userbook.goodreadsid = bookid
      userbook.price = int(float(price) * 100)
      userbook.acceptedformats = formats
      userbook.labels = labels
      userbook.archived = False
      userbook.date = currenttime
      userbook.notified = currenttime - notifieddelta
      userbook.myput()
      book = GetBook(userbook.goodreadsid)
      book.myput()
#       taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})

    self.redirect('/search')

class ArchiveBook(webapp2.RequestHandler):
  def get(self):
    currenttime = datetime.datetime.now()
    bookid = self.request.get('bookid')
#     userbook = GetUserBook(bookid, users.get_current_user().email())
    userbook.archived = True
    userbook.date = currenttime
    userbook.myput()
  
class RestoreBook(webapp2.RequestHandler):
  def get(self):
    currenttime = datetime.datetime.now()
    bookid = self.request.get('bookid')
#     userbook = GetUserBook(bookid, users.get_current_user().email())
    userbook.archived = False
    userbook.date = currenttime
    userbook.myput()
  
class DeleteBook(webapp2.RequestHandler):
  def get(self):
    bookid = self.request.get('bookid')
#     userbook = GetUserBook(bookid, users.get_current_user().email())
    userbook.mydelete()
  
    self.redirect('/')
    
class EditBook(webapp2.RequestHandler):
  def get(self):
#     myuser = GetMyUser(users.get_current_user().email())
    bookid = self.request.get('bookid')
    book = GetBook(bookid)
#     userbook = GetUserBook(bookid, users.get_current_user().email())

    template_values = {
    	'book': book,
    	'myuser': myuser,
    	'userbook': userbook,
    	'possibleformats': possibleformats,
    }
    
    template = jinja_environment.get_template('edit.html')
    self.response.out.write(template.render(template_values))

class ProduceDisplayBooksXML(webapp2.RequestHandler):
  def get(self):
	  xmlfile = "<?xml version= \"1.0\"?>"
	  xmlfilecontent = open(topleveldirectory + '/getdisplaybooks.xml')
	  xmlfile = xmlfilecontent.read()
	  xmlfilecontent.close()

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
#       userbook = GetUserBook(bookid, users.get_current_user().email())
      if (action == "addlabel"):
        if (label not in set(userbook.labels)):
          userbook.labels.append(label)
          userbook.labels.sort()
          if (DEBUG >= 10):
            logging.info("----------------- added " + label)
      elif (action == "removelabel"):
        if (label in set(userbook.labels)):
          userbook.labels.remove(label)
          if (DEBUG >= 10):
            logging.info("----------------- added " + label)
      elif (action == "addformat"):
        if (format not in set(userbook.acceptedformats)):
          userbook.acceptedformats.append(format)
          userbook.acceptedformats.sort()
          if (DEBUG >= 10):
            logging.info("----------------- added " + format)
        userbook.date = currenttime
        userbook.notified = currenttime - notifieddelta
#         taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})  
      elif (action == "removeformat"):
        if (format in set(userbook.acceptedformats)):
          userbook.acceptedformats.remove(format)
          if (DEBUG >= 10):
            logging.info("----------------- added " + format)
      elif (action == "price"):
        userbook.price = int(float(price) * 100)
        userbook.date = currenttime
        userbook.notified = currenttime - notifieddelta
#         taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})  
      elif (action == "archive"):
        userbook.archived = True
        userbook.date = currenttime
      elif (action == "restore"):
        userbook.archived = False
        userbook.date = currenttime
        userbook.notified = currenttime - notifieddelta
#         taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})  
      userbook.myput()

# --------------------------- Info Pages -------------------------

class About(webapp2.RequestHandler):
    def get(self):
#         if users.get_current_user():
#             url = users.create_logout_url(self.request.uri)
#             url_linktext = 'Logout'
#             loggedin = True             
#         else:
#             url = users.create_login_url(self.request.uri)
#             url_linktext = 'Login'
#             loggedin = False

        template_values = {
            'loggedin': loggedin,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = jinja_environment.get_template('about.html')
        self.response.out.write(template.render(template_values))

class AccountSettings(webapp2.RequestHandler):
    def get(self):
#         if users.get_current_user():
#             myuser = GetMyUser(users.get_current_user().email())
#             url = users.create_logout_url(self.request.uri)
#             url_linktext = 'Logout'
#             loggedin = True             
#         else:
#             url = users.create_login_url(self.request.uri)
#             url_linktext = 'Login'
#             loggedin = False
#             myuser = ""

        template_values = {
            'myuser': myuser,
            'possibleformats': possibleformats,
            'loggedin': loggedin,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = jinja_environment.get_template('accountsettings.html')
        self.response.out.write(template.render(template_values))

class CurrentDeals(webapp2.RequestHandler):
    def get(self):
      currenttime = datetime.datetime.now()
      notifieddelta = datetime.timedelta(days=7)
      
#       if users.get_current_user():
#         url = users.create_logout_url(self.request.uri)
#         url_linktext = 'Logout'
#         loggedin = True             
#       else:
#         url = users.create_login_url(self.request.uri)
#         url_linktext = 'Login'
#         loggedin = False
        
#       books_query = db.GqlQuery("SELECT * FROM UserBook WHERE notified > :1 ORDER BY notified DESC", currenttime-notifieddelta)
      userbooks = books_query.fetch(100)
      
      displaybooks=[]
      for userbook in userbooks:
        userbook.acceptedformats = possibleformats  # Do not .put() this!
        displaybooks.append(GetDisplayBook(userbook))

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
#       if users.get_current_user():
#         url = users.create_logout_url(self.request.uri)
#         url_linktext = 'Logout'
#         loggedin = True             
#       else:
#         url = users.create_login_url(self.request.uri)
#         url_linktext = 'Login'
#         loggedin = False
        
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
#     myuser = GetMyUser(users.get_current_user().email())
    myuser.preferredemail = self.request.get('preferredemail')
    price = self.request.get('defaultprice')
    try:
      myuser.defaultprice = int(float(price) * 100)
    except ValueError:
      myuser.defaultprice = None
    myuser.defaultformats = self.request.get_all('format')
    myuser.notificationwaittime = int(self.request.get('wait'))
    myuser.preferredsort = self.request.get('sortorder')
    if (self.request.get_all('ascdesc')[0] == "ascending"):
      myuser.ascending = True
    else:
      myuser.ascending = False

    oldlabels = myuser.labels
    labels = Set()
    tabs = Set()
    myuser.labels = []
    myuser.tabs = []
    for i in range(20):
      label = self.request.get('label' + str(i))
      if (label):
        labels.add(label)
    for label in labels:
      myuser.labels.append(label)
    myuser.labels.sort() 
    
    myuser.myput()

    self.redirect('/accountsettings')

# ----------------------------- CRON --------------------------------
    
class UpdatePriceCron(webapp2.RequestHandler):
  def get(self):
    currenttime = datetime.datetime.now()
    useremail = {}
    lowpricebooks = []
    notify = False
    
#     userbooks_query = db.GqlQuery("SELECT * FROM UserBook") 
    userbooks = userbooks_query.fetch(None)
        
    for userbook in userbooks:
#       taskqueue.add(url='/insertandupdateeditions', params={'goodreadsid': userbook.goodreadsid})
      for format in userbook.acceptedformats:
        priceandurl = LowestFormatPrice(userbook.goodreadsid, format)
        if (priceandurl[0] != "") and (priceandurl[0] <= userbook.price):
          myuser = GetMyUser(userbook.email)
          days = int(myuser.notificationwaittime or 1)*7
          notifieddelta = datetime.timedelta(days = days)
          if (userbook.notified) and (userbook.notified < currenttime - notifieddelta) and not (userbook.archived):
			  book = GetBook(userbook.goodreadsid)
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
        userbook.myput()
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
	
    message = mail.EmailMessage(sender="Bibliosaur <lis@bibliosaur.com>", subject="You have new books available")
                            
    for key in useremail:
      message.to = key
      message.body = useremail[key]
      message.bcc = "lis@bibliosaur.com"
      message.send()
          
# -----------------------------  Final Stuff ---------------------


application = webapp2.WSGIApplication([('/', MainPage),
                               ('/search', SearchBook),
                               ('/login/google', google_login),
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
                               ('/insertandupdateeditions', InsertAndUpdateEditionsQueue),
                               ('/updatepricecron', UpdatePriceCron),
                               ('/add', AddBook)],
                              debug=True)


