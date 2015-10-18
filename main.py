#!/usr/bin/env python
# -*- coding: utf-8 -*-
# modelr web app
# Agile Geoscience
# 2012-2014
#

from google.appengine.ext import webapp as webapp2
from google.appengine.ext.webapp.util import run_wsgi_app
from jinja2 import Environment, FileSystemLoader
from os.path import dirname, join
from lib_db import Article
import json
from numpy.random import randint
import numpy as np


env = Environment(loader=FileSystemLoader(join(dirname(__file__),
                                            'templates')))


def GenerateKeywords(curAbstract, curTitle, curKeywords):
    N_Keywords = len(KeyWords)        
    kwv = np.zeros(N_Keywords)
    extractedKW=set()
    p=-1
    for kw in KeyWords:
        p+=1
        if kw in curKeywords: #if the existing keyword is a recognized one
            extractedKW.add(kw)
            kwv[p]=1.0
            continue
        if kw in curAbstract.lower() and kw in curTitle.lower():
            extractedKW.add(kw)
            kwv[p]=0.9
            continue
        if kw in curAbstract.lower():
            extractedKW.add(kw)
            kwv[p]=0.5
            continue
        if kw in curTitle.lower():
            extractedKW.add(kw)
            kwv[p]=0.8
            continue
    return extractedKW, kwv



def LoadKeywordsFromFile(infile, kw=None):
    if not kw:
        KeyWords = set()
    else:
        KeyWords = kw
    
    f = open(infile,'r')
    cnt = 0
    for line in f:
        if len(line)<2:
            continue
        curKeyword = line
        if line[-1]=='\n':
            curKeyword = line[:-1]
        KeyWords.add(curKeyword.strip().lower())
        cnt+=1

    return KeyWords


class MainHandler(webapp2.RequestHandler):

    def get(self):

        template = env.get_template('index.html')

        with open('trash.b64', 'r') as f:

            image64 = f.read()
        
        html = template.render(image=image64)

        self.response.write(html)


class SuggestionHandler(webapp2.RequestHandler):

    def get(self):

        self.response.headers['Content-Type'] = 'application/json'
        articles = Article.all().fetch(10, offset=randint(0, 1000))

        titles = []

        for article in articles:
            titles.append(article.title)

        self.response.out.write(json.dumps(titles))


class DataHandler(webapp2.RequestHandler):

    def get(self):

        self.response.headers['Content-Type'] = 'application/json'
        
        #author = self.request.get('author')
        
        articles = Article.all().fetch(10)

        authors = []
        titles = []
        
        for art in articles:
            authors += art.authors
            titles.append(art.title)
            
        self.response.out.write(json.dumps({'authors': authors,
                                            'titles': titles}))


class PopulateKeywordsHandler(webapp2.RequestHandler):

    # Read in global keywords
    keywords = LoadKeywordsFromFile('data/SEG_Keywords.txt')
    keywords = LoadKeywordsFromFile('data/seg2015.json_keywords.txt',
                                    kw=keywords)

    # Populate the keywords in the db
    articles = Article.all().fetch(10)
    for article in articles:

        new_kw, prob = GenerateKeywords(article.abstract, article.title,
                                        article.keywords)

        print new_kw, prob
        #article.keywords = new_kw
        #article.kw_prob = prob

        #print article.keywords
        #article.put()

    
class LoadDataHandler(webapp2.RequestHandler):

    def get(self):

        def parse(l, cast):
            try:
                return cast(l[0])
            except:
                return None
            
        infile = 'data/geophysics_70-79.json'
        errors = []
        with open(infile, 'r') as f:
            for d in json.loads(f.read()):

                d['abstract'] = parse(d['abstract'], str)
                d['title'] = parse(d['title'], str)
                d['doi'] = parse(d['doi'], str)
                d['volume'] = parse(d['volume'], int)
                d['year'] = parse(d['year'], int)
                d['issue'] = parse(d['year'], int)

                try:
                    Article(**d).put()
                except Exception as e:
                    print e
                    errors.append(d)
                    
        self.response.out.write(json.dumps(errors))

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/loaddata', LoadDataHandler),
                               ('/data', DataHandler),
                               ('/titles', SuggestionHandler),
                               ('/keywords', PopulateKeywordsHandler)],
                              debug=False)


def main():

    run_wsgi_app(app)

if __name__ == "__main__":
    main()
