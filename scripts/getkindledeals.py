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

bibliosaur.GetKindleDeals(conn)