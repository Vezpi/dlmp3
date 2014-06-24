#!/usr/bin/env python
# coding: utf-8
"""
mps.

https://github.com/np1/mps

Copyright (C)  2013-2014 nagev

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from __future__ import print_function

__version__ = "0.20.14"
__author__ = "nagev"
__license__ = "GPLv3"

import xml.etree.ElementTree as ET
import unicodedata
import subprocess
import tempfile
import logging
import hashlib
import difflib
import random
import socket
import zlib
import time
import math
import json
import sys
import re
import os

try:
    # pylint: disable=F0401
    from colorama import init as init_colorama, Fore, Style
    has_colorama = True

except ImportError:
    has_colorama = False


# Python 3 compatibility hack

if sys.version_info[:2] >= (3, 0):
    # pylint: disable=E0611,F0401
    import pickle
    from urllib.request import build_opener
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    py2utf8_encode = lambda x: x
    py2utf8_decode = lambda x: x
    compat_input = input

else:
    from urllib2 import build_opener, HTTPError, URLError
    from urllib import urlencode
    import cPickle as pickle
    py2utf8_encode = lambda x: x.encode("utf8") if type(x) == unicode else x
    py2utf8_decode = lambda x: x.decode("utf8") if type(x) == str else x
    compat_input = raw_input

# mswin = os.name == "nt"
# non_utf8 = mswin or not "UTF-8" in os.environ.get("LANG", "")
non_utf8 = not "UTF-8" in os.environ.get("LANG", "")

member_var = lambda x: not(x.startswith("__") or callable(x))
zcomp = lambda v: zlib.compress(pickle.dumps(v, protocol=2), 9)
zdecomp = lambda v: pickle.loads(zlib.decompress(v))


def get_default_ddir():
    """ Get system default Download directory, append mps dir. """

    join, user = os.path.join, os.path.expanduser("~")

    # if mswin:
    #     #return os.path.join(os.path.expanduser("~"), "Downloads", "mps")
    #     return join(user, "Downloads", "pms")

    USER_DIRS = join(user, ".config", "user-dirs.dirs")
    DOWNLOAD_HOME = join(user, "Downloads")

    if 'XDG_DOWNLOAD_DIR' in os.environ:
        ddir = os.environ['XDG_DOWNLOAD_DIR']

    elif os.path.exists(USER_DIRS):
        lines = open(USER_DIRS).readlines()
        defn = [x for x in lines if x.startswith("XDG_DOWNLOAD_DIR")]

        if len(defn) == 0:
            ddir = user

        else:
            ddir = defn[0].split("=")[1]\
                .replace('"', '')\
                .replace("$HOME", user).strip()

    elif os.path.exists(DOWNLOAD_HOME):
        ddir = DOWNLOAD_HOME
    else:
        ddir = user

    ddir = py2utf8_decode(ddir)
    return join(ddir, "mps")


def get_config_dir():
    """ Get user configuration directory.  Create if needed. """

    # if mswin:
    #     # AppData\Roaming on Windows 7
    #     confd = os.environ["APPDATA"]
    # else:
    # if "XDG_CONFIG_HOME" in os.environ:
    #     confd = os.environ["XDG_CONFIG_HOME"]
    # else:
    #     confd = os.path.join(os.environ["HOME"], ".config")

    # oldd = os.path.join(confd, "pms")
    mpsd = "/etc/dlmp3"

    # if os.path.exists(oldd) and not os.path.exists(mpsd):
    #     os.rename(oldd, mpsd)

    if not os.path.exists(mpsd):
        os.makedirs(mpsd)

    return mpsd


class Config(object):

    """ Holds various configuration values. """

    # PLAYER = "mplayer"
    # PLAYERARGS = "-nolirc -prefer-ipv4"
    # COLOURS = False if mswin and not has_colorama else True
    COLOURS = True
    # CHECKUPDATE = True
    # SHOW_MPLAYER_KEYS = True
    DDIR = get_default_ddir()


if os.environ.get("mpsdebug") == '1':

    logfile = os.path.join(tempfile.gettempdir(), "mps.log")
    logging.basicConfig(level=logging.DEBUG, filename=logfile)

dbg = logging.debug

try:
    import readline
    readline.set_history_length(2000)
    has_readline = True

except ImportError:
    has_readline = False

opener = build_opener()
ua = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"
opener.addheaders = [("User-Agent", ua)]
urlopen = opener.open


class Memo(object):

    """ Memo handling and creation. """

    def __init__(self, filepath, life=60 * 60 * 24 * 3):
        self.life = life
        self.filepath = filepath
        self.data = {}

        if os.path.isfile(filepath):

            try:

                with open(filepath, "rb") as f:
                    self.data = pickle.load(f)
                    dbg("cache opened, %s items", len(self.data))

            except (EOFError, IOError) as e:
                dbg(str(e))

        else:
            dbg("No cache found!")

        self.prune()

    def add(self, key, val, lifespan=None):
        """ Add key value pair, expire in lifespan seconds. """

        key = key.encode("utf8")
        key = hashlib.sha1(key).hexdigest()
        lifespan = self.life if not lifespan else lifespan
        expiry_time = int(time.time()) + lifespan
        self.data[key] = dict(expire=expiry_time, data=zcomp(val))
        dbg("cache item added: %s", key)

    def get(self, key):
        """ Fetch a value if it exists and is fresh. """

        now = int(time.time())
        key = key.encode("utf8")
        key = hashlib.sha1(key).hexdigest()

        if key in self.data:

            if self.data[key]['expire'] > now:
                dbg("cache hit %s", key)
                return zdecomp(self.data[key]['data'])

            else:
                del self.data[key]
                return None

        return None

    def prune(self):
        """ Remove stale items. """

        now = int(time.time())
        dbg("Pruning: ")
        stalekeys = [x for x in self.data if self.data[x]['expire'] < now]
        dbg("%s stale keys; %s total kys", len(stalekeys), len(self.data))

        for x in stalekeys:
            del self.data[x]

    def save(self):
        """ Save memo file to persistent storage. """

        self.prune()

        with open(self.filepath, "wb") as f:
            pickle.dump(self.data, f, protocol=2)


class Playlist(object):

    """ Representation of a playist, has list of songs. """

    def __init__(self, name=None, songs=None):
        self.name = name
        self.creation = time.time()
        self.songs = songs or []

    @property
    def is_empty(self):
        """ Return True / False if songs are populated or not. """

        return bool(not self.songs)

    @property
    def size(self):
        """ Return number of tracks. """

        return len(self.songs)

    @property
    def duration(self):
        """ Sum duration of the playlist. """

        duration = 0

        for song in self.songs:
            duration += int(song['Rduration'])

        duration = time.strftime('%H:%M:%S', time.gmtime(int(duration)))
        return duration


class g(object):

    """ Class for holding globals that are needed throught the module. """

    album_tracks_bitrate = 320
    model = Playlist(name="model")
    last_search_query = ""
    current_page = 1
    active = Playlist(name="active")
    noblank = False
    text = {}
    userpl = {}
    last_opened = message = content = ""
    config = [x for x in sorted(dir(Config)) if member_var(x)]
    configbool = [x for x in config if type(getattr(Config, x)) is bool]
    defaults = {setting: getattr(Config, setting) for setting in config}
    CFFILE = os.path.join(get_config_dir(), "config")
    PLFILE = os.path.join(get_config_dir(), "playlist")
    memo = Memo(os.path.join(get_config_dir(), "cache" + sys.version[0:5]))
    OLD_CFFILE = os.path.join(os.path.expanduser("~"), ".pms-config")
    OLD_PLFILE = os.path.join(os.path.expanduser("~"), ".pms-playlist")
    READLINE_FILE = None


def showconfig(_):
    """ Dump config data. """

    s = "  %s%-17s%s : \"%s\"\n"
    out = "  %s%-17s   %s%s%s\n" % (c.ul, "Option", "Valeur", " " * 40, c.w)

    for setting in g.config:
        out += s % (c.g, setting.lower(), c.w, getattr(Config, setting))

    g.content = out
    g.message = "Entrer %sc <option> <valeur>%s pour modifier" % (c.g, c.w)


def saveconfig():
    """ Save current config to file. """

    config = {setting: getattr(Config, setting) for setting in g.config}
    pickle.dump(config, open(g.CFFILE, "wb"), protocol=2)


def clearcache():
    """ Clear the cache. """
    g.memo.data = {}
    g.memo.save()
    g.content = generate_songlist_display()
    g.message = c.r + "Cache cleared!" + c.w


# override config if config file exists
def loadconfig(pfile):
    """ Load config from file. """

    saved_config = pickle.load(open(pfile, "rb"))
    for kk, vv in saved_config.items():
        setattr(Config, kk, vv)

# Account for old versions
if os.path.exists(g.CFFILE):
    loadconfig(g.CFFILE)

elif os.path.exists(g.OLD_CFFILE):
    loadconfig(g.OLD_CFFILE)
    saveconfig()
    os.remove(g.OLD_CFFILE)

if has_readline:
    g.READLINE_FILE = os.path.join(get_config_dir(), "input_history")

    if os.path.exists(g.READLINE_FILE):
        readline.read_history_file(g.READLINE_FILE)


class c(object):

    """ Class for holding colour code values. """

    # if mswin and has_colorama:
    #     white = Style.RESET_ALL
    #     ul = Style.DIM + Fore.YELLOW
    #     red, green, yellow = Fore.RED, Fore.GREEN, Fore.YELLOW
    #     blue, pink = Fore.CYAN, Fore.MAGENTA

    # elif mswin:
    #     Config.COLOURS = False

    # else:
    white = "\x1b[%sm" % 0
    ul = "\x1b[%sm" * 3 % (2, 4, 33)
    cols = ["\x1b[%sm" % n for n in range(91, 96)]
    red, green, yellow, blue, pink = cols

    if not Config.COLOURS:
        ul = red = green = yellow = blue = pink = white = ""
    r, g, y, b, p, w = red, green, yellow, blue, pink, white


def setconfig(key, val):
    """ Set configuration variable. """

    # pylint: disable=R0912
    success_msg = fail_msg = ""
    key = key.upper()

    if key == "ALL" and val.upper() == "DEFAULT":

        for k, v in g.defaults.items():
            setattr(Config, k, v)
            success_msg = "Default configuration reinstated"

    elif key == "DDIR" and not val.upper() == "DEFAULT":

        valid = os.path.exists(val) and os.path.isdir(val)

        if valid:
            setattr(Config, key, val)
            success_msg = "Downloads will be saved to %s%s%s" % (c.y, val, c.w)

        else:
            fail_msg = "Invalid path: %s%s%s" % (c.r, val, c.w)

    elif key in g.configbool and not val.upper() == "DEFAULT":

        if val.upper() in "0 FALSE OFF NO".split():
            setattr(Config, key, False)
            success_msg = "%s set to disabled (restart may be required)" % key

        # elif key == "COLOURS" and mswin and not has_colorama:
        #     fail_msg = "Can't enable colours, colorama not found"

        else:
            setattr(Config, key, True)
            success_msg = "%s set to enabled (restart may be required)" % key

    elif key in g.config:

        if val.upper() == "DEFAULT":
            val = g.defaults[key]

        setattr(Config, key, val)
        success_msg = "%s has been set to %s" % (key.upper(), val)

    else:
        fail_msg = "Unknown config item: %s%s%s" % (c.r, key, c.w)

    showconfig(1)

    if success_msg:
        saveconfig()
        g.message = success_msg

    elif fail_msg:
        g.message = fail_msg

# "[h]elp, [a]lbum, [t]op, [c]config, [q]uit"
HELP = """
{0}Rercherche{1}
Entrer le nom d'un artiste, le nom d'une chanson, les deux ensemble,
ou simplement des mots clés pour la recherche.
Si la recherche ne retourne pas ce que vous voulez, ajouter +tous
pour rechercher toutes les qualités de son

