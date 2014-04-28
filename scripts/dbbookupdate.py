#!/usr/bin/python
# Checks the DB table for bookids to update

import bibliosaur
import sys
import sqlite3
import os

if os.path.isfile(bibliosaur.topleveldirectory + "/updatingbooks"):
  sys.exit()

open(bibliosaur.topleveldirectory + "/updatingbooks", 'a').close()
# touch it if it doesn't

conn = sqlite3.connect(bibliosaur.topleveldirectory + "/" + bibliosaur.db)
c = conn.cursor()

c.execute("select bookid from bookupdatequeue")
bookids = c.fetchall()
with conn:
  c.execute("delete from bookupdatequeue")
conn.close()

for bookid in bookids:
  print bookid[0]
  book = bibliosaur.Book()
  try:
    book.get(id = int(bookid[0]))
    book.updateEditions()
  except:
    pass
    

os.remove(bibliosaur.topleveldirectory + "/updatingbooks")