import os
import cPickle as pickle

cli = True
daemon = False
songlist = []
last_search_query = ""
current_page = 1
last_opened = message = content = ""
READLINE_FILE = None
member_var = lambda x: not(x.startswith("__") or callable(x))

def get_default_dldir():
    """ Get system default Download directory, append mps dir. """
    join, user = os.path.join, os.path.expanduser("~")
    USER_DIRS = join(user, ".config", "user-dirs.dirs")
    # DOWNLOAD_HOME = join(user, "Downloads")
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
    # dldir = py2utf8_decode(dldir)
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


class Color(object):
    """ Class for holding colour code values. """
    white = "\x1b[%sm" % 0
    underline = "\x1b[%sm" * 3 % (2, 4, 33)
    cols = ["\x1b[%sm" % n for n in range(91, 96)]
    red, green, yellow, blue, pink = cols
    if not Config.COLOURS:
        ul = red = green = yellow = blue = pink = white = ""


config = [x for x in sorted(dir(Config)) if member_var(x)]
configbool = [x for x in config if type(getattr(Config, x)) is bool]
defaults = {setting: getattr(Config, setting) for setting in config}
CFFILE = os.path.join(get_config_dir(), "config")

try:
    import readline
    readline.set_history_length(2000)
    has_readline = True

except ImportError:
    has_readline = False

def saveconfig():
    """ Save current config to file. """
    config = {setting: getattr(Config, setting) for setting in config}
    pickle.dump(config, open(CFFILE, "wb"), protocol=2)

# override config if config file exists
def loadconfig(pfile):
    """ Load config from file. """
    saved_config = pickle.load(open(pfile, "rb"))
    for kk, vv in saved_config.items():
        setattr(Config, kk, vv)

# Account for old versions
if os.path.exists(CFFILE):
    loadconfig(CFFILE)
if has_readline:
    READLINE_FILE = os.path.join(get_config_dir(), "input_history")
    if os.path.exists(READLINE_FILE):
        readline.read_history_file(READLINE_FILE)

def launch_server():
    """ Launch the web server. """
    import runserver
    runserver.main()

def launch_terminal():
    """ Launch the application in terminal mode. """
    import terminal
    terminal.main()