{0}Rercherche d'album{1}
Entrer "a" + le nom d'un album pour le rechercher.

{0}Téléchargement{1}
Quand une liste de musiques est affiché à l'écran, entrer le numéro
de la chanson correspondante pour la télécharger.

{0}Top{1}
Entrer "t" (+ 3m, 6m, year, all) pour afficher le top charts associé.
Defaut : Semaine
3m : 3 mois
6m : 6 mois
year : annuel
all : de tout les temps

{0}Configuration{1}
Entrer "c" pour afficher la configuration.

{0}Quitter{1}
Entrer "q" pour quitter.
""".format(c.ul, c.w, c.g, c.r)


def F(key, nb=0, na=0, percent=r"\*", nums=r"\*\*", textlib=None):
    """Format text.

    nb, na indicate newlines before and after to return
    percent is the delimter for %s
    nums is the delimiter for the str.format command (**1 will become {1})
    textlib is the dictionary to use (defaults to g.text if not given)

    """

    textlib = textlib or g.text

    assert key in textlib
    text = textlib[key]
    percent_fmt = textlib.get(key + "_")
    number_fmt = textlib.get("_" + key)

    if number_fmt:
        text = re.sub(r"(%s(\d))" % nums, "{\\2}", text)
        text = text.format(*number_fmt)

    if percent_fmt:
        text = re.sub(r"%s" % percent, r"%s", text)
        text = text % percent_fmt

    text = re.sub(r"&&", r"%s", text)

    return "\n" * nb + text + c.w + "\n" * na

g.text = {
    "exitmsg": """\
