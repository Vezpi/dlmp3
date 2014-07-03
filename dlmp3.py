#! /usr/bin/python
# -*- coding:utf-8 -*-

from dlmp3 import launcher
import argparse

__author__ = "Vezpi"
__version__ = "0.01.0"
__license__ = "GPLv3"

def dlmp3_launcher():
    parser = argparse.ArgumentParser(description='Music MP3 downloader')
    parser.add_argument('-w', '--web', action='store_true', help='launch the web server')
    parser.add_argument('-d', '--daemon', action='store_true', help='NOT IMPLEMENTED the server is launched as a daemon')
    parser.add_argument('-p', '--port', type=int, help='specify the port which the server will listen')
    parser.add_argument('-v','--version', action='version', version=__version__, help='print the version of the application')
    parser.add_argument('-D','--debug', action='store_true', help='run in debug mode')
    args = parser.parse_args()
    if args.web:
        launcher.CLI = False
        if args.daemon:
            launcher.DAEMON = True
        if args.port:
        	launcher.PORT = args.port
        if args.debug:
        	launcher.DEBUG = True
    launcher.start()

if __name__ == '__main__':
    dlmp3_launcher()
