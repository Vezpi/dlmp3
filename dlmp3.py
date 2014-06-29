#! /usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import dlmp3

__author__ = "Vezpi"
__version__ = "0.01.0"
__license__ = "GPLv3"

def launcher():
    parser = argparse.ArgumentParser(description='Music MP3 downloader')
    parser.add_argument('-w', '--web', action='store_true', help='launch the web server')
    parser.add_argument('-d', '--daemon', action='store_true', help='the server is launched as a daemon')
    parser.add_argument('-v','--version', action='version', version=__version__, help='print the version of the application')
    args = parser.parse_args()
    if args.web:
        dlmp3.launch_server()
    else:
        dlmp3.launch_terminal()

if __name__ == '__main__':
    launcher()