"""
Utilities for communication w/ vk.com social network.
"""

__author__ = "Andy Belsky"
__version__ = "0.1"
__email__ = "andy@abelsky.com"

import difflib
import httplib
import os
import re
import shutil
import tempfile
import urllib
import urllib2

class VKException(Exception):
    pass


class AuthenticationException(VKException):
    pass


class VKAuth:
    """Performs basic VK.com authentication."""

    def __init__(self, login, password):
        self.__login = login
        self.__password = password
        self.__sid = None

        urllib2.install_opener(self.__build_opener())

        self.__id, self.__sid = self.__auth()


    def __build_opener(self):
        """To prevent automatic redirects on 302 HTTP code."""
        from urllib2 import (OpenerDirector, ProxyHandler, UnknownHandler, HTTPHandler,
                             HTTPDefaultErrorHandler, HTTPRedirectHandler,
                             FTPHandler, FileHandler)

        opener = OpenerDirector()

        default_classes = [ProxyHandler, UnknownHandler, HTTPHandler,
                           HTTPDefaultErrorHandler, HTTPRedirectHandler,
                           FTPHandler, FileHandler]

        if hasattr(httplib, 'HTTPS'):
            default_classes.append(urllib2.HTTPSHandler)

        for clazz in default_classes:
            opener.add_handler(clazz())

        return opener


    def _get_sid(self):
        return self.__sid

    def _get_id(self):
        return self.__id

    def __auth(self):
        location = lambda data: data.info().dict['location']
        cookies = lambda data: data.info().dict['set-cookie']

        # act = login
        host = 'http://login.vk.com/?act=login'
        post = urllib.urlencode({'email': self.__login, 'pass': self.__password})
        data = urllib2.urlopen(urllib2.Request(host, post))

        # user ID
        id = re.match(r'.*l=([0-9]+); ', cookies(data)).group(1)

        target = location(data)

        # act = slogin
        data = urllib2.urlopen(target)
        target = location(data)

        # act = vkcomredirect
        data = urllib2.urlopen(target)
        target = location(data)

        if not re.match(r'.*&hash=[a-z0-9]+.*', target):
            # redirected to login page
            raise AuthenticationException('Authentication failed.')

        # act = slogin
        data = urllib2.urlopen('http://vk.com' + target)
        cookie = cookies(data)

        sid = re.match(r'.*(remixsid=[a-z0-9]+; )', cookie).group(1)
        return id, sid


    def fetch(self, url, data=None):
        sid = self._get_sid()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'windows-1251,utf-8;q=0.7,*;q=0.3',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'Connection': 'keep-alive',
            'Host': 'vk.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                          'AppleWebKit/535.11 (KHTML, like Gecko) '
                          'Chrome/17.0.963.83 Safari/535.11',
            'Cookie': 'remixlang=0; remixdt=10800; remixchk=5; remixseenads=2; remixflash=11.1.102; remixvkcom=1; ' + sid
        }

        if data:
            data = urllib.urlencode(data)

        data = urllib2.urlopen(urllib2.Request(url, data=data, headers=headers))
        return data.read()


class VKUtil(VKAuth):
    def __init__(self, login, password):
        VKAuth.__init__(self, login, password)


    def get_songs(self, user_id=None):
        """
        Yields tuples of:
            (title, artist, mp3 URL)
        """

        if not user_id:
            user_id = self._get_id()

        data = {
            'act': 'load_audios_silent',
            'al': 1,
            'edit': 0,
            'gid': 0,
            'id': user_id
        }

        page = self.fetch('http://vk.com/audio', data)

        def decode(s):
            s = s.decode('cp1251').strip()
            s = re.sub(r'&#[0-9]+;', '', s)
            s = re.sub(r'&amp;', '&', s)
            return s

        # XXX: yep, that's scary... Maybe parse as JSON?
        for sub in re.findall(r'\[[^\[]+\]', page):
            m = re.match(r"\['([0-9]+)','([0-9]+)','([a-z0-9/:.]+)','([0-9]+)','([0-9]+:[0-9]+)','([^']*)','([^']*)',.*", sub)

            if m:
                url = m.group(3)
                artist = m.group(6)
                title = m.group(7)

                yield decode(title), decode(artist), url


    def get_friends(self, user_id=None):
        """
        Yields tuples of:
            (id, name, page URL)
        """
        if not user_id:
            user_id = self._get_id()

        data = {
            'act': 'load_friends_silent',
            'al': 1,
            'edit': 0,
            'gid': 0,
            'id': user_id
        }
        page = self.fetch('http://vk.com/al_friends.php', data)

        def decode(s):
            s = s.decode('cp1251')
            return s

        # XXX: yep, that's scary... Maybe parse as JSON?
        for sub in re.findall(r'\[[^\[]+\]', page):
            m = re.match(r"\['([0-9]+)','([a-z0-9/:_.]+)','([/a-z_0-9.]+)','([0-9]+)','([0-9]+)','([^']*)',.*", sub)
            if m:
                id = m.group(1)
                url = 'http://vk.com/' + m.group(3)
                name = m.group(6)

                yield id, decode(name), url


def friend_id(friends, friend_name):
    """
    Returns id of a friend with the specified name or None if not found.
    """

    friends = list(friends)

    def exact_match(friend_name):
        for (id, name, url) in friends:
            if name == friend_name:
                return id

    # look for an exact match ...
    id = exact_match(friend_name)
    if id:
        return id

    matches = difflib.get_close_matches(friend_name, [name for (id, name, url) in friends])

    if not matches:
        print "Got %d friends, but no one like %s..." % (len(friends), friend_name)

    elif len(matches) == 1:
        name = matches[0]
        print 'Assuming you meant "%s"...' % name
        return exact_match(name)

    else:
        print 'Did you mean one of these: ', matches
        return None


def download(music, path, logger=None):
    if logger is None:
        def logger(x):  print x

    music = list(music)

    count = len(music)

    logger('Downloading %d files...' % count)

    if count and not os.path.exists(path):
        os.mkdir(path)

    for (index, (title, artist, url)) in [(i, music[i]) for i in range(0, count)]:
        name = url.split('/')[-1]
        local_name = os.path.join(path, name)

        if os.path.exists(local_name):
            logger('  %d/%d: "%s" - "%s" -> %s (already exists)' % (index + 1, count, artist, title, local_name))
            continue
        else:
            logger('  %d/%d: "%s" - "%s" -> %s' % (index + 1, count, artist, title, local_name))

        with tempfile.TemporaryFile(prefix=name, dir=path) as file:
            file.write(urllib2.urlopen(url).read())

            with open(local_name, 'w') as local_file:
                shutil.copyfileobj(file, local_file)