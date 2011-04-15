# This file is part of OtfBot.
#
# OtfBot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OtfBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OtfBot; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# (c) 2008 - 2010 by Alexander Schier
# (c) 2008 - 2010 by Robert Weidlich
#

"""
   Some functions to simplify handling of HTTP-requests
"""

import urllib2
from twisted.web import client
client.HTTPClientFactory.noisy = False

from twisted.internet import defer
from otfbot.lib import version
from twisted.internet import reactor
_version = version._version

from twisted.web.client import _parse

def get_page_with_header(url, contextFactory=None, *args, **kwargs):
    """
    Download a web page as a string.

    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.

    See HTTPClientFactory to see what extra args can be passed.
    """
    if type(url) == unicode:
        url = url.encode("utf-8")
    scheme, host, port, path = _parse(url)
    factory = client.HTTPClientFactory(url, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)
        
    def cb(page):
        return defer.succeed((page, factory.response_headers))
    factory.deferred.addCallback(cb)
    return factory.deferred

def get_headers(url):
    def cb(args):
        page, header = args
        new_header = {}
        for k in header:
            new_header[k] = header[k][0]
        return defer.succeed(new_header)
    d = get_page_with_header(url, method='HEAD')
    d.addCallback(cb)
    return d

def is_html(headers):
    if not "content-type" in headers:
        return false
    return headers["content-type"].lower()[:9] == "text/html"

def convert_bytes(bytes):
    """
        copied from http://www.5dollarwhitebox.org/drupal/node/84
    """
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size

def download_if_html(url):
    """
    download content, if the mimetype is text/html
    """
    def cb(header):
        if (is_html(header)):
            return download(url)
        else:
            return defer.succeed("")
    d = get_headers(url)
    d.addCallback(cb)
    return d

def download(url, file=None, **kwargs):
    """
    Uses twisted.web.client.getPage() to fetch a Page via HTTP

    @return: A Defered which will call a Callback with the content as argument

    """
    if type(url) == unicode:
        url = url.encode("UTF-8")
    if "agent" not in kwargs:
        kwargs['agent'] = "OTFBot (%s; otfbot.org)" % _version.short()
    if file:
        return client.downloadPage(url, file, **kwargs)
    else:
        return client.getPage(url, **kwargs)
