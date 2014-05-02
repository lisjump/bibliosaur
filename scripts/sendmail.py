#!/usr/bin/python
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
import smtplib
from email.mime.text import MIMEText
import bibliosaur

# -------------- Definitions and Environment ---------------

toplevelurl = "http://dev.bibliosaur.com"
topleveldirectory = "/var/www/dev.bibliosaur.com"
db = "bibliosaur.db"

bcc = []
subject = "Bibliosaur Updates"
body = '''Please forgive this email, it is the first bulk email I have sent and hopefully the last, but I wanted everyone to know about some changes to bibliosaur.

If you have used the app often, you will probably have noticed its frequent time outs and lack of service.  This is because Google App Engine has been hosting bibliosaur and they have a strict limit to the number of free database operations that can be performed each day.  Since bibliosaur is not a very profitable app (it earns about $0.50/month), I could not justify paying for more database operations and was willing to live with a few outages.

However, lately the outages have become much worse and I decided it was time for a more permanent fix.  I am now hosting bibliosaur on my own webserver with my own database.  This means that I have unlimited database operations and a much more reliable connection.  It does, have the small setback of being independently run, so if the server goes down while no one is around to fix it, there may be a short outage until it can be brought back to life.

In the long run, I think this is a good move and I have ported all of the App Engine databases to the new server.  There were a few problems and a handful of books were not able to be properly converted, so please look through your books and let me know if there are any problems I need to fix.  Also, if you've added any books to the site in the past week, please make sure to re-add them.

Google App Engine will still be serving http://www.bibliosaur.com until this weekend so that you can compare your books as desired.  The new site is available at http://dev.bibliosaur.com.  The database is stable, so please feel free to begin adding new books to this site.  When I switch the server, I will be sure to post a message on dev site to let you know to start using the www site.  After the switch, the old data will be available at librosopticon.appspot.com for around a month.

Thank you for your support, and please let me know of any issues you encounter or suggestions you may have!

- Lis @ bibliosaur

P.S.  It may take a few days to get all of the prices updated, so please don't worry if they are not yet accurate.
'''

conn = sqlite3.connect(topleveldirectory + "/" + db)
c = conn.cursor()
  
c.execute("SELECT preferredemail FROM users") 
users = c.fetchall()
for user in users:
  to = [user[0]]
  bibliosaur.SendMail(to, [], bcc, subject, body)