__author__ = "Andy Belsky"
__version__ = "0.1"
__email__ = "andy@abelsky.com"

import argparse
import getpass
import locale
import os
import ipodsync
import vksync

def sync(args):
    vk = vksync.VKUtil(args.username, args.password)

    if args.friend_name:
        name = args.friend_name.decode(locale.getdefaultlocale()[1])
        id = vksync.friend_id(vk.get_friends(), name)
        if not id:
            return
    else:
        id = None

    music = vk.get_songs(id)
    vksync.download(music, args.target_path)

    if args.sync:
        playlist = 'VK music'
        if args.friend_name:
            playlist += ' from ' + args.friend_name

        ipodsync.sync_folder(args.target_path, playlist)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VK.com audio records fetcher and synchronizer.')

    parser.add_argument('--username', '-u', help='Account login.')

    parser.add_argument('--password', '-p', required=False,
        help='Password. If omitted, will be requested from command line.')

    parser.add_argument('--friend-name', required=False,
        help='Name of the user to fetch records from. If omitted, the authenticated account is used.')

    parser.add_argument('--target-path', default=os.getcwd(),
        help='Destination path for the audio files. If not specified, the current directory will be used.')

    parser.add_argument('--sync', default='store_true',
        help='Synchronize with the connected iPod. Requires Windows, iTunes, connected iPod and a plenty of luck.')

    args = parser.parse_args()

    if not args.password:
        #noinspection PyArgumentEqualDefault
        args.password = getpass.getpass('Password: ')

    try:
        sync(args)

    except vksync.AuthenticationException:
        print 'Authentication failed for "%s". Please check the credentials and try again.' % args.username
