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

env = Environment(loader=FileSystemLoader(join(dirname(__file__),
                                            'templates')))


class MainHandler(webapp2.RequestHandler):

    def get(self):

        template = env.get_template('index.html')
        html = template.render()

        self.response.write(html)


class DataHandler(webapp2.RequestHandler):

    def get(self):

        self.response.headers['Content-Type'] = 'application/json'
        
        author = self.request.get('author')
        
        articles = Article.all().filter("authors =", author).fetch(10000)

        self.response.out.write(json.dumps([i.json for i in articles]))

        
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
                               ('/data', DataHandler)],
                              debug=False)


def main():

    run_wsgi_app(app)

if __name__ == "__main__":
    main()
