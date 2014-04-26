#!/usr/bin/python

import bibliosaur
import sys
import sqlite3

# check if file exists
# exit if it does
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
    

# delete file