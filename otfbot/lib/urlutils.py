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

import urllib2
from twisted.web import client
client.HTTPClientFactory.noisy=False

from otfbot.lib import version

_version=version._version

def get_headers(url):
    request=urllib2.Request(url)
    request.get_method=lambda: 'HEAD'
    http=urllib2.urlopen(request)
    return http.headers

def is_html(headers):
    return headers['content-type'].lower()[:9] == "text/html"

def download_headers_and_content_if_html(url):
    headers=get_headers()
    content=''
    if is_html(headers):
        content=download(url)
    return (headers, content)

def download_if_html(url):
    """
    download content, if the mimetype is text/html
    """
    if is_html(get_headers(url)):
        return download(url)
    return ""

def download(url, file=None, **kwargs):
    """ 
    Uses twisted.web.client.getPage() to fetch a Page via HTTP
    
    @return: A Defered which will call a Callback with the content as argument
    
    """
    if "agent" not in kwargs:
        kwargs['agent'] = "OTFBot (%s; otfbot.berlios.de)" % _version.short()
    if file:
        return client.downloadPage(url, file, **kwargs)
    else:
        return client.getPage(url, **kwargs)
