# -*- coding:utf-8 -*-

import unicodedata
import time
import sys
import re
import os

# Python 3 compatibility hack
if sys.version_info[:2] >= (3, 0):
    compat_input = input
else:
    compat_input = raw_input

from dlmp3 import config, session
from searcher import Search


class Color(object):
    """ Class for holding colour code values. """
    white = "\x1b[%sm" % 0
    underline = "\x1b[%sm" * 3 % (2, 4, 33)
    cols = ["\x1b[%sm" % n for n in range(91, 96)]
    red, green, yellow, blue, pink = cols
    if not config.COLOURS:
        ul = red = green = yellow = blue = pink = white = ""


HELP = """
{0}Rercherche{1}
Entrer le nom d'un artiste, le nom d'une chanson, les deux ensemble,
ou simplement des mots clés pour la recherche.
Si la recherche ne retourne pas ce que vous voulez, ajouter {2}+tous{1}
pour rechercher dans toutes les qualités de son.
Utiliser {2}n{1} et {2}p{1} pour naviguer parmis les differentes pages.

{0}Source{1}
Deux sources de téléchargement sont disponibles :
Pleer.com
Mp3download.pw
Pour sélectionner une source, entrer {2}c source <pleer / mp3download>{1}

{0}Téléchargement{1}
Quand une liste de musiques est affiché à l'écran, entrer le numéro
de la chanson correspondante pour la télécharger.

{0}Top{1}
Entrer {2}t{1} ({2}+ d/deezer{1}, {2}3m{1}, {2}6m{1}, {2}year{1}, {2}all{1}) pour afficher le top charts associé.
Defaut : Semaine
{2}d/deezer{1} : Deezer
{2}3m{1} : 3 mois
{2}6m{1} : 6 mois
{2}year{1} : annuel
{2}all{1} : de tout les temps

{0}configuration{1}
Entrer {2}c{1} pour afficher la configuration.

{0}Quitter{1}
Entrer {2}q{1} pour quitter.
""".format(Color.underline, Color.white, Color.green, Color.red)

def real_len(u):
    """ Try to determine width of strings displayed with monospace font. """
    ueaw = unicodedata.east_asian_width
    widths = dict(W=2, F=2, A=1, N=0.75, H=0.5)
    return int(round(sum(widths.get(ueaw(char), 1) for char in u)))

def uea_trunc(num, t):
    """ Truncate to num chars taking into account East Asian width chars. """
    while real_len(t) > num:
        t = t[:-1]
    return t

def uea_rpad(num, t):
    """ Right pad with spaces taking into account East Asian width chars. """
    t = uea_trunc(num, t)
    if real_len(t) < num:
        t = t + (" " * (num - real_len(t)))
    return t

