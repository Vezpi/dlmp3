#! /usr/bin/python
# -*- coding:utf-8 -*-

import argparse

__license__ = "GPLv3"
__authot__ = "Vezpi"
__version__ = "0.01.0"

def launcher():
    parser = argparse.ArgumentParser(description='Music MP3 downloader')
    parser.add_argument('-w', '--web', action='store_true', help='launch the web server')
    parser.add_argument('-d', '--daemon', action='store_true', help='the server is launched as a daemon')
    parser.add_argument('-v','--version', action='version', version=__version__, help='print the version of the application')
    args = parser.parse_args()
    if args.web:
        from dlmp3 import server
        server.run()
    else:
        from dlmp3 import terminal
        terminal.main()

if __name__ == '__main__':
    launcher()