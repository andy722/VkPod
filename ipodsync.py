"""
Utilities to upload a bunch of MP3s to your iPod. Works via COM, so requires Windows,
iTunes and some luck.
"""

__author__ = "Andy Belsky"
__version__ = "0.1"
__email__ = "andy@abelsky.com"

import glob
import win32com.client

from win32com.client import CastTo

class ITunesException(Exception):
    pass


class IPodSynchronizer:
    def __init__(self):
        self._itunes = win32com.client.Dispatch("iTunes.Application")

    def start_upload(self, name):
        self.ipod = self.__get_ipod()

        self._disable_all_tracks()
        self._playlist = self._create_playlist(name)

    def add_file(self, path):
        return self._add_file(path, self._playlist)

    def sync(self):
        self.ipod.UpdateIPod()

    def eject(self):
        self.ipod.EjectIPod()

    def _disable_all_tracks(self):
        library = self._itunes.LibraryPlaylist
        for t in library.Tracks:
            if t.Enabled:
                t.Enabled = False

    def _add_file(self, path, user_playlist, enabled=True):
        library = self._itunes.LibraryPlaylist

        status = library.AddFile(path)
        assert len(status.Tracks) == 1

        t = status.Tracks[0]

        user_playlist.AddTrack(t)
        t.Enabled = enabled

        return t

    def _create_playlist(self, name):
        cast = lambda playlist: CastTo(playlist, 'IITUserPlaylist')

        # Check if playlist already exists
        for p in [p for p in self._itunes.LibrarySource.Playlists if p.Name == name]:
            p.Delete()

        return cast(self._itunes.CreatePlaylist(name))

    def __get_ipod(self):
        ITSourceKindIPod = 2
        ipods = [src for src in self._itunes.Sources if src.Kind == ITSourceKindIPod]
        if not ipods:
            raise ITunesException('No attached devices found. Please connect your IPod.')
        elif len(ipods) > 1:
            raise ITunesException('Multiple devices found: ', ipods)

        return CastTo(ipods[0], 'IITIPodSource')


def sync_folder(path, playlist='my-playlist'):
    sync = IPodSynchronizer()

    sync.start_upload(playlist)
    print 'Found attached device: "%s" (%s Gb)' % (sync.ipod.Name, round(sync.ipod.Capacity / (1024 ** 3)) )
    print 'Importing to "%s":' % playlist

    for f in glob.glob(path + '/*.mp3'):
        t = sync.add_file(f)
        print '  %s: %s - %s' % (t.Artist or 'Unknown artist',
                                 t.Album or 'Unknown album',
                                 t.Name or 'Unknown title')

    print 'Started syncing to "%s". Check ITunes window to see when the process is finished' % sync.ipod.Name
    sync.sync()

    raw_input('Press [Return] to eject device or interrupt to finish...')
    sync.eject()