def generate_songlist_display(song=False):
    """ Generate list of choices from a song list."""
    songs = session.songlist.songs or []
    if not songs:
        return
    if session.search.nature == "charts" and session.search.term ==  "deezer":
        fmtrow = "%s %-6s%-44s %-44s%s\n"
        head = (Color.underline, "Item", "Artist", "Track", Color.white)
        out = "\n" + fmtrow % head
        for number, x in enumerate(songs):
            col = (Color.red if number % 2 == 0 else Color.pink) if not song else Color.blue
            title = x.title or "unknown title"
            artist = x.artist or "unknown artist"
            if not song or song != songs[number]:
                out += (fmtrow % (col, str(number + 1), artist, title, Color.white))
            else:
                out += (fmtrow % (Color.pink, str(number + 1), artist, title, Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
    elif config.SOURCE == "pleer":
        fmtrow = "%s %-6s %-9s %-44s %-44s %-9s %-7s%s\n"
        head = (Color.underline, "Item", "Size", "Artist", "Track", "Length", "Bitrate", Color.white)
        out = "\n" + fmtrow % head
        for n, x in enumerate(songs):
            col = (Color.red if n % 2 == 0 else Color.pink) if not song else Color.blue
            size = x.size or 0
            title = x.title or "unknown title"
            artist = x.artist or "unknown artist"
            bitrate = x.bitrate or "unknown"
            duration = x.duration or "unknown length"
            art, tit = uea_trunc(44, artist), uea_trunc(44, title)
            art, tit = uea_rpad(44, art), uea_rpad(44, tit)
            fmtrow = "%s %-6s %-9s %s %s %-9s %-7s%s\n"
            if not song or song != songs[n]:
                out += (fmtrow % (col, str(n + 1), size,
                                  art, tit, duration[:8], bitrate[:6], Color.white))
            else:
                out += (fmtrow % (Color.pink, str(n + 1), size,
                                  art, tit, duration[:8], bitrate[:6], Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
    elif config.SOURCE == "mp3download":
        fmtrow = "%s %-6s %-9s %-88s %-9s%s\n"
        head = (Color.underline, "Item", "Size", "Track", "Length", Color.white)
        out = "\n" + fmtrow % head
        for number, x in enumerate(songs):
            col = (Color.red if number % 2 == 0 else Color.pink) if not song else Color.blue
            track = x.track
            size = x.size
            duration = x.duration
            if not song or song != songs[number]:
                out += (fmtrow % (col, str(number + 1), size, track, duration, Color.white))
            else:
                out += (fmtrow % (Color.pink, str(number + 1), size, track, duration, Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
        return

def top(period):
    if period == "deezer" or period == "d":
        session.message = ("%sTop tracks from Deezer%s" % (Color.yellow, Color.white))
        session.search = Search("charts", "deezer")
    else:
        original_period = period
        period = period or "w"
        periods = "_ w 3m 6m year all".split()
        period = periods.index(period)
        tps = "past week,past 3 months,past 6 months,past year,all time".split(",")
        session.message = ("%sTop tracks for %s%s" % (Color.yellow, tps[period - 1], Color.white))
        session.search = Search("charts", original_period)
    session.search.do()
    session.content = generate_songlist_display()

def search(term):
    """ Perform search. """
    session.search = Search("search", term)
    show_term = term.replace(" +tous", "")
    session.message = "Rercherche de '%s%s%s'" % (Color.yellow, show_term, Color.white)
    session.output()
    if session.search.do():
        session.message = "Résultats de la recherche pour %s%s%s" % (Color.yellow, show_term, Color.white)
        session.content = generate_songlist_display()
    else:
        session.message = "Rien trouvé pour %s%s%s" % (Color.yellow, show_term, Color.white)

def download(num):
    """ Download a track. """
    song = (session.songlist.songs[int(num) - 1])
    download = song.download()
    try:
        download.start()
        session.message = ("Downloading %s%s%s ...\n" % (Color.green, song.filename, Color.white))
        session.output()
        status_string = ('  {0}{1:,}{2} Bytes [{0}{3:.2%}{2}] received. Rate: '
                     '[{0}{4:4.0f} kbps{2}].  ETA: [{0}{5:.0f} secs{2}]')
        while True:
            if not download.get():
                break
            stats = (Color.yellow, download.bytesdone, Color.white, download.bytesdone * 1.0 / download.total, download.rate, download.eta)
            status = status_string.format(*stats)
            sys.stdout.write("\r" + status + ' ' * 4 + "\r")
            sys.stdout.flush()
        session.message = "Downloaded " + Color.green + song.filename + Color.white
    except IndexError:
        session.message = Color.red + "Invalid index" + Color.white
    except KeyboardInterrupt:
        session.message = Color.red + "Download halted" + Color.white
        try:
            os.remove(filename)
        except IOError:
            pass
    finally:        
        session.content = "\n"

def show_help(helpname=None):
    """ Print help message. """
    print(HELP)

def quits():
    """ Exit the program. """
    sys.exit()

def prompt_for_exit():
    """ Ask for exit confirmation. """
    session.message = Color.red + "Press ctrl-c again to exit" + Color.white
    session.content = generate_songlist_display()
    session.output()
    try:
        userinput = compat_input(Color.red + " > " + Color.white)
    except (KeyboardInterrupt, EOFError):
        quits()
    return userinput

def nextprev(np):
    """ Get next / previous search results. """
    if np == "n":
        if session.search.next():
            session.message += " : page %s" % session.search.page
        else:
            session.message = "No more songs to display"
    if np == "p":
        if session.search.prev():
            session.message += " : page %s" % session.search.page
        else:
            session.message = "No previous songs to display"
    session.content = generate_songlist_display()

def showconfig(_):
    """ Dump config data. """
    s = "  %s%-17s%s : \"%s\"\n"
    out = "  %s%-17s   %s%s%s\n" % (Color.underline, "Option", "Valeur", " " * 40, Color.white)
    for key, value in config.getitem().items():
        out += s % (Color.green, key.lower(), Color.white, value)
    session.content = out
    session.message = "Entrer %sc <option> <valeur>%s pour modifier" % (Color.green, Color.white)

def setconfig(key, val):
    """ Set configuration variable. """
    success_msg = fail_msg = ""
    key = key.upper()
    if key == "DLDIR":
        valid = os.path.exists(val) and os.path.isdir(val)
        if valid:
            new_config = config.getitem()
            setattr(config, key, val)
            success_msg = "Downloads will be saved to %s%s%s" % (Color.yellow, val, Color.white)
        else:
            fail_msg = "Invalid path: %s%s%s" % (Color.red, val, Color.white)
    elif key == "SOURCE":
        if val == "pleer" or val == "mp3download":
            new_config = config.getitem()
            setattr(config, key, val)
            success_msg = "Search source is now %s%s%s" % (Color.yellow, val, Color.white)
        else:
            fail_msg = "Invalid source: %s%s%s" % (Color.red, val, Color.white)
    else:
        fail_msg = "Unknown config item: %s%s%s" % (Color.red, key, Color.white)
    showconfig(1)
    if success_msg:
        config.save()
        session.message = success_msg
    elif fail_msg:
        session.message = fail_msg

def main():
    """ Main control loop. """
    session.message = "Rechercher la musique que vous voulez " + Color.blue + "- [h]elp, [t]op, [c]config, [q]uit" + Color.white
    session.output()
    # input types
    regx = {
        'show_help': r'(h|\?)$',
        'search': r'([a-zA-Z]\w.{0,500})',
        'download': r'(\d{1,2})$',
        'nextprev': r'(n|p)$',
        'top': r't\s*(|3m|6m|year|all|deezer|d)\s*$',
        'showconfig': r'(c)$',
        'setconfig': r'c\s*(\w+)\s*"?([^"]*)"?\s*$',
        'quits': r'q$',
    }
    # compile regexp's
    regx = {name: re.compile(val, re.UNICODE) for name, val in regx.items()}
    prompt = Color.blue + "dlmp3" + Color.white + " > "
    while True:
        try:
            # get user input
            userinput = compat_input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            userinput = prompt_for_exit()
        for k, v in regx.items():
            if v.match(userinput):
                func, matches = k, v.match(userinput).groups()
                try:
                    globals()[func](*matches)
                except IndexError:
                    session.message = Color.red + "Item invalide" + Color.white
                break
        else:
            if userinput:
                session.message = Color.blue + "Saisie incorrecte. Entrer ? pour l'aide" + Color.white
        session.output()