**0mps - **1http://github.com/np1/mps**0
Released under the GPLv3 license
(c) 2013-2014 nagev**2\n""",
    "_exitmsg": (c.r, c.b, c.w),

    # Error / Warning messages

    'no playlists': "*No saved playlists found!*",
    'no playlists_': (c.r, c.w),
    'pl bad name': '*&&* is not valid a valid name. Ensure it starts with a '
    'letter or _',
    'pl bad name_': (c.r, c.w),
    'pl not found': 'Playlist *&&* unknown. Saved playlists are shown above',
    'pl not found_': (c.r, c.w),
    'pl not found advise ls': 'Playlist "*&&*" not found. Use *ls* to list',
    'pl not found advise ls_': (c.y, c.w, c.g, c.w),
    'pl empty': 'Playlist is empty!',
    'advise add': 'Use *add N* to add a track',
    'advise add_': (c.g, c.w),
    'advise search': 'Search for songs and then use *add* to add them',
    'advise search_': (c.g, c.w),
    'no data': 'Error fetching data. Perhaps http://pleer.com is down.\n*&&*',
    'no data_': (c.r, c.w),
    'use dot': 'Start your query with a *.* to perform a search',
    'use dot_': (c.g, c.w),
    'cant get track': 'Problem fetching this track: *&&*',
    'cant get track_': (c.r, c.w),
    'track unresolved': 'Sorry, this track is not available',
    'no player': '*&&* was not found on this system',
    'no player_': (c.y, c.w),
    'no pl match for rename': '*Couldn\'t find matching playlist to rename*',
    'no pl match for rename_': (c.r, c.w),
    'invalid range': "*Invalid item / range entered!*",
    'invalid range_': (c.r, c.w),

    # Info messages

    'pl renamed': 'Playlist *&&* renamed to *&&*',
    'pl renamed_': (c.y, c.w, c.y, c.w),
    'pl saved': 'Playlist saved as *&&*.  Use *ls* to list playlists',
    'pl saved_': (c.y, c.w, c.g, c.w),
    'pl loaded': 'Loaded playlist *&&* as current playlist',
    'pl loaded_': (c.y, c.w),
    'pl viewed': 'Showing playlist *&&*',
    'pl viewed_': (c.y, c.w),
    'pl help': 'Enter *open <name or ID>* to load a playlist',
    'pl help_': (c.g, c.w),
    'added to pl': '*&&* tracks added (*&&* total [*&&*]). Use *vp* to view',
    'added to pl_': (c.y, c.w, c.y, c.w, c.y, c.w, c.g, c.w),
    'added to saved pl': '*&&* tracks added to *&&* (*&&* total [*&&*])',
    'added to saved pl_': (c.y, c.w, c.y, c.w, c.y, c.w, c.y, c.w),
    'song move': 'Moved *&&* to position *&&*',
    'song move_': (c.y, c.w, c.y, c.w),
    'song sw': ("Switched track *&&* with *&&*"),
    'song sw_': (c.y, c.w, c.y, c.w),
    'current pl': "This is the current playlist. Use *save <name>* to save it",
    'current pl_': (c.g, c.w),
    'songs rm': '*&&* tracks removed &&',
    'songs rm_': (c.y, c.w)
}


# def save_to_file():
#     """ Save playlists.  Called each time a playlist is saved or deleted. """

#     f = open(g.PLFILE, "wb")
#     pickle.dump(g.userpl, f, protocol=2)


# def load_playlist(pfile):
#     """ Load pickled playlist file. """

#     try:
#         f = open(pfile, "rb")
#         g.userpl = pickle.load(f)

#     except IOError:
#         g.userpl = {}
#         save_to_file()


# def open_from_file():
#     """ Open playlists. Called once on script invocation. """

#     if os.path.exists(g.PLFILE):
#         load_playlist(g.PLFILE)

#     elif os.path.exists(g.OLD_PLFILE):
#         load_playlist(g.OLD_PLFILE)
#         save_to_file()
#         os.remove(g.OLD_PLFILE)

#     else:
#         g.userpl = {}
#         save_to_file()


# def logo(col=None, version=""):
#     """ Return text logo. """

#     LOGO = c.r +"SUPPRIME CETTE LIGNE"
#     return LOGO + c.w


def tidy(raw, field):
    """ Tidy HTML entities, format songlength if field is duration.  """

    if field == "duration":
        raw = time.strftime('%M:%S', time.gmtime(int(raw)))

    else:
        for r in (("&#039;", "'"), ("&amp;#039;", "'"), ("&amp;amp;", "&"),
                 ("  ", " "), ("&amp;", "&"), ("&quot;", '"')):
            raw = raw.replace(r[0], r[1])

    return raw


def get_average_bitrate(song):
    """ Calculate average bitrate of VBR tracks. """

    if song["rate"] == "VBR":
        vbrsize = float(song["Rsize"][:-3]) * 8192
        vbrlen = float(song["Rduration"])
        vbrabr = int(vbrsize / vbrlen)

        # fix some songs reporting large bitrates
        if vbrabr > 320:
            dbg("---- %s => bitrate: %s", song["song"], str(vbrabr))
            vbrabr = 320

        song["listrate"] = str(vbrabr) + " v"  # for display in list
        song["rate"] = str(vbrabr) + " Kb/s VBR"  # for playback display

    else:
        song["listrate"] = song["rate"][:3]  # not vbr list display

    return song


def get_tracks_from_page(page):
    """ Get search results from web page. """

    fields = "duration file_id singer song link rate size source".split()
    matches = re.findall(r"\<li.(duration[^>]+)\>", page)
    songs = []

    if matches:

        for song in matches:
            cursong = {}

            for f in fields:
                v = re.search(r'%s=\"([^"]+)"' % f, song)

                if v:
                    cursong[f] = tidy(v.group(1), f)
                    cursong["R" + f] = v.group(1)

                else:
                    cursong[f] = "unknown"
                    cursong["R" + f] = "unknown"
                    #raise Exception("problem with field " + f)

            cursong = get_average_bitrate(cursong)
            songs.append(cursong)

    else:
        dbg("got unexpected webpage or no search results")
        return False

    return songs


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

#    if not g.noblank:
#        print("\n")

    if g.content:
        xprint(g.content)

    if g.message:
        xprint(g.message)

    g.message = g.content = ""
    g.noblank = False



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

    songs = g.model.songs or []

    if not songs:
        return # logo(c.g) + "\n\n"

    fmtrow = "%s %-6s %-9s %-44s %-44s %-9s %-7s%s\n"
    head = (c.ul, "Item", "Size", "Artist", "Track", "Length", "Bitrate", c.w)
    out = "\n" + fmtrow % head

    for n, x in enumerate(songs):
        col = (c.r if n % 2 == 0 else c.p) if not song else c.b
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
                              art, tit, duration[:8], bitrate[:6], c.w))
        else:
            out += (fmtrow % (c.p, str(n + 1), size + " Mb",
                              art, tit, duration[:8], bitrate[:6], c.w))

    return out + "\n" * (5 - len(songs)) if not song else out


def get_stream(song, force=False):
    """ Return the url for a song. """

    if not "track_url" in song or force:
        url = 'http://pleer.com/site_api/files/get_url?action=download&id=%s'
        url = url % song['link']

        try:
            dbg("[0] fetching " + url)
            wdata = urlopen(url, timeout=7).read().decode("utf8")
            dbg("fetched " + url)

        except (HTTPError, socket.timeout):
            time.sleep(2)  # try again
            dbg("[1] fetching 2nd attempt ")
            wdata = urlopen(url, timeout=7).read().decode("utf8")
            dbg("fetched 2nd attempt" + url)

        j = json.loads(wdata)

        if not j.get("track_link"):
            raise URLError("This track is not accessible")

        track_url = j['track_link']
        return track_url

    else:
        return song['track_url']



def get_length(song):
    """ Return song length in seconds. """

    d = song['duration']
    return sum(int(x) * 60 ** n for n, x in enumerate(reversed(d.split(":"))))


def writestatus(text):
    """ Update status line. """

    spaces = 75 - len(text)
    sys.stdout.write(" " + text + (" " * spaces) + "\r")
    sys.stdout.flush()


def make_status_line(match_object, songlength=0, volume=None,
                     progress_bar_size=60):
    """ Format progress line output.  """

    try:
        elapsed_s = int(match_object.group('elapsed_s') or '0')

    except ValueError:
        return ""

    display_s = elapsed_s
    display_m = 0

    if elapsed_s >= 60:
        display_m = display_s // 60
        display_s %= 60

    pct = (float(elapsed_s) / songlength * 100) if songlength else 0

    status_line = "%02i:%02i %s" % (display_m, display_s,
                                    ("[%.0f%%]" % pct).ljust(6)
                                    )

    if volume:
        progress_bar_size -= 10
        vol_suffix = " vol: %d%%  " % volume

    else:
        vol_suffix = ""

    progress = int(math.ceil(pct / 100 * progress_bar_size))
    status_line += " [%s]" % ("=" * (progress - 1) +
                              ">").ljust(progress_bar_size)
    status_line += vol_suffix
    return status_line


def top(period, page=1):
    """ Get top music for period, returns songs list."""

    period = period or "w"
    periods = "_ w 3m 6m year all".split()
    period = periods.index(period)
    url = ("http://pleer.com/en/gettopperiod?target1=%s&target2=r1&select=e&"
           "page_ru=1&page_en=%s")
    url = url % ("e%s" % period, page)
    tps = "past week,past 3 months,past 6 months,past year,all time".split(",")
    msg = ("%sTop tracks for %s%s" % (c.y, tps[period - 1], c.w))
    g.message = msg
    dbg("[2] fetching " + url)

    try:
        wdata = urlopen(url).read().decode("utf8")

    except (URLError, HTTPError) as e:
        g.message = F('no data') % e
        # g.content = logo(c.r)
        return

    dbg("fetched " + url)
    match = re.search(r"<ol id=\"search-results\">[\w\W]+?<\/ol>", wdata)
    html_ol = match.group(0)
    g.model.songs = get_tracks_from_page(html_ol)
    g.content = generate_songlist_display()


def search(term, page=1, splash=True):
    """ Perform search. """

    if not term or len(term) < 2:
        g.message = c.r + "Not enough input" + c.w
        g.content = generate_songlist_display()

    # elif term == "albumsearch":
    #     return

    else:
        original_term = term
        url = "http://pleer.com/search"
        query = {"target": "tracks", "page": page}

        if not "+tous" in term:
            query["quality"] = "best"

        else:
            term = term.replace(" +tous", "")

        query["q"] = term
        g.message = "Rercherche de '%s%s%s'" % (c.y, term, c.w)
        query = [(k, query[k]) for k in sorted(query.keys())]
        url = "%s?%s" % (url, urlencode(query))

        if g.memo.get(url):
            songs = g.memo.get(url)

        else:
            if splash:
                screen_update()

            try:
                wdata = urlopen(url).read().decode("utf8")
                songs = get_tracks_from_page(wdata)

            except (URLError, HTTPError) as e:
                g.message = F('no data') % e
                # g.content = logo(c.r)
                return

            if songs:
                g.memo.add(url, songs)

        if songs:
            g.model.songs = songs
            g.message = "Résultats de la recherche pour %s%s%s" % (c.y, term, c.w)
            g.last_opened = ""
            g.last_search_query = original_term
            g.current_page = page
            g.content = generate_songlist_display()

        else:
            g.message = "Rien trouvé pour %s%s%s" % (c.y, term, c.w)
            # g.content = logo(c.r)
            g.current_page = 1
            g.last_search_query = ""


def show_message(message, col=c.r, update=False):
    """ Show message using col, update screen if required. """

    g.content = generate_songlist_display()
    g.message = col + message + c.w

    if update:
        screen_update()


def search_album(term, page=1, splash=True, bitrate=g.album_tracks_bitrate):
    """Search for albums. """

    #pylint: disable=R0914,R0912
    if not term:
        show_message("Enter album name:", c.g, update=True)
        term = compat_input("> ")

        if not term or len(term) < 2:
            g.message = c.r + "Not enough input!" + c.w
            g.content = generate_songlist_display()
            return

    album = _get_mb_album(term)

    if not album:
        show_message("Album '%s' not found!" % term)
        return

    out = "'%s' by %s%s%s\n\n" % (album['title'],
                                  c.g, album['artist'], c.w)
    out += ("[Enter] to continue, [q] to abort, or enter artist name for:\n"
            "    %s" % (c.y + term + c.w + "\n"))

    g.message = out
    screen_update()
    prompt = xenc("Artist? [%s] > " % album['artist'])
    artistentry = compat_input(prompt).strip()

    if artistentry:

        if artistentry == "q":
            show_message("Album search abandoned!")
            return

        album = _get_mb_album(term, artist=artistentry)

        if not album:
            show_message("Album '%s' by '%s' not found!" % (term, artistentry))
            return

    title, artist = album['title'], album['artist']
    mb_tracks = _get_mb_tracks(album['aid'])

    if not mb_tracks:
        show_message("Album '%s' by '%s' has 0 tracks!" % (title, artist))
        return

    msg = "%s%s%s by %s%s%s\n\n" % (c.g, title, c.w, c.g, artist, c.w)
    msg += "Specify bitrate to match or [q] to abort"
    g.message = msg
    g.content = "Tracks:\n"
    for n, track in enumerate(mb_tracks, 1):
        g.content += "%02s  %s" % (n, track['title'])
        g.content += "\n"

    #g.content = logo(c.b) + "\n\n"
    screen_update()
    bitrate = g.album_tracks_bitrate
    brentry = compat_input("Bitrate? [%s] > " % bitrate)

    if brentry.isdigit():
        bitrate = int(brentry)

    elif brentry == "":
        pass

    else:
        show_message("Album search abandoned!")
        return

    songs = []
    print("\n")
    itt = _match_tracks(artist, title, bitrate, mb_tracks)

    while True:

        try:
            songs.append(next(itt))

        except KeyboardInterrupt:
            print("%sHalted!%s" % (c.r, c.w))
            break

        except StopIteration:
            break

    if songs:
        print("\n%s / %s songs matched" % (len(songs), len(mb_tracks)))
        compat_input("Press Enter to continue")
        g.model.songs = songs
        g.message = "Contents of album %s%s - %s%s %s(%d/%d)%s:" % (
            c.y, artist, title, c.w, c.b, len(songs), len(mb_tracks), c.w)
        g.last_opened = ""
        g.last_search_query = ""
        g.current_page = page
        g.content = generate_songlist_display()

    else:
        g.message = "Found no album tracks for %s%s%s" % (c.y, title, c.w)
        g.content = generate_songlist_display()
        g.current_page = 1
        g.last_search_query = ""


def _match_tracks(artist, title, bitrate, mb_tracks):
    """ Match list of tracks in mb_tracks by performing multiple searches. """

    #pylint: disable=R0914
    title_artist_str = c.g + title + c.w, c.g + artist + c.w
    xprint("\nSearching for %s by %s" % title_artist_str)
    xprint("Attempting to match bitrate of %s kbps\n\n" % bitrate)
    url = "http://pleer.com/search"
    dtime = lambda x: time.strftime('%M:%S', time.gmtime(int(x)))

    # do matching
    for track in mb_tracks:
        ttitle = track['title']
        length = track['length']
        xprint("Search :  %s%s - %s%s - %s" % (c.y, artist, ttitle, c.w,
                                               dtime(length)))
        q = py2utf8_encode(artist) + " " + py2utf8_encode(ttitle)
        q = py2utf8_encode(ttitle) if artist == "Various Artists" else q
        query = {"target": "tracks", "page": 1, "q": q}
        wdata, fromcache = _do_query(url, query, err='album track error',
                                     report=True)
        results = get_tracks_from_page(wdata.decode("utf8")) if wdata else None

        if not fromcache:
            time.sleep(1.5)

        if not results:
            print(c.r + "Nothing matched :(\n" + c.w)
            continue

        s, score = _best_song_match(results, ttitle, length, bitrate)
        cc = c.g if score > 89 else c.y
        cc = c.r if score < 75 else cc
        xprint("Matched:  %s%s - %s%s - %s (%s kbps)\n[%sMatch confidence: "
               "%s%s]\n" % (c.y, s['singer'], s['song'], c.w, s['duration'],
                            s['listrate'], cc, score, c.w))
        yield s


def _get_mb_album(albumname, **kwa):
    """ Return artist, album title and track count from MusicBrainz. """

    url = "http://musicbrainz.org/ws/2/release/"
    qargs = dict(
        release='"%s"' % albumname,
        primarytype=kwa.get("primarytype", "album"),
        status=kwa.get("status", "official"))
    qargs.update({k: '"%s"' % v for k, v in kwa.items()})
    qargs = ["%s:%s" % item for item in qargs.items()]
    qargs = {"query": " AND ".join(qargs)}
    g.message = "Album search for '%s%s%s'" % (c.y, albumname, c.w)
    wdata = _do_query(url, qargs)

    if not wdata:
        return None

    ns = {'mb': 'http://musicbrainz.org/ns/mmd-2.0#'}
    root = ET.fromstring(wdata)
    rlist = root.find("mb:release-list", namespaces=ns)

    if int(rlist.get('count')) == 0:
        return None

    album = rlist.find("mb:release", namespaces=ns)
    artist = album.find("./mb:artist-credit/mb:name-credit/mb:artist",
                        namespaces=ns).find("mb:name", namespaces=ns).text
    title = album.find("mb:title", namespaces=ns).text
    aid = album.get('id')
    return dict(artist=artist, title=title, aid=aid)


def _get_mb_tracks(albumid):
    """ Get track listing from MusicBraiz by album id. """

    ns = {'mb': 'http://musicbrainz.org/ns/mmd-2.0#'}
    url = "http://musicbrainz.org/ws/2/release/" + albumid
    query = {"inc": "recordings"}
    wdata = _do_query(url, query, err='album search error')

    if not wdata:
        return None

    root = ET.fromstring(wdata)
    tlist = root.find("./mb:release/mb:medium-list/mb:medium/mb:track-list",
                      namespaces=ns)
    mb_songs = tlist.findall("mb:track", namespaces=ns)

    tracks = []

    for track in mb_songs:
        title = track.find("./mb:recording/mb:title", namespaces=ns).text
        rawlength = track.find("./mb:recording/mb:length", namespaces=ns).text
        length = int(round(float(rawlength) / 1000))
        tracks.append(dict(title=title, length=length, rawlength=rawlength))

    return tracks


def _best_song_match(songs, title, duration, bitrate):
    """ Select best matching song based on title, length and bitrate.

    Score from 0 to 1 where 1 is best.

    """

    # pylint: disable=R0914
    seqmatch = difflib.SequenceMatcher
    variance = lambda a, b: float(abs(a - b)) / max(a, b)
    candidates = []

    for song in songs:
        dur, tit = int(song['Rduration']), song['song']
        bitr = int("".join(re.findall(r"\d", song['listrate'])))
        title_score = seqmatch(None, title, tit).ratio()
        bitrate_score = 1 - variance(bitrate, bitr)
        duration_score = 1 - variance(duration, dur)

        # apply weightings
        score = duration_score * .5 + title_score * .3 + bitrate_score * .2
        candidates.append((score, song))

    best_score, best_song = max(candidates, key=lambda x: x[0])
    percent_score = int(100 * best_score)
    return best_song, percent_score


def _do_query(url, query, err='query failed', cache=True, report=False):
    """ Perform http request.

    if cache is True, memo is utilised
    if report is True, return whether response is from memo

    """

    # convert query to sorted list of tuples (needed for consistent url_memo)
    query = [(k, query[k]) for k in sorted(query.keys())]
    url = "%s?%s" % (url, urlencode(query))

    if cache and g.memo.get(url):
        return g.memo.get(url) if not report else (g.memo.get(url), True)

    try:
        wdata = urlopen(url).read()

    except (URLError, HTTPError) as e:
        g.message = "%s: %s (%s)" % (err, e, url)
        # g.content = logo(c.r)
        return None if not report else (None, False)

    if cache and wdata:
        g.memo.add(url, wdata)

    return wdata if not report else (wdata, False)


def _make_fname(song):
    """" Create download directory, generate filename. """

    if not os.path.exists(Config.DDIR):
        os.makedirs(Config.DDIR)

    filename = song['singer'][:49] + " - " + song['song'][:49] + ".mp3"
    # filename = os.path.join(Config.DDIR, mswinfn(filename.replace("/", "-")))
    filename = os.path.join(Config.DDIR, filename)
    return filename


