# -*- coding:utf-8 -*-

import unicodedata
import time
import sys
import re
import os

# Python 3 compatibility hack
if sys.version_info[:2] >= (3, 0):
    # pylint: disable=E0611,F0401
    py2utf8_encode = lambda x: x
    py2utf8_decode = lambda x: x
    compat_input = input
else:
    py2utf8_encode = lambda x: x.encode("utf8") if type(x) == unicode else x
    py2utf8_decode = lambda x: x.decode("utf8") if type(x) == str else x
    compat_input = raw_input

from dlmp3 import application, config
import searcher


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

{0}Téléchargement{1}
Quand une liste de musiques est affiché à l'écran, entrer le numéro
de la chanson correspondante pour la télécharger.

{0}Top{1}
Entrer {2}t{1} ({2}+ 3m{1}, {2}6m{1}, {2}year{1}, {2}all{1}) pour afficher le top charts associé.
Defaut : Semaine
{2}3m{1} : 3 mois
{2}6m{1} : 6 mois
{2}year{1} : annuel
{2}all{1} : de tout les temps

{0}configuration{1}
Entrer {2}c{1} pour afficher la configuration.

{0}Quitter{1}
Entrer {2}q{1} pour quitter.
""".format(Color.underline, Color.white, Color.green, Color.red)

def xprint(stuff):
    """ Compatible print. """
    print(xenc(stuff))

def xenc(stuff):
    """ Encode for non utf8 environments and python 2. """
    # stuff = non_utf8_encode(stuff)
    stuff = py2utf8_encode(stuff)
    return stuff

def screen_update():
    """ Display content, show message, blank screen."""
    if application.content:
        xprint(application.content)
    if application.message:
        xprint(application.message)
    application.message = application.content = ""

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
    songs = application.songlist or []
    import pdb
    pdb.set_trace()
    if not songs:
        return
    if config.SOURCE == "pleer":
        fmtrow = "%s %-6s %-9s %-44s %-44s %-9s %-7s%s\n"
        head = (Color.underline, "Item", "Size", "Artist", "Track", "Length", "Bitrate", Color.white)
        out = "\n" + fmtrow % head
        for n, x in enumerate(songs):
            col = (Color.red if n % 2 == 0 else Color.pink) if not song else Color.blue
            size = x.get('size') or 0
            title = x.get('song') or "unknown title"
            artist = x.get('singer') or "unknown artist"
            bitrate = x.get('listrate') or "unknown"
            duration = x.get('duration') or "unknown length"
            art, tit = uea_trunc(44, artist), uea_trunc(44, title)
            art, tit = uea_rpad(44, art), uea_rpad(44, tit)
            fmtrow = "%s %-6s %-9s %s %s %-9s %-7s%s\n"
            size = str(size)[:3]
            size = size[0:2] + " " if size[2] == "." else size
            if not song or song != songs[n]:
                out += (fmtrow % (col, str(n + 1), size + " Mb",
                                  art, tit, duration[:8], bitrate[:6], Color.white))
            else:
                out += (fmtrow % (Color.pink, str(n + 1), size + " Mb",
                                  art, tit, duration[:8], bitrate[:6], Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
    elif config.SOURCE == "deezer":
        fmtrow = "%s %-6s%-44s %-44s%s\n"
        head = (Color.underline, "Item", "Artist", "Track", Color.white)
        out = "\n" + fmtrow % head
        for number, x in enumerate(songs):
            col = (Color.red if number % 2 == 0 else Color.pink) if not song else Color.blue
            title = x['title'] or "unknown title"
            artist = x['artist']['name'] or "unknown artist"
            if not song or song != songs[number]:
                out += (fmtrow % (col, str(number + 1), artist, title, Color.white))
            else:
                out += (fmtrow % (Color.pink, str(number + 1), artist, title, Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
    elif config.SOURCE == "mp3download":
        fmtrow = "%s %-6s %-9s %-88s %-9s%s\n"
        head = (Color.underline, "Item", "Size", "Track", "Length", Color.white)
        out = "\n" + fmtrow % head
        for number, x in enumerate(songs):
            col = (Color.red if number % 2 == 0 else Color.pink) if not song else Color.blue
            track = x[0]
            size = x[3] + " " + x[4]
            duration = x[2]
            if not song or song != songs[number]:
                out += (fmtrow % (col, str(number + 1), size, track, duration, Color.white))
            else:
                out += (fmtrow % (Color.pink, str(number + 1), size, track, duration, Color.white))
        return out + "\n" * (5 - len(songs)) if not song else out
        return

def show_message(message, col=Color.red, update=False):
    """ Show message using col, update screen if required. """
    application.content = generate_songlist_display()
    application.message = col + message + Color.white
    if update:
        screen_update()

def top(period, page=1):
    if period == "deezer" or period == "d":
        msg = ("%sTop tracks from Deezer%s" % (Color.yellow, Color.white))
        application.message = msg
        searcher.deezer()
        application.content = generate_songlist_display()
    else:
        original_period = period
        period = period or "w"
        periods = "_ w 3m 6m year all".split()
        period = periods.index(period)
        tps = "past week,past 3 months,past 6 months,past year,all time".split(",")
        msg = ("%sTop tracks for %s%s" % (Color.yellow, tps[period - 1], Color.white))
        application.message = msg
        searcher.get_top(original_period, page)
        application.content = generate_songlist_display()

def search(term, page=1):
    """ Perform search. """
    show_term = term.replace(" +tous", "")
    application.message = "Rercherche de '%s%s%s'" % (Color.yellow, show_term, Color.white)
    screen_update()
    songs = searcher.do_search(term, config.SOURCE, page)
    if songs:
        application.message = "Résultats de la recherche pour %s%s%s" % (Color.yellow, show_term, Color.white)
        application.content = generate_songlist_display()
    else:
        application.message = "Rien trouvé pour %s%s%s" % (Color.yellow, show_term, Color.white)

def downloading(song, filename):
    """ Download file, show status, return filename. """
    if config.SOURCE == "pleer":
        xprint("Downloading %s%s%s ..\n" % (Color.green, filename, Color.white))
        status_string = ('  {0}{1:,}{2} Bytes [{0}{3:.2%}{2}] received. Rate: '
                     '[{0}{4:4.0f} kbps{2}].  ETA: [{0}{5:.0f} secs{2}]')
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
            stats = (Color.yellow, bytesdone, Color.white, bytesdone * 1.0 / total, rate, eta)
            if not chunk:
                outfh.close()
                break
            status = status_string.format(*stats)
            sys.stdout.write("\r" + status + ' ' * 4 + "\r")
            sys.stdout.flush()
        return filename
    else:
        resp = searcher.urlopener(song[1])
        outfh = open(filename, 'wb')
        chunksize = 16384
        while True:
            chunk = resp.read(chunksize)
            outfh.write(chunk)  
            if not chunk:
                outfh.close()
                break
        return filename              

def download(num):
    """ Download a track. """
    song = (application.songlist[int(num) - 1])
    filename = searcher.make_filename(song)
    try:
        f = downloading(song, filename)
        application.message = "Downloaded " + Color.green + f + Color.white
    except IndexError:
        application.message = Color.red + "Invalid index" + Color.white
    except KeyboardInterrupt:
        application.message = Color.red + "Download halted!" + Color.white
        try:
            os.remove(filename)
        except IOError:
            pass
    finally:
        application.content = "\n"

def show_help(helpname=None):
    """ Print help message. """
    print(HELP)

def quits(showlogo=True):
    """ Exit the program. """
    sys.exit()

def prompt_for_exit():
    """ Ask for exit confirmation. """
    application.message = Color.red + "Press ctrl-c again to exit" + Color.white
    application.content = generate_songlist_display()
    screen_update()
    try:
        userinput = compat_input(Color.red + " > " + Color.white)
    except (KeyboardInterrupt, EOFError):
        quits(showlogo=False)
    return userinput

def nextprev(np):
    """ Get next / previous search results. """
    if np == "n":
        if len(application.songlist) == 20 and application.last_search_query:
            application.current_page += 1
            search(application.last_search_query, application.current_page)
            application.message += " : page %s" % application.current_page
        else:
            application.message = "No more songs to display"
    elif np == "p":
        if application.current_page > 1 and application.last_search_query:
            application.current_page -= 1
            search(application.last_search_query, application.current_page)
            application.message += " : page %s" % application.current_page
        else:
            application.message = "No previous songs to display"
    application.content = generate_songlist_display()

def showconfig(_):
    """ Dump config data. """
    s = "  %s%-17s%s : \"%s\"\n"
    out = "  %s%-17s   %s%s%s\n" % (Color.underline, "Option", "Valeur", " " * 40, Color.white)
    for key, value in config.getitem().items():
        out += s % (Color.green, key.lower(), Color.white, value)
    application.content = out
    application.message = "Entrer %sc <option> <valeur>%s pour modifier" % (Color.green, Color.white)

def setconfig(key, val):
    """ Set configuration variable. """
    # pylint: disable=R0912
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
        application.message = success_msg
    elif fail_msg:
        application.message = fail_msg

def main():
    """ Main control loop. """
    if os.path.exists(config.CFFILE):
        config.load(config.CFFILE)
    application.message = "Rechercher la musique que vous voulez " + Color.blue + "- [h]elp, [t]op, [c]config, [q]uit" + Color.white
    screen_update()
    # input types
    regx = {
        'show_help': r'h$',
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
                    application.message = Color.red + "Invalid item / range entered!" + Color.white
                break
        else:
            if userinput:
                application.message = Color.blue + "Bad syntax. Enter h for help" + Color.white
        screen_update()
