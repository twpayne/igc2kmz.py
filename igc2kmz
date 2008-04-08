#!/usr/bin/python

import fileinput
import optparse
import sys

import igc
from track import Hints, Track

def main():
  track = igc.IGC(fileinput.input()).track()
  track.kmz(Hints()).write('t.kmz')

if __name__ == '__main__':
  main()
