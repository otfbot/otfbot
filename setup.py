#!/usr/bin/env python

from distutils.core import setup
from otfbot.lib import version

setup(name='otfbot',
      version=version._version.base(),
      description='Modular IRC-Bot',
      long_description='',
      author='Alexander Schier, Robert Weidlich, Thomas Wiegart',
      author_email='otfbot-dev@list.otfbot.org',
      url="http://www.otfbot.org/",
      download_url="http://www.otfbot.org/files/otfbot-%s.tar.gz" % version._version.base(),
      license="GPLv2",
      packages=[
	'otfbot',
	'otfbot.services',
	'otfbot.plugins',
	'otfbot.plugins.ircClient',
	'otfbot.lib',
        'twisted.plugins',
	],
      package_data={
            'twisted': ['plugins/otfbot_plugin.py', 'plugins/genconfig_plugin.py'],
      },
      classifiers=[
	"Development Status :: 5 - Production/Stable",
	"Environment :: No Input/Output (Daemon)",
	"Framework :: Twisted",
	"Intended Audience :: End Users/Desktop",
	"License :: OSI Approved :: GNU General Public License (GPL)",
	"Operating System :: OS Independent",
	"Programming Language :: Python",
	"Programming Language :: Python :: 2.6",
	"Topic :: Communications :: Chat :: Internet Relay Chat",
	"Topic :: Games/Entertainment"
      ]
)
