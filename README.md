VkPod
-----

Synchronizes your vk.com music with the iPod with a single script.

vkpod.py
--------

Kind of an entry point.

Command-line tool to:
  * Download music from vk.com
    * Your whole playlist
    * Your friend's, which is specified by name. Names are compared using a fuzzy
      algorithm.
  * Authentication is done using plain login/password, skipping OAuth.
  * Synchronize your playlist with iPod.

ipodsync.py
-----------

Utilities to upload a bunch of MP3s to your iPod. Works via COM, so requires Windows,
iTunes and some luck.

vksync.py
---------

Utilities to download your (or your friend's) MP3s from vk.com.

Credits
-------

You may send cookies and other stuff to Andy Belsky at andy@abelsky.com ;)
