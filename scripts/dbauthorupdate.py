#!/usr/bin/python
# Checks the DB table for bookids to update

import bibliosaur
import sys
import sqlite3
import os

if os.path.isfile(bibliosaur.topleveldirectory + "/updatingauthors"):
  sys.exit()

open(bibliosaur.topleveldirectory + "/updatingauthors", 'a').close()
# touch it if it doesn't

conn = sqlite3.connect(bibliosaur.topleveldirectory + "/" + bibliosaur.db)
c = conn.cursor()

c.execute("select authorid from authorupdatequeue")
authorids = c.fetchall()
with conn:
  c.execute("delete from authorupdatequeue")
conn.close()

for authorid in authorids:
  print authorid[0]
  author = bibliosaur.Author()
  try:
    author.get(id = int(authorid[0]))
    author.updateBooks()
  except:
    pass
    
os.remove(bibliosaur.topleveldirectory + "/updatingauthors")