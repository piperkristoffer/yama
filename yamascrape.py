#!/usr/bin/env python

#How this is going to go
# Scrape yamaguchy.com
# get a list of links
# make a txt file out of that list
# go to those links and scrape their contents into .doc files
# repeat until whole site library is saved into dir of docs

from bs4 import BeautifulSoup
import requests
import re
# import docx
import sys
import os
import time
from fake_useragent import UserAgent
import random

url_list = []
already_list = []
ua = UserAgent()
proxies = []

def writeLinkIntoFile(link, LL):
    global url_list, already_list
    if link not in '\t'.join(url_list):
        LL.write(link)
        LL.write('\n')
        url_list.append(link)
    else:
        pass

def reformatLink(link, current_url):
    ## Array holds Full Link and link ID (author dirname + page)
    arr = []
    if any(x in link for x in ["#", "None", "@", "javascript", ".edu"]):
        pass
    elif "http://www.yamaguchy.com" in link:
        ## If it's a full link, return string with author dirname and page
        fullLink = link
        ID = link.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    elif "library" in link:
        ## If it's a partial link with library,
        if "/library" in link:
            prepend = "http://www.yamaguchy.com"
        else:
            prepend = "http://www.yamaguchy.com/"
        fullLink = prepend + link
        ID = fullLink.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    elif "../.." in link:
        strip = current_url.rsplit('/',3)[0]
        link = link[5:]
        fullLink = strip + link
        ID = fullLink.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    elif ".." in link:
        # if it's a '..' we 'go back a page' and then add the link to result
        strip = current_url.rsplit('/',2)[0]
        link = link[2:]
        fullLink = strip + link
        ID = fullLink.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    elif "/" not in link:
        # if link just looks like this -> 'econ.html'
        if current_url == "http://www.yamaguchy.com":
            strip = current_url
        else:
            strip = current_url.rsplit('/',1)[0]
        fullLink = strip + "/" + link
        ID = fullLink.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    elif "http" not in link:
        # if link looks like this (maybe?) -> something/econ.html
        strip = current_url.rsplit('/',1)[0]
        fullLink = strip + "/" + link
        ID = fullLink.rsplit('/',2)[1]
        arr.extend((fullLink, ID))
    return arr



def getLinx(a_tags, LL, current_url):
    global url_list
    for tag in a_tags:
        formatted = reformatLink(tag, current_url)
        if formatted == []:
            continue
        writeLinkIntoFile(formatted[0], LL)


def getTags(url):
    r = requests.get(url).text
    rsoup = BeautifulSoup(r, 'html.parser')
    if "<frameset" in str(rsoup):
        frames = rsoup.find_all('frame')
        for f in frames:
            nurl_suf = str(f.get('src'))
            if  any(x in nurl_suf for x in ["list", "toc"]):
                nurl_pre = url.rsplit('/',1)[0]
                nurl = nurl_pre + '/' + nurl_suf
                nr = requests.get(nurl).text
                nrsoup = BeautifulSoup(nr, 'html.parser')
                rsoup = nrsoup
    a_tags = rsoup.find_all('a')
    new_arr = []
    for tag in a_tags:
        try:
            a = str(tag.get('href'))
            new_arr.append(a)
        except:
            pass
    return new_arr

def parseIntoBooks(filename):
    f = open(filename, 'r')
    dict = {}
    lines = f.readlines()
    for line in lines:
        line = line.rstrip()
        author = line.split('/')[4]
        if any(x in line for x in ["/dir/", "/doct/", "/forum", "library/index"]):
            pass
        else:
            if author not in dict.keys():
                ## Add author to dictionary if new
                dict[author] = {}

            if len(line.split('/')) > 6:
                booktag =  line.split('/')[-2]
                page = line.split('/')[6]
                if booktag not in dict[author].keys():
                    ## Add book to author in dictionary if new
                    dict[author][booktag] = []
                for book in dict[author].keys():
                    if book in line and page in line:
                        dict[author][book].append(page)


            else:
                booktag =  line.split('/')[-1][:4]
                page = line.split('/')[5]
                if booktag not in dict[author].keys():
                    ## Add book to author in dictionary if new
                    dict[author][booktag] = []
                for book in dict[author].keys():
                    if book in page:
                        dict[author][book].append(page)

    return dict

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         if isinstance(value, list):
             for v in value:
                 print('\t' * (indent+1) + str(v))



def cleanUp(filename):
    f = open(filename, 'r')
    n = open('gazza.txt', 'w')
    arr = []
    lines = f.readlines()
    for line in lines:
        if line not in arr:
            arr.append(line)
    for item in arr:
        n.write(item)
    n.close()
    os.remove(filename)
    os.rename('gazza.txt', filename)

def titleGetter(page):
    p = page.split('.')[0]
    try:
        n = re.split('_\d+', p)[0]
        return n
    except:
        try:
            n = re.split('\d+',1)
            nr = n[0]+n[1]
            return nr
        except:
            return p

def bookClient(author, pages, book):
    baseurl = "http://www.yamaguchy.com/library/" + author + "/"
    if not os.path.isdir("./books"):
        os.mkdir("./books")
    pathn = "./books/" + author
    if not os.path.isdir(pathn):
        os.mkdir(pathn)
    if len(book)!=4:
        for page in pages:
            requrl = baseurl + book + "/" + page
            r = requests.get(requrl).text.encode('utf-8').decode('ascii', 'ignore')
            rsoup = BeautifulSoup(r, 'html.parser')
            title = "./books/" + author + "/" + book + ".txt"
            with open(title, 'a+') as f:
                f.write('\n')
                try:
                    f.write(rsoup.get_text())
                except:
                    foo = rsoup.get_text()
                    f.write(foo.encode('utf-8'))
    else:
        ## Book Title is given in the pages
        for page in pages:
            requrl = baseurl + page
            r = requests.get(requrl).text.encode('utf-8').decode('ascii', 'ignore')
            rsoup = BeautifulSoup(r, 'html.parser')
            title = "./books/" + author + "/" + titleGetter(page) + ".txt"
            with open(title, 'a+') as f:
                f.write('\n')
                try:
                    f.write(rsoup.get_text())
                except:
                    foo = rsoup.get_text()
                    f.write(foo.encode('utf-8'))

def main():
    global url_list, already_list
    url = sys.argv[1]
    url2 = url+"/index2.html"
    url_list.append(url)
    url_list.append(url2)
    LL = open('linklist.txt', 'a+')
    for url_here in url_list:
        if url_here not in already_list:
            a_tags = getTags(url_here)
            getLinx(a_tags, LL, url_here)
            already_list.append(url_here)
        else:
            pass
    LL.close()

    with open('linklist.txt', 'r') as r:
        z = open('newlist.txt', 'w')
        for line in sorted(r):
            z.write(line)
        z.close()
    os.remove('linklist.txt')
    cleanUp('newlist.txt')

    libdict = parseIntoBooks('newlist.txt')
    for author in libdict.keys():
        for x in libdict[author]:
            book = x
            pages = libdict[author][book]
            # import pdb; pdb.set_trace()
            bookClient(author, pages, book)

    pretty(libdict)


if __name__ == "__main__":
    main()





#
