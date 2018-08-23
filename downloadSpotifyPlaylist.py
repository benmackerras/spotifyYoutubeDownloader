import json
import re
import urllib
import urllib2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup
import os
import sys
import youtube_dl

# This is doing tracks under 1 hour only (since it usually means its an album)
def toSeconds(i):
	ar = i.split(':')
	if len(ar) == 2: 
		return ((int(ar[0]) * 60) + int(ar[1]))
	else:
		return 0

def inRange(real, yt, maxDif):
	if abs(yt - real) < maxDif: # find videos within 1 minute of the spotify track length
		return True
	else:
		return False

def closest(to, comp):
	arr = list()
	for i in comp:
		arr.append(abs(abs(i)-abs(to)))

	for i in range(1,len(comp)):
		if abs(abs(comp[i])-abs(to)) < abs(abs(comp[i-1])-abs(to)):
			comp[i], comp[i-1] = comp[i-1], comp[i]
	return comp

def getVid(soup):
	for thumb in soup.find_all("a", class_=" yt-uix-sessionlink spf-link "):
		try:
			vidLen = thumb.find("span", class_="video-time").get_text()
		except AttributeError:
			break
		toSeconds(vidLen)
		validLen = toSeconds(vidLen)
		if validLen > 0:
			if inRange(int(i[2]), int(validLen), 20):
				return(thumb["href"])
	return False

class MyLogger(object):
    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def printProgress(d):
	if d['status'] == 'finished':
		print('Download complete, converting...')

ccm = SpotifyClientCredentials()
sp = spotipy.Spotify(client_credentials_manager=ccm)
uri = sys.argv[1]
uname = uri.split(':')[2]
playlistId = uri.split(':')[4]
results = sp.user_playlist(uname, playlistId)
playlistName = results["name"]
playlist = list()

for tracks in results["tracks"]["items"]:
	title = tracks['track']['name']
	artists = ''
	for names in tracks["track"]["artists"]:
		artists = artists + str(names['name']) + ' '
	duration = tracks['track']['duration_ms'] / 1000
	playlist.append([title, artists, duration])

queryUrl = "https://www.youtube.com/results?search_query=" # + "&page=1"
videoLinks = []

#Get the videos for each track in the playlist
for i in playlist:
	query = (i[0] + ' ' + i[1]).replace(' ', '+')[:-1]
	resp = urllib2.urlopen(queryUrl + query + "&page=1")
	html = resp.read()
	soup = BeautifulSoup(html,features="html.parser")
	try:
		videoLinks.append("https://youtube.com" + getVid(soup))
	except TypeError:
		print("Could not find " + query)
"""
	#outtmp: the output directory
"""
ydl_opts = {
	'outtmpl': os.path.dirname(os.path.abspath(__file__)) + '/' + playlistName + '/' + '%(title)s.%(ext)s',
	'forcetitle': 'true',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': MyLogger(),
    'progress_hooks': [printProgress],
}
youtube_dl.YoutubeDL(ydl_opts).download(videoLinks)