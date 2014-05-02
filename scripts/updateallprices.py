#!/usr/bin/python

import bibliosaur
import sys

force = False
count = len(sys.argv)
if count > 1:
  if str(sys.argv[1]).lower() in ["f", "force"]:
    force = True

bibliosaur.UpdatePriceCron(force = force)    