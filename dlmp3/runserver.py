from flask import Flask
server = Flask(__name__)
server.debug = True
server.secret_key = 'jeveuxdesloots'
server.config['PERMANENT_SESSION_LIFETIME'] = 15

def main():
	server.run()

# import dlmp3.views
