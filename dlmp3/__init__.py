from flask import Flask

server = Flask(__name__)
server.debug = True
server.secret_key = 'jeveuxdesloots'
server.config['PERMANENT_SESSION_LIFETIME'] = 15

import dlmp3.views
import dlmp3.interpreter
