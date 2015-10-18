
class Paper(object):
    def __init__(self, object):
        """ creates object elements"""
        self._abstract = object[u"abstract"]
        self._authors = object[u"authors"]
        self._doi = object[u"doi"]
        self._institution= object[u"institution"]
        self._keywords= object[u"keywords"]
        self._title= object[u"title"]

        #self._references
        #self._citedby

        self.clean()
        # checks for year
        

    def clean_authors(self):
        authors = self._authors
        cleaned = []
        for uni in authors:
            temp = str(uni.encode('ascii', 'replace'))
            n = len(temp)-1
            if(temp[n]=='*'):
                temp = temp[0:n]
            cleaned.append(temp)
        return cleaned

    def clean_title(self):
        title = self._title
        cleaned = ""
        for uni in title:
            cleaned = cleaned + str(uni.encode('ascii','replace'))
        return cleaned

    def clean_keywords(self):
        keywords = self._keywords
        cleaned = []
        for uni in keywords:
            cleaned.append(str(uni.encode('ascii','replace')))
        return cleaned

    def clean_doi(self):
        doi = self._doi
        cleaned = ""
        for uni in doi:
            cleaned = cleaned + str(uni.encode('ascii','replace'))
        return cleaned

    def clean_institution(self):
        inst = self._institution
        cleaned = []
        for uni in inst:
            cleaned.append(str(uni.encode('ascii','replace')))
        return cleaned

    def clean_abstract(self):
        abstract = self._abstract
        cleaned = ""
        for uni in abstract:
            cleaned = cleaned + str(uni.encode('ascii','replace'))
        return cleaned

    def clean_issue(self):
        issue = self._issue
        cleaned = int(issue.encode('ascii','replace'))
        return cleaned

    def clean_year(self):
        year = self._year
        cleaned = int(year.encode('ascii','replace'))
        return cleaned

    def clean_volume(self):
        volume = self._volume
        cleaned = int(volume.encode('ascii','replace'))
        return cleaned

    def clean(self): 
        """take out u' and ' """
        self._authors = self.clean_authors()
        self._title = self.clean_title()
        self._keywords = self.clean_keywords()
        self._abstract = self.clean_abstract()
        self._institution = self.clean_institution()
        self._doi = self.clean_doi()
        #self._issue = self.clean_issue()
        #self._year = self.clean_year()
        #self._volume = self.clean_volume()
        
    def print_paper(self):
        print(self.get_doi())
        print(self.get_title())
        print(self.get_authors())
        print(self.get_institution())
        print(self.get_keywords())
        print(self.get_abstract())
    
    def get_abstract(self):
        """returns _abstract"""
        return str(self._abstract)
    
    def get_authors(self):
        """returns _author"""
        return (self._authors)
    
    def get_doi(self):
        """returns _doi"""
        return str(self._doi)
  
    def get_institution(self):
        """returns _institution"""
        return (self._institution)
    
    def get_keywords(self):
        """returns _key_words"""
        return (self._keywords)
    
    def get_title(self):
        """returns _title"""
        return str(self._title)

    def have_abstract(self, string):
        """no need for a have abstract?????"""
        if string == get_abstract():
            return True
        else:
            return False

    def have_authors(self, author_question):
        """does it have this author"""
        list_authors = get_authors()
        for author in list_authors:
            if author_question == author:
                return True
        return False

    def have_institution(self, string):
        """does it have this author"""
        list_institution = get_institution()
        for institution in list_institution:
            if string == institution:
                return True
        return False        
    
    def have_keyword(self, string):
        """does it have this keyword"""
        list_keywords = get_keywords()
        for keyword in list_keywords:
            if string == keyword:
                return True
        return False
        
    def have_title(self, string):
        """does it have this title"""
        if string == get_title():
                return True
        return False
 
