import os
import pickle
import hashlib
import time
from core import zdecomp, zcomp

class Memo(object):

    """ Memo handling and creation. """

    def __init__(self, filepath, life=60 * 60 * 24 * 3):
        self.life = life
        self.filepath = filepath
        self.data = {}

        if os.path.isfile(filepath):

            # try:

            with open(filepath, "rb") as f:
                self.data = pickle.load(f)
            #         dbg("cache opened, %s items", len(self.data))

            # except (EOFError, IOError) as e:
            #     dbg(str(e))

        # else:
        #     dbg("No cache found!")

        self.prune()

    def add(self, key, val, lifespan=None):
        """ Add key value pair, expire in lifespan seconds. """

        key = key.encode("utf8")
        key = hashlib.sha1(key).hexdigest()
        lifespan = self.life if not lifespan else lifespan
        expiry_time = int(time.time()) + lifespan
        self.data[key] = dict(expire=expiry_time, data=zcomp(val))
        # dbg("cache item added: %s", key)

    def get(self, key):
        """ Fetch a value if it exists and is fresh. """

        now = int(time.time())
        key = key.encode("utf8")
        key = hashlib.sha1(key).hexdigest()

        if key in self.data:

            if self.data[key]['expire'] > now:
                # dbg("cache hit %s", key)

                return zdecomp(self.data[key]['data'])

            else:
                del self.data[key]
                return None

        return None

    def prune(self):
        """ Remove stale items. """

        now = int(time.time())
        # dbg("Pruning: ")
        stalekeys = [x for x in self.data if self.data[x]['expire'] < now]
        # dbg("%s stale keys; %s total kys", len(stalekeys), len(self.data))

        for x in stalekeys:
            del self.data[x]

    def save(self):
        """ Save memo file to persistent storage. """

        self.prune()

        with open(self.filepath, "wb") as f:
            pickle.dump(self.data, f, protocol=2)