# -*- coding:utf-8 -*-

from runserver import server
from flask import request, make_response, abort, redirect, render_template, session, flash
from PIL import Image
from StringIO import StringIO
from datetime import date
import time
from dlmp3 import application, config
import searcher

def get_song_from_list(songid):
    return [song for song in application.songlist if song['link'] == songid]

def downloading(song, filename):
    """ Download file, show status, return filename. """
    # xprint("Downloading %s%s%s ..\n" % (Color.green, filename, Color.white))
    # status_string = ('  {0}{1:,}{2} Bytes [{0}{3:.2%}{2}] received. Rate: '
    #                  '[{0}{4:4.0f} kbps{2}].  ETA: [{0}{5:.0f} secs{2}]')
    song['track_url'] = searcher.get_stream(song)
    resp = searcher.urlopener(song['track_url'])
    total = int(resp.info()['Content-Length'].strip())
    chunksize, bytesdone, t0 = 16384, 0, time.time()
    outfh = open(filename, 'wb')
    while True:
        chunk = resp.read(chunksize)
        outfh.write(chunk)
        elapsed = time.time() - t0
        bytesdone += len(chunk)
        rate = (bytesdone / 1024) / elapsed
        eta = (total - bytesdone) / (rate * 1024)
        # stats = (Color.yellow, bytesdone, Color.white, bytesdone * 1.0 / total, rate, eta)
        if not chunk:
            outfh.close()
            break
        # status = status_string.format(*stats)
        # sys.stdout.write("\r" + status + ' ' * 4 + "\r")
        # sys.stdout.flush()
    return filename

@server.route('/', methods=['GET', 'POST'])
def index():
    if not 'logged_in' in session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            if request.form['recherche']:
                term = request.form['recherche']
                songs = searcher.do_search(term)
                if songs:
                    flash(u'Résultats de la recherche pour ' + term)
                else:
                    flash(u'Rien trouvé pour ' + term)
        return render_template('index.html', songs=application.songlist)

@server.route('/download=<songid>')
def download(songid):
    if not 'logged_in' in session:
        return redirect('/login')
    else:
        song = get_song_from_list(songid)
        filename = searcher.make_filename(song[0])
        flash(u'Téléchargement de '+ filename)
        if downloading(song[0], filename):
            flash(u'Téléchargement terminé')
        else:
            flash(u'Téléchargement en erreur')
        return redirect('/')

# @server.route('/top')
# def top():
#     if not 'logged_in' in session:
#         return redirect('/login')
#     else:

@server.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['PASSWORD'] == server.config['PASSWORD']:
            session['logged_in'] = True
            flash(u'Vous êtes connecté')
            return redirect('/')
        else:
            error = 'Invalid password'
    return render_template('login.html', error=error)
    
        



















@server.route('/sandbox')
def sandbox():
    return render_template('sandbox.html')

# @server.route('/old')
# def index_old():
#     pw_visiteur = request.cookies.get('pw') # on récupère le cookie 'pw'
#     if pw_visiteur is not None:
#         return "C'est un plaisir de se revoir, {pw} !".format(pw=pw_visiteur)
#     else:
#         reponse = make_response("Bonjour, c'est votre première visite ?")
#         reponse.set_cookie('pw', 'Toto')
#         return reponse

# @server.route('/date')
# def fdate():
#     d = date.today().isoformat()
#     t = "La date du jour"
#     return render_template('accueil.html',texte=t, la_date=d)

# @server.route('/la')
# def la():
#     return "Le chemin est " + request.path 

# @server.route('/contact/', methods=['GET', 'POST'])
# def contact():
#     if request.method == 'POST':
#         return "Vous avez envoyé : {msg}".format(msg=request.form['msg'])
#     return '<form action="" method="post"><input type="text" name="msg" /><input type="submit" value="Envoyer" /></form>'

# @server.route('/contact2') # on n'autorise pas la méthode POST
# def contact2():
#     if request.args.get('msg') is not None:
#         return "Vous avez envoyé : {msg}".format(msg=request.args['msg'])
#     return '<form action="" method="get"><input type="text" name="msg" /><input type="submit" value="Envoyer" /></form>'    

# @server.route('/discussion/')
# @server.route('/discussion/page/<int:num_page>')
# def mon_chat(num_page = 1):
#     premier_msg = 1 + 50 * (num_page - 1)
#     dernier_msg = premier_msg + 50
#     return 'affichage des messages {} à {}'.format(premier_msg, dernier_msg)

# @server.route('/image')
# def genere_image():
#     mon_image = StringIO()
#     Image.new("RGB", (300,300), "#92C41D").save(mon_image, 'BMP')
#     reponse = make_response(mon_image.getvalue())
#     reponse.mimetype = "image/bmp"  # à la place de "text/html"
#     return reponse

@server.route('/404')
def page_non_trouvee():
    return "Cette page devrait vous avoir renvoyé une erreur 404", 404

@server.errorhandler(401)
@server.errorhandler(404)
@server.errorhandler(405)
@server.errorhandler(500)
def ma_page_erreur(error):
    return "Ma jolie page {}".format(error.code), error.code

# @server.route('/profil')
# def profil():
#     if utilisateur_non_identifie:
#         abort(401)
#     return "Vous êtes bien identifié, voici la page demandée : ..."

# @server.route('/google')
# def redirection_google():
#     return redirect('http://www.google.fr')
