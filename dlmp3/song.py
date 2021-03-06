import os
import time


class Song(object):
    """ Characteristics of a single song. """

    def __init__(self):
        self.link = None
        self.track = None
        self.title = None
        self.artist = None
        self.size = None
        self.length = None
        self.bitrate = None

    def make_filename(self, config):
        """" Create download directory, generate filename. """
        if not os.path.exists(config.DLDIR):
            os.makedirs(config.DLDIR)
        if self.source == "pleer":
            filename = self.artist[:49] + " - " + self.title[:49] + ".mp3"
        elif self.source == "mp3download":
            filename = self.track + ".mp3"
        self.filename = os.path.join(config.DLDIR, filename)

    def remove_filename(self):
        try:
            os.remove(self.filename)
        except IOError:
            pass

    def get_link(self, search):
        """ Return the url for a song. """
        if self.source == "pleer" and not self.link:
            wdata = search.get_pleer_link(self)
            if wdata.get("track_link"):
                self.link = wdata['track_link']
                return True
            else:
                return False
        elif self.source == "deezer":
            return False
        else:
            return True

    def duration_format(self, duration):
        """ Transform the format of the duration. """
        self.length = time.strftime('%M:%S', time.gmtime(int(duration)))

    def size_format(self, size):
        """ Transform the format of the size. """
        size = str(size)[:3]
        size = size[0:2] + " " if size[2] == "." else size
        self.size = size + ' MB'

    def filter(self, raw_song):
        maxi = 600
        if not raw_song[4] == "MB":
            return False
        time = raw_song[2].split(":")
        seconds = int(time[0]) * 60 + int(time[1])
        if seconds > maxi:
            return False
        return True


class Songlist(object):
    """ List of several songs. """

    def __init__(self, data):
        self.songs = []
        self.raw_songs = data[0]
        self.source = data[1]
        if self.raw_songs:
            self.build(self.source)

    def build(self, source):
        """ Build a list of songs from a search querry. """
        if source == "pleer":
            self.categories = [["artist", "50"], ["title", "50"], ["size", "9"], ["length", "8"], ["bitrate", "7"]]
        elif source == "mp3download":
            self.categories = [["track", "100"], ["size", "9"], ["length", "8"]]
        elif source == "deezer":
            self.categories = [["artist", "50"], ["title", "50"], ["length", "8"]]
        for raw_song in self.raw_songs:
            song = Song()
            song.source = source
            if source == "pleer": # list of dict : keys : ['Rfile_id', 'Rsinger', 'singer', 'Rduration', 'Rsong', 'song', 'Rsource', 'source', 'Rsize', 'rate', 'link', 'file_id', 'listrate', 'duration', 'Rrate', 'size', 'Rlink']
                song.artist = raw_song['singer']
                song.title = raw_song['song']
                song.size_format(raw_song['size'])
                song.bitrate = raw_song['listrate']
                song.duration_format(raw_song['duration'])
                song.id = raw_song['link']       
            elif source == "mp3download": # list of list : ['All Of Me', 'http://mp3download.pw/download.php?name=all+of+me&url=aHR0cDovL2FwaS5zb3VuZGNsb3VkLmNvbS90cmFja3MvMTEzNjYyNjc2L3N0cmVhbT9jbGllbnRfaWQ9YWU5MzEzMzc5YzNjMGZlM2Y4M2U4MGY4MzVmMGFkNGM=', '04:29', '10.29', 'MB', '']
                if not song.filter(raw_song):
                    continue
                song.track = raw_song[0]
                song.link = raw_song[1]
                song.length = raw_song[2]
                song.size = raw_song[3] + ' ' + raw_song[4]
            elif source == "deezer": # list of dict : keys : [u'album', u'artist', u'title', u'link', u'duration', u'preview', u'type', u'id']
                song.artist = raw_song['artist']['name']
                song.title = raw_song['title']
                song.duration_format(raw_song['duration'])
            self.songs.append(song)
            
