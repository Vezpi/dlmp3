#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import pickle
from terminal import py2utf8_decode
from urllib2 import build_opener, HTTPError, URLError

member_var = lambda x: not(x.startswith("__") or callable(x))

def get_default_dldir():
    """ Get system default Download directory, append mps dir. """

    join, user = os.path.join, os.path.expanduser("~")

    USER_DIRS = join(user, ".config", "user-dirs.dirs")
    # DOWNLOAD_HOME = join(user, "Downloads")

    # if 'XDG_DOWNLOAD_DIR' in os.environ:
    #     dldir = os.environ['XDG_DOWNLOAD_DIR']

    if os.path.exists(USER_DIRS):
        lines = open(USER_DIRS).readlines()
        defn = [x for x in lines ]

        if len(defn) == 0:
            dldir = user

        else:
            dldir = defn[0].split("=")[1]\
                .replace('"', '')\
                .replace("$HOME", user).strip()

    # elif os.path.exists(DOWNLOAD_HOME):
    #     dldir = DOWNLOAD_HOME
    else:
        dldir = user

    dldir = py2utf8_decode(dldir)
    return join(dldir, "dlmp3")


def get_config_dir():
    """ Get user configuration directory.  Create if needed. """

    # if "XDG_CONFIG_HOME" in os.environ:
    #     confd = os.environ["XDG_CONFIG_HOME"]
    # else:
    #     confd = os.path.join(os.environ["HOME"], ".config")

    # oldd = os.path.join(confd, "pms")
    confd = "/etc/dlmp3"

    # if os.path.exists(oldd) and not os.path.exists(confd):
    #     os.rename(oldd, confd)

    if not os.path.exists(confd):
        os.makedirs(confd)

    return confd


class Config(object):

    """ Holds various configuration values. """

    COLOURS = True
    DLDIR = get_default_dldir()
    CONFDIR = get_config_dir()


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


class g(object):

    """ Class for holding globals that are needed throught the module. """

    from dlmp3 import memo
    from dlmp3 import playlist

    album_tracks_bitrate = 320
    model = playlist.Playlist(name="model")
    last_search_query = ""
    current_page = 1
    text = {}
    last_opened = message = content = ""
    config = [x for x in sorted(dir(Config)) if member_var(x)]
    configbool = [x for x in config if type(getattr(Config, x)) is bool]
    defaults = {setting: getattr(Config, setting) for setting in config}
    CFFILE = os.path.join(get_config_dir(), "config")
    memo = memo.Memo(os.path.join(get_config_dir(), "cache" + sys.version[0:5]))
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

def setconfig(key, val):
    """ Set configuration variable. """

    # pylint: disable=R0912
    success_msg = fail_msg = ""
    key = key.upper()

    if key == "ALL" and val.upper() == "DEFAULT":

        for k, v in g.defaults.items():
            setattr(Config, k, v)
            success_msg = "Default configuration reinstated"

    elif key == "DLDIR" and not val.upper() == "DEFAULT":

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