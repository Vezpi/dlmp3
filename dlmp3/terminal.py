# -*- coding:utf-8 -*-

import unicodedata
import sys
import re
from dlmp3 import config, session
from searcher import Search, Download


class Color(object):
    """ Class for holding colour code values. """
    white = "\x1b[%sm" % 0
    underline = "\x1b[%sm" * 3 % (2, 4, 33)
    cols = ["\x1b[%sm" % n for n in range(90, 96)]
    gray, red, green, yellow, blue, pink = cols
    if not config.COLOURS:
        ul = gray = red = green = yellow = blue = pink = white = ""


def display():
    """ Display the messages on the terminal screen. """
    if session.content:
        print(session.content)
    if session.message:
        print(session.message)
    session.message = session.content = ""

def songlist_display():
    """ Generate list of choices from a song list."""
    songs = session.songlist.songs
    head = [Color.underline, "Item"]
    fmtrow = "%s  %-5s"
    for item in session.songlist.categories:
        head.append(item[0].title())
        fmtrow = fmtrow + " %-" + item[1] + "s"
    fmtrow = fmtrow + "\n"
    head = tuple(head)
    out = fmtrow % head
    for number, song in enumerate(songs):
        color = (Color.white if number % 2 == 0 else Color.gray)
        body = [color, str(number + 1)]
        if song.track:
            body.append(song.track[:97])
        if song.artist:
            body.append(song.artist[:47])
        if song.title:
            body.append(song.title[:47])
        if song.size:
            body.append(song.size[:9])
        if song.length:
            body.append(song.length[:8])
        if song.bitrate:
            body.append(song.bitrate[:7])
        body = tuple(body)
        out += (fmtrow % body)
    session.content = out[:(len(out)-1)] + Color.white

def top(period):
    session.search = Search("charts", config)
    if period == "deezer" or period == "d":
        session.search.source = "deezer"
        session.message = ("%sTop tracks from Deezer%s" % (Color.green, Color.white))
    else:
        session.search.period = period
        period = period or "w"
        periods = "_ w 3m 6m year all".split()
        period = periods.index(period)
        tps = "past week,past 3 months,past 6 months,past year,all time".split(",")
        session.message = ("%sTop tracks for %s%s" % (Color.green, tps[period - 1], Color.white))
    if session.search.do():
        songlist_display()

def search(term):
    """ Perform search. """
    session.search = Search("search", config, term)
    term = term.replace(" +tous", "")
    session.message = "Searching for %s%s%s ..." % (Color.green, term, Color.white)
    display()
    try:
        if session.search.do():
            session.message = session.search.last_search_query = "Results for %s%s%s" % (Color.green, term, Color.white)
            # session.search.last_search_query = session.message
            songlist_display()
        else:
            session.message = "Nothing found for %s%s%s" % (Color.green, term, Color.white)
    except KeyboardInterrupt:
        session.message = Color.red + "\nCanceled" + Color.white        

def download(num):
    """ Download a track. """
    song = (session.songlist.songs[int(num) - 1])
    download = Download(song)
    try:
        if not download.start(config, session.search):
            session.message = Color.red + "This track is not available from here" + Color.white
            display()
            return
        else:
            session.message = ("Downloading %s%s%s ...\n" % (Color.green, song.filename, Color.white))
            display()
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
        song.remove_filename()

def show_help():
    """ Print help message. """
    help = """
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
    print(help)

def quits():
    """ Exit the program. """
    sys.exit()

def nextprev(np):
    """ Get next / previous search results. """
    if session.search:
        if np == "n":
            if session.search.next():
                session.message = session.search.last_search_query + " : page %s%s%s" % (Color.green, session.search.page, Color.white)
                songlist_display()
            else:
                session.message = "No more songs to display"
        if np == "p":
            if session.search.prev():
                session.message = session.search.last_search_query + " : page %s%s%s" % (Color.green, session.search.page, Color.white)
                songlist_display()
            else:
                session.message = "No previous songs to display"
    else:
        session.message = "Do a search first"
    
def showconfig():
    """ Dump config data. """
    s = "  %s%-17s%s : \"%s\"\n"
    out = "  %s%-17s   %s%s%s\n" % (Color.underline, "Option", "Value", " " * 40, Color.white)
    for key, value in config.getitem().items():
        out += s % (Color.green, key.lower(), Color.white, value)
    session.content = out[:(len(out)-1)]
    session.message = "Enter %sc <option> <value>%s for change" % (Color.yellow, Color.white)

def setconfig(key, val):
    """ Set configuration variable. """
    key = key.upper()
    if key == "DLDIR":
        success_msg = "Downloads will be saved to %s%s%s" % (Color.green, val, Color.white)
        fail_msg = "Invalid path: %s%s%s" % (Color.red, val, Color.white)
    elif key == "SOURCE":
        success_msg = "Search source is now %s%s%s" % (Color.green, val, Color.white)
        fail_msg = "Invalid source: %s%s%s" % (Color.red, val, Color.white)
    else:
        fail_msg = "Unknown config item: %s%s%s" % (Color.red, key, Color.white)
    if config.set(key, val):
        config.save()
        showconfig()
        session.message = success_msg
    else:
        session.message = fail_msg
    display()

def main():
    """ Main control loop. """
    session.message = "Search for music" + Color.blue + " - [h]elp, [t]op, [c]config, [q]uit" + Color.white
    display()
    # input types
    regx = {
        'show_help': r'h|\?$',
        'search': r'([a-zA-Z]\w.{0,500})',
        'download': r'(\d{1,2})$',
        'nextprev': r'(n|p)$',
        'top': r't\s*(|3m|6m|year|all|deezer|d)\s*$',
        'showconfig': r'c$',
        'setconfig': r'c\s*(\w+)\s*"?([^"]*)"?\s*$',
        'quits': r'q$',
    }
    # compile regexp's
    regx = {name: re.compile(val, re.UNICODE) for name, val in regx.items()}
    prompt = Color.blue + "dlmp3" + Color.white + " > "
    while True:
        try:
            userinput = raw_input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("")
            quits()
        for k, v in regx.items():
            if v.match(userinput):
                func, matches = k, v.match(userinput).groups()
                try:
                    globals()[func](*matches)
                except IndexError:
                    session.message = Color.red + "Invalid item" + Color.white
                break
        else:
            if userinput:
                session.message = Color.red + "Wrong syntax : ? for help" + Color.white
        display()
