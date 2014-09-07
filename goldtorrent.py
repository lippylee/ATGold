import requests
import urllib
import xml.sax.saxutils
from io import BytesIO

from flask import Flask, request, render_template, make_response, send_file
from bs4 import BeautifulSoup


app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    s = requests.Session()
    try:
        uid = request.values.get('uid')
        password = request.values.get('pass')

    except:
        auth = request.authorization
        uid = auth.username
        password = auth.password

    if uid is None or password is None:
        discountpage = requests.get('http://www.asiatorrents.me/index.php?page=torrents&discount=3', cookies=s.cookies)

        soup = BeautifulSoup(discountpage.text)
        titles, urls = processdata(soup, gotuid=False)

        rss_xml = render_template('rss2', titles=titles, url=urls)
        response= make_response(rss_xml)
        response.cookies = s.cookies
        response.headers["Content-Type"] = "application/xml"
        return response
    else:
        payload = {'uid': uid, 'pwd': password}
        resp = s.post('http://www.asiatorrents.me/index.php?page=login', data=payload, allow_redirects=True)

        discountpage = requests.get('http://www.asiatorrents.me/index.php?page=torrents&discount=3', cookies=s.cookies)

        soup = BeautifulSoup(discountpage.text)
        titles, urls = processdata(soup, gotuid=True)

        rss_xml = render_template('rss', titles=titles, url=urls, uid=uid, password=password)
        response= make_response(rss_xml)
        response.cookies = s.cookies
        response.headers["Content-Type"] = "application/xml"
        return response

@app.route('/download.php', methods=['GET'])
def download():
    s = requests.Session()
    try:
        uid = request.values.get('uid')
        password = request.values.get('pass')
    except:
        auth = request.authorization
        uid = auth.username
        password = auth.password

    payload = {'uid': uid, 'pwd': password}
    resp = s.post('http://www.asiatorrents.me/index.php?page=login', data=payload, allow_redirects=True)
    ident = request.values.get('id')
    f = request.values.get('f')
    torrent = requests.get('http://www.asiatorrents.me/download.php?id='+str(ident)+"&f="+f, cookies=s.cookies, stream=True)

    torrentfile = BytesIO()
    for block in torrent.iter_content(1024):
        if not block:
            break
        torrentfile.write(block)
    torrentfile.seek(0)
    return send_file(torrentfile,
                     attachment_filename=f,
                     as_attachment=True)


def processdata(soup, gotuid):
    trs = {}
    row_num = 0

    for row in soup.body('table')[12].findAll('tr'):
        trs[row_num] = row('tr')
        row_num = row_num + 1

    title = {}
    url = {}
    j = 0
    for item in trs[1]:
        data = item.find_all('td')
        i = 0
        link_title = {}
        link_url = {}

        for line in data:
            if line.a is not None:
                try:
                    if "View details:" in line.a.attrs[u'title']:
                        if "#comments" in line.a.attrs[u'href']:
                            pass
                        else:
                            link_title[i] = line.a.attrs[u'title'].split(": ")[1]
                except:
                    link_title[i] = None
                try:
                    if "download.php" in line.a.attrs[u'href']:
                        link_url[i] = line.a.attrs[u'href']
                    else:
                        link_url[i] = None
                except:
                    link_url = None
                i = i + 1
        title[j] = link_title[1]
        if gotuid is True:
            url[link_title[1]] = xml.sax.saxutils.escape(urllib.unquote(u'http://zeus.lipnet.org:5000/' + str(link_url[2])))
        else:
            url[link_title[1]] = xml.sax.saxutils.escape(urllib.unquote(u'http://www.asiatorrents.me/' + str(link_url[2])))
        j = j + 1
    print url
    return title, url

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
