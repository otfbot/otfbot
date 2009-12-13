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
# (c) 2008 by Alexander Schier
#
import urllib2
from twisted.web import client

client.HTTPClientFactory.noisy=False
svnrevision="$Revision: 187 $".split(" ")[1]

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
    if is_html(get_headers(url)):
        return download(url)
    return ""

def download(url, file=None, **kwargs):
    """ 
    Uses twisted.web.client.getPage() to fetch a Page via HTTP
    
    @return: A Defered which will call a Callback with the content as argument
    
    """
    if not kwargs.has_key("agent"):
        kwargs['agent'] = "OTFBot (svn r%s; otfbot.berlios.de)"%(svnrevision)
    if file:
        return client.downloadPage(url, file, **kwargs)
    else:
        return client.getPage(url, **kwargs)
