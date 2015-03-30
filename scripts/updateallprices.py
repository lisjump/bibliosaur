#!/usr/bin/python

import bibliosaur
import sys

force = False
useronly = False

count = len(sys.argv)
if count > 1:
  if str(sys.argv[1]).lower() in ["f", "force"]:
    force = True
  if str(sys.argv[1]).lower() in ["u", "useronly"]:
    print "Useronly true"
    useronly = True

bibliosaur.UpdatePriceCron(force = force, useronly = useronly)    