def _download(song, filename):
    """ Download file, show status, return filename. """

    xprint("Downloading %s%s%s ..\n" % (c.g, filename, c.w))
    status_string = ('  {0}{1:,}{2} Bytes [{0}{3:.2%}{2}] received. Rate: '
                     '[{0}{4:4.0f} kbps{2}].  ETA: [{0}{5:.0f} secs{2}]')
    song['track_url'] = get_stream(song)
    dbg("[4] fetching url " + song['track_url'])
    resp = urlopen(song['track_url'])
    dbg("fetched url " + song['track_url'])
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
        stats = (c.y, bytesdone, c.w, bytesdone * 1.0 / total, rate, eta)

        if not chunk:
            outfh.close()
            break

        status = status_string.format(*stats)
        sys.stdout.write("\r" + status + ' ' * 4 + "\r")
        sys.stdout.flush()

    return filename


def _bi_range(start, end):
    """
    Inclusive range function, works for reverse ranges.

    eg. 5,2 returns [5,4,3,2] and 2, 4 returns [2,3,4]

    """
    if start == end:
        return (start,)

    elif end < start:
        return reversed(range(end, start + 1))

    else:
        return range(start, end + 1)


def _parse_multi(choice, end=None):
    """ Handle ranges like 5-9, 9-5, 5- and -5. Return list of ints. """

    end = end or str(g.model.size)
    pattern = r'(?<![-\d])(\d+-\d+|-\d+|\d+-|\d+)(?![-\d])'
    items = re.findall(pattern, choice)
    alltracks = []

    for x in items:

        if x.startswith("-"):
            x = "1" + x

        elif x.endswith("-"):
            x = x + str(end)

        if "-" in x:
            nrange = x.split("-")
            startend = map(int, nrange)
            alltracks += _bi_range(*startend)

        else:
            alltracks.append(int(x))

    return alltracks

