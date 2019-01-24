import sys
import xbmc
import xbmcgui
import xbmcplugin
import requests
import re
from lxml import html
from urlparse import parse_qsl
from datetime import date, timedelta

# https://forum.kodi.tv/showthread.php?tid=324570

_pid = sys.argv[0]
_handle = int(sys.argv[1])
headers = {
  'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36',
}


def list_categories():
  xbmcplugin.setPluginCategory(_handle, 'LA7')
  xbmcplugin.setContent(_handle, 'videos')

  rex = "vS = '(.*?)'"

  page = requests.get('http://www.la7.it/dirette-tv', headers=headers).content
  if re.findall(rex, page):
    url = re.findall(rex, page)[0]
    listitem = xbmcgui.ListItem(label='Live')
    listitem.setInfo('video', {'title': 'Live', 'mediatype': 'video'})
    listitem.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=_handle, url='{0}?action=play&video={1}'.format(_pid, url), listitem=listitem, isFolder=False)

  for x in range(7):
    ddd = (date.today() - timedelta(x)).strftime('%A %d %B %Y')
    listitem = xbmcgui.ListItem(label=ddd)
    listitem.setInfo('video', {'title': ddd, 'mediatype': 'video'})
    xbmcplugin.addDirectoryItem(handle=_handle, url='{0}?action=listing&daysago={1}'.format(_pid, x), listitem=listitem, isFolder=True)

  xbmcplugin.endOfDirectory(_handle)


def list_videos(daysago):
  ddd = (date.today() - timedelta(daysago)).strftime('%A %d %B %Y')
  xbmcplugin.setPluginCategory(_handle, ddd)
  xbmcplugin.setContent(_handle, 'videos')

  page = requests.get('http://www.la7.it/rivedila7/{0}/LA7'.format(daysago), headers=headers).content
  tree = html.fromstring(page)

  for item in tree.xpath('//div[@class="palinsesto_row             disponibile clearfix"]'):
    href = item.xpath('.//div[@class="titolo clearfix"]/a')[0].get('href');
    if not href.startswith('http'):
      href = 'http://www.la7.it{0}'.format(href)

    image = item.xpath('.//a[@class="thumbVideo"]//img')[0]
    time = item.xpath('.//div[@class="orario"]')[0].text.encode('utf-8').strip()
    title = '[{0}] {1}'.format(time, image.get('title').encode('utf-8').strip())
    desc = item.xpath('.//div[@class="descrizione"]/p')[0].text.encode('utf-8').strip()

    listitem = xbmcgui.ListItem(label=title)
    listitem.setInfo('video', {'title': title, 'plot': desc, 'mediatype': 'video'})
    listitem.setArt({'thumb': image.get('src').encode('utf-8').strip()})
    listitem.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=_handle, url='{0}?action=get_play&video={1}'.format(_pid, href), listitem=listitem, isFolder=False)

  xbmcplugin.endOfDirectory(_handle)


def get_and_play_video(path):
  rex = re.compile(r'"(http:[^"]*\.m3u8)"', re.IGNORECASE)
  for m in re.finditer(rex, requests.get(path, headers=headers).content):
    url = m.group(1).encode('utf-8').strip()
    xbmc.log("play {0}".format(url), xbmc.LOGNOTICE)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=xbmcgui.ListItem(path=url))
    break


def play_video(path):
  xbmc.log("play {0}".format(path), xbmc.LOGNOTICE)
  xbmcplugin.setResolvedUrl(_handle, True, listitem=xbmcgui.ListItem(path=path))


xbmc.log(" ".join(sys.argv), xbmc.LOGNOTICE)

def router(paramstring):
  params = dict(parse_qsl(paramstring))
  if params:
    if params['action'] == 'listing':
      list_videos(int(params['daysago']))
    elif params['action'] == 'get_play':
      get_and_play_video(params['video'])
    elif params['action'] == 'play':
      play_video(params['video'])
  else:
    list_categories()

if __name__ == '__main__':
  router(sys.argv[2][1:])
