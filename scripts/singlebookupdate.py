#!/usr/bin/python

import bibliosaur
import sys

i = 1
count = len(sys.argv)

for i in range(count):
  if i == 0:
    continue
  print sys.argv[i]
  book = bibliosaur.Book()
  try:
    book.get(id = int(sys.argv[i]))
    book.updateEditions()
  except:
    pass