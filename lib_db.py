from google.appengine.ext import db
import numpy as np

class Keywords(db.Model):

    data = db.StringListProperty()


class Article(db.Model):

    title = db.StringProperty()
    authors = db.StringListProperty()
    doi = db.StringProperty()
    abstract = db.TextProperty()
    institution = db.StringListProperty()
    volume = db.IntegerProperty()
    year = db.IntegerProperty()
    citedby = db.StringListProperty()
    keywords = db.StringListProperty()
    kw_prob = db.ListProperty(float)
    kw_ind = db.ListProperty(int)
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
    
    @property
    def kw_vector(self):

        kw_vec = np.zeros(len(Keywords.all().get()))

        kw_vec[self.kw_ind] = self.kw_prob

        return kw_vec

        
        