def show_help(helpname=None):
    """ Print help message. """

    print(HELP)


def quits(showlogo=True):
    """ Exit the program. """

    sys.exit()


def download(num):
    """ Download a track. """

    song = (g.model.songs[int(num) - 1])
    filename = _make_fname(song)

    try:
        f = _download(song, filename)
        g.message = "Downloaded " + c.g + f + c.w

    except IndexError:
        g.message = c.r + "Invalid index" + c.w

    except KeyboardInterrupt:
        g.message = c.r + "Download halted!" + c.w

        try:
            os.remove(filename)

        except IOError:
            pass

    finally:
        g.content = "\n"


def prompt_for_exit():
    """ Ask for exit confirmation. """

    g.message = c.r + "Press ctrl-c again to exit" + c.w
    g.content = generate_songlist_display()
    screen_update()

    try:
        userinput = compat_input(c.r + " > " + c.w)

    except (KeyboardInterrupt, EOFError):
        quits(showlogo=False)

    return userinput


def nextprev(np):
    """ Get next / previous search results. """

    if np == "n":
        if len(g.model.songs) == 20 and g.last_search_query:
            g.current_page += 1
            search(g.last_search_query, g.current_page, splash=False)
            g.message += " : page %s" % g.current_page

        else:
            g.message = "No more songs to display"

    elif np == "p":
        if g.current_page > 1 and g.last_search_query:
            g.current_page -= 1
            search(g.last_search_query, g.current_page, splash=False)
            g.message += " : page %s" % g.current_page

        else:
            g.message = "No previous songs to display"

    g.content = generate_songlist_display()


