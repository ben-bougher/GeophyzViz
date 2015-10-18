from google.appengine.ext import db


class Article(db.Model):

    title = db.StringProperty()
    authors = db.StringListProperty()
    doi = db.StringProperty()
    abstract = db.TextProperty()
    institution = db.StringListProperty()
    volume = db.IntegerProperty()
    year = db.IntegerProperty()
    keywords = db.StringListProperty()
    kw_prob = db.ListProperty
    issue = db.IntegerProperty()
    
    @property
    def json(self):

        return {"title": self.title,
                "authors": self.authors,
                "doi": self.doi,
                "abstract": self.abstract,
                "institution": self.institution,
                "volume": self.volume,
                "year": self.year,
                "keywords": self.keywords,
                "issue": self.issue}
    
