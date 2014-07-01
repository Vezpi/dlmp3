from flask import Flask
server = Flask(__name__)
server.debug = True
server.secret_key = 'jeveuxdesloots'
server.config['PERMANENT_SESSION_LIFETIME'] = 600
server.config['PASSWORD'] = "cl"

def main():
	server.run()

import views