def main():
    """ Main control loop. """

    # DEBUG
    # pdb.set_trace()

    # update screen
    g.content = generate_songlist_display()
#    g.content = logo(col=c.g, version=__version__) + "\n"
    if not sys.argv[1:]:
    	g.message = "Rechercher la musique que vous voulez " + c.b + "- [h]elp, [a]lbum, [t]op, [c]config, [q]uit" + c.w
    screen_update()

    # open playlists from file
    # open_from_file()

    # get cmd line input
    inp = " ".join(sys.argv[1:])

    # input types
#    word = r'[^\W\d][-\w\s]{,100}'
#    rs = r'(?:repeat\s*|shuffle\s*)'
    regx = {
        # 'ls': r'ls$',
        # 'vp': r'vp$',
        'show_help': r'h$',
        'search': r'([a-zA-Z]\w.{0,500})',
        'search_album': r'a\s*(.{0,500})',
        'download': r'(\d{1,2})$',
        'top': r't\s*(|3m|6m|year|all)\s*$',
        'showconfig': r'(c)$',
        'setconfig': r'c\s*(\w+)\s*"?([^"]*)"?\s*$',
        'quits': r'(?:q|quit|exit)$',
#        'plist': r'.*(list[\da-zA-Z]{8,14})$',
#        'play': r'(%s{0,3})([-,\d\s]{1,250})\s*(%s{0,2})$' % (rs, rs),
        # 'top': r'top(|3m|6m|year|all)\s*$',
######  'search': r'(?:search|\.|/)\s*(.{0,500})',
        
#        'play_pl': r'play\s*(%s|\d+)$' % word,
        # 'download': r'(?:d|dl|download)\s*(\d{1,4})$',
        
#        'nextprev': r'(n|p)$',
#        'play_all': r'(%s{0,3})all\s*(%s{0,3})$' % (rs, rs),
#        'save_last': r'(save)\s*$',
        #'setconfig': r'set\s*(\w+)\s*"([^"]*)"\s*$',
        
        
#        'add_rm_all': r'(rm|add)\s*all$',
#        'clearcache': r'clearcache$',
        #'showconfig': r'(showconfig)',
        
#        'playlist_add': r'add\s*(-?\d[-,\d\s]{1,250})(%s)$' % word,
#        'open_save_view': r'(open|save|view)\s*(%s)$' % word,
#        'songlist_mv_sw': r'(mv|sw)\s*(\d{1,4})\s*[\s,]\s*(\d{1,4})$',
#        'songlist_rm_add': r'(rm|add)\s*(-?\d[-,\d\s]{,250})$',
#        'playlist_rename': r'mv\s*(%s\s+%s)$' % (word, word),
#        'playlist_remove': r'rmp\s*(\d+|%s)$' % word,
#        'open_view_bynum': r'(open|view)\s*(\d{1,4})$',
#        'playlist_rename_idx': r'mv\s*(\d{1,3})\s*(%s)\s*$' % word,
    }

    # compile regexp's
    regx = {name: re.compile(val, re.UNICODE) for name, val in regx.items()}
    prompt = "> "

    while True:
        try:
            # get user input
            userinput = inp or compat_input(prompt)
            userinput = userinput.strip()
#            print(c.w)

        except (KeyboardInterrupt, EOFError):
            userinput = prompt_for_exit()

        inp = None

        for k, v in regx.items():
            if v.match(userinput):
                func, matches = k, v.match(userinput).groups()

                try:
                    globals()[func](*matches)

                except IndexError:
                    g.message = F('invalid range')
                    # g.content = g.content #or generate_songlist_display()

                break

        else:
            if userinput:
                g.message = c.b + "Bad syntax. Enter h for help" + c.w

        screen_update()


if __name__ == "__main__":
    if has_colorama:
        init_colorama()
    main()