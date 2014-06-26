import time

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