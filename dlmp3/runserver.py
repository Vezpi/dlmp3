from flask import Flask
from dlmp3 import launcher

server = Flask(__name__)
server.debug = launcher.DEBUG
server.secret_key = 'jeveuxdesloots'
server.config['PERMANENT_SESSION_LIFETIME'] = 600
server.config['PASSWORD'] = "cl"

def main():
    server.run(port=launcher.PORT)

import views
