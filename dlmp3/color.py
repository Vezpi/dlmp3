#! /usr/bin/python
# -*- coding:utf-8 -*-

from config import Config

class c(object):

    """ Class for holding colour code values. """

    white = "\x1b[%sm" % 0
    ul = "\x1b[%sm" * 3 % (2, 4, 33)
    cols = ["\x1b[%sm" % n for n in range(91, 96)]
    red, green, yellow, blue, pink = cols

    if not Config.COLOURS:
        ul = red = green = yellow = blue = pink = white = ""
    r, g, y, b, p, w = red, green, yellow, blue, pink, white