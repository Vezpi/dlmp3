# -*- coding:utf-8 -*-

import os
import cPickle as pickle


class Launcher(object):
    """ Holds Launcher options. """

    def __init__(self):
    	""" Application options. """
        self.CLI = True
        self.DAEMON = False
        self.PORT = 5000
        self.DEBUG = False

    def start(self):
        """ Launch the application. """
        if self.CLI:
            import terminal
            terminal.main()
        else:
            import runserver
            runserver.main()


launcher = Launcher()


class Application(object):
    """ Holds the global application objects. """

    def __init__(self):
        self.songlist = []
        self.last_search_query = ""
        self.current_page = 1
        self.last_opened = ""
        self.message = ""
        self.content = ""

    
application = Application()


class Config(object):
    """ Holds various configuration values. """

    def get_default_dldir(self):
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

    def get_config_dir(self):
        """ Get configuration directory. """
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conf")
        return config_dir

    def __init__(self):
        self.COLOURS = True
        self.DLDIR = self.get_default_dldir()
        self.READLINE_FILE = None
        self.CFFILE = os.path.join(self.get_config_dir(), "dlmp3.config")
        self.SOURCE = "pleer"

    def getitem(self):
        return self.__dict__

    def save(self):
        """ Save current config to file. """
        if not os.path.exists(self.get_config_dir()):
            try:
                os.makedirs(self.get_config_dir())
                os.chmod(self.get_config_dir(), 0777)
            except OSError:
                application.message = Color.red + "Impossible de créer le répertoire " + self.get_config_dir() + Color.white
        to_save = self.getitem()
        pickle.dump(to_save, open(self.CFFILE, "wb"), protocol=2)

    # override config if config file exists
    def load(self, pfile):
        """ Load config from file. """
        saved_config = pickle.load(open(pfile, "rb"))
        for kk, vv in saved_config.items():
            setattr(self, kk, vv)


config = Config()




