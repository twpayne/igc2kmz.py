#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import igc

def main(argv):
  for arg in argv[1:]:
    try:
      igc.IGC(arg)
    except igc.SyntaxError, line:
      print "%s: %s" % (arg, line)

if __name__ == '__main__':
  main(sys.argv)
