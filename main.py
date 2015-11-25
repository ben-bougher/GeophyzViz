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
from lib_db import Article, Keywords

import json
from numpy.random import randint
import numpy as np


env = Environment(loader=FileSystemLoader(join(dirname(__file__),
                                               'templates')))


def KeywordScore(kqv, kv):

    s = (kqv.T).dot(kv)
    return s


def GetAuthorsFromCitation(citation):

    authors = set()
    for a in citation:
        for person in a['authors']:
            authors.add(person)
    return list(authors)


def AuthorScore(AuthorQuery, authors):
    s = 0.0
    for author in AuthorQuery.keys():
        if author in authors:
            s += AuthorQuery[author]
    return s


def CitationAuthorScore(AuthorQuery, citation):
    return AuthorScore(AuthorQuery, GetAuthorsFromCitation(citation))


def preprocess(KeywordsQuery, KeyWords):
    """
    Forms a query of keywords into a weighting vector
    """
    
    # query preprocessing
    for k in KeywordsQuery:
        KeywordsQuery[k.strip().lower()] = KeywordsQuery.pop(k)

    N_Keywords = len(KeyWords)
    kqv = np.zeros(N_Keywords)
    KQ = [k for k in KeywordsQuery.keys()]
    p = 0
        
    for kw in KeyWords:
        if kw in KQ: # if the input keyword is a recognized one
            kqv[p] = KeywordsQuery[kw]
        p += 1

    return kqv


def GenerateKeywords(curAbstract, curTitle, curKeywords, KeyWords):
    
    N_Keywords = len(KeyWords)
    kwv = []
    kw_ind = []
    extractedKW = set()
    p = -1
    for kw in KeyWords:
        p += 1
        if kw in curKeywords: # if the existing keyword is a recognized one
            extractedKW.add(kw)
            kwv.append(1.0)
            kw_ind.append(p)
            continue
        if kw in curAbstract.lower() and kw in curTitle.lower():
            extractedKW.add(kw)
            kwv.append(0.9)
            kw_ind.append(p)
            continue
        if kw in curAbstract.lower():
            extractedKW.add(kw)
            kwv.append(0.5)
            kw_ind.append(p)
            continue
        if kw in curTitle.lower():
            extractedKW.add(kw)
            kwv.append(0.8)
            kw_ind.append(p)
            continue
    return extractedKW, kwv, kw_ind


def LoadKeywordsFromFile(infile, kw=None):
    if not kw:
        KeyWords = set()
    else:
        KeyWords = kw

    f = open(infile, 'r')
    cnt = 0
    for line in f:
        if len(line) < 2:
            continue
        curKeyword = line
        if line[-1] == '\n':
            curKeyword = line[:-1]
        KeyWords.add(curKeyword.strip().lower())
        cnt += 1

    return KeyWords


class IndexHandler(webapp2.RequestHandler):

    def get(self):

        template = env.get_template('breakfast.html')
        
        html = template.render()

        self.response.write(html)


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

        AuthorQuery = self.request.get('authors')
        kqv = self.request.get('keywords')

        W0 = 2.0
        W1 = 1.0
        W2 = 0.5
        articles = Article.all().fetch(100000)
        scores = []
        for article in articles:
            authors = article.authors
            kv = article.kw_prob  # get the keyword vector
            citation = article.citedby
            score = (W0 * AuthorScore(AuthorQuery, authors) +
                     W1 * KeywordScore(kqv, kv) +
                     W2 * CitationAuthorScore(AuthorQuery, citation))
            scores.append(score)
        

        self.request.out.write('success')


class DataHandler(webapp2.RequestHandler):

    def get(self):

        self.response.headers['Content-Type'] = 'application/json'

        articles = Article.all().fetch(10)

        arts = []
        kw = []
        authors = []
        for art in articles:
            arts.append(art.json)
            kw += art.keywords
            authors += art.authors

        keywords = [kw[i] for i in randint(0, len(kw), 15)]
        authors = [authors[i] for i in randint(0, len(authors), 5)]
        keywords = list(set(keywords))
        authors = list(set(keywords))
        self.response.out.write(json.dumps({'keywords': keywords,
                                            'authors': authors,
                                            'suggestions': arts}))


class PopulateKeywordsHandler(webapp2.RequestHandler):

    def get(self):
        # Read in global keywords
        keywords = LoadKeywordsFromFile('data/SEG_Keywords.txt')
        keywords = LoadKeywordsFromFile('data/seg2015.json_keywords.txt',
                                        kw=keywords)

        # Populate the keywords in the db
        articles = Article.all().fetch(100000)
        for article in articles:

            if (article.title is None) or (article.abstract is None):
                continue
        
            new_kw, prob, ind = GenerateKeywords(article.abstract,
                                                 article.title,
                                                 article.keywords,
                                                 keywords)

            article.keywords = list(new_kw)
            article.kw_prob = prob
            article.kw_ind = ind
            article.put()

        Keywords(data=list(keywords)).put()
        
        self.response.out.write('worky worky')





class LoadDataHandler(webapp2.RequestHandler):

    def get(self):

        def parse(l, cast):
            try:
                return cast(l[0])
            except:
                return None
            
        infile = 'data/geophysics_hack_CLEAN.json'
        errors = []
        with open(infile, 'r') as f:
            for d in json.loads(f.read()):

                d['abstract'] = parse(d['abstract'], str)
                d['title'] = parse(d['title'], str)
                d['doi'] = parse(d['doi'], str)
                d['volume'] = parse(d['volume'], int)
                d['year'] = parse(d['year'], int)
                d['issue'] = parse(d['year'], int)
                d['citedby'] = GetAuthorsFromCitation(d['citedby'])

                try:
                    Article(**d).put()
                except Exception as e:
                    print e
                    errors.append(d)
                    
        self.response.out.write(json.dumps(errors))

app = webapp2.WSGIApplication([('/', IndexHandler),
                               ('/breakfast_learn', MainHandler),
                               ('/loaddata', LoadDataHandler),
                               ('/data', DataHandler),
                               ('/suggest', SuggestionHandler),
                               ('/keywords', PopulateKeywordsHandler)],
                              debug=False)


def main():

    run_wsgi_app(app)

if __name__ == "__main__":
    main()

