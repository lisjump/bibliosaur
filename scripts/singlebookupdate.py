#!/usr/bin/python
# Takes one or more bookids on the command line and updates the book in the database

import bibliosaur
import sys

i = 1
count = len(sys.argv)
force = False
if str(sys.argv[1]).lower() in ["f", "force"]:
  force = True
  i = 2

for i in range(count):
  book = bibliosaur.Book()
  try:
    book.get(id = int(sys.argv[i]))
    print book.title
    book.updateEditions(force = force)
  except:
    pass