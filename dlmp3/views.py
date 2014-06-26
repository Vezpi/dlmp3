#! /usr/bin/python
# -*- coding:utf-8 -*-

from dlmp3 import server
from flask import request, make_response, abort, redirect, render_template, session
from PIL import Image
from StringIO import StringIO
from datetime import date

@server.route('/')
def index_get():
    if not 'ok' in session:
        return redirect('/login')
            
    else:
        return "C'est un plaisir de se revoir toto! "


@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['pw'] = request.form['pw']
        if session['pw'] == 'cl':
            session['ok'] = 1
        else:
            return "Mot de passe incorrect"

        # return "Bonjour {pw}".format(pw=request.form['pw'])
        

    if not 'ok' in session:
        return "Mot de passe : " + '<form action="" method="post"><input type="text" name="pw" /><input type="submit" value="OK" /></form>'

    return redirect('/')
        


@server.route('/old')
def index_old():
    pw_visiteur = request.cookies.get('pw') # on récupère le cookie 'pw'
    if pw_visiteur is not None:
        return "C'est un plaisir de se revoir, {pw} !".format(pw=pw_visiteur)
    else:
        reponse = make_response("Bonjour, c'est votre première visite ?")
        reponse.set_cookie('pw', 'Toto')
        return reponse

@server.route('/date')
def fdate():
    d = date.today().isoformat()
    t = "La date du jour"
    return render_template('accueil.html',texte=t, la_date=d)

@server.route('/la')
def la():
    return "Le chemin est " + request.path 

@server.route('/contact/', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return "Vous avez envoyé : {msg}".format(msg=request.form['msg'])
    return '<form action="" method="post"><input type="text" name="msg" /><input type="submit" value="Envoyer" /></form>'

@server.route('/contact2') # on n'autorise pas la méthode POST
def contact2():
    if request.args.get('msg') is not None:
        return "Vous avez envoyé : {msg}".format(msg=request.args['msg'])
    return '<form action="" method="get"><input type="text" name="msg" /><input type="submit" value="Envoyer" /></form>'    

@server.route('/discussion/')
@server.route('/discussion/page/<int:num_page>')
def mon_chat(num_page = 1):
    premier_msg = 1 + 50 * (num_page - 1)
    dernier_msg = premier_msg + 50
    return 'affichage des messages {} à {}'.format(premier_msg, dernier_msg)

@server.route('/image')
def genere_image():
    mon_image = StringIO()
    Image.new("RGB", (300,300), "#92C41D").save(mon_image, 'BMP')
    reponse = make_response(mon_image.getvalue())
    reponse.mimetype = "image/bmp"  # à la place de "text/html"
    return reponse

@server.route('/404')
def page_non_trouvee():
    return "Cette page devrait vous avoir renvoyé une erreur 404", 404

@server.errorhandler(401)
@server.errorhandler(404)
@server.errorhandler(405)
@server.errorhandler(500)
def ma_page_erreur(error):
    return "Ma jolie page {}".format(error.code), error.code

@server.route('/profil')
def profil():
    if utilisateur_non_identifie:
        abort(401)
    return "Vous êtes bien identifié, voici la page demandée : ..."

@server.route('/google')
def redirection_google():
    return redirect('http://www.google.fr')