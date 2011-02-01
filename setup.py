#!/usr/bin/env python

from setuptools import setup
from otfbot.lib import version

setup(name='otfbot',
     version=version.simple_version,
     description='a modular IRC-Bot',
     long_description='a modular IRC-Bot',
     author='Alexander Schier, Robert Weidlich, Thomas Wiegart',
     author_email='otfbot-dev@list.otfbot.org',
     url="http://www.otfbot.org/",
     license="GPLv2",
     install_requires=["twisted >=10.0.0", "pyyaml", "pyopenssl", "pycrypto",
         "pyasn1"],
     download_url="http://www.otfbot.org/files/otfbot-%s.tar.gz"
        % version.simple_version,
     packages=[
        'otfbot',
        'otfbot.services',
        'otfbot.plugins',
        'otfbot.plugins.ircClient',
        'otfbot.plugins.ircServer',
        'otfbot.lib',
        'otfbot.lib.pluginSupport',
        'twisted.plugins',
    ],
    package_data={
            'twisted': ['plugins/otfbot_plugin.py',
                'plugins/genconfig_plugin.py'],
            'otfbot.plugins.ircClient': ['*.yaml'],
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
    ])
