import json
import geophys_paper as gp
import os
from collections import OrderedDict


infile = './data/geophysics_70-79.json'
#infile = './data/seg2015.json'

with open(infile, 'r') as f:
    data = json.loads(f.read())

papers = []
for d in data:
    papers.append(gp.Paper(d))

authors_2015_list = list()
authors_2015_set = set()
for art in papers:
    #print(art.get_keywords())
    for auth in art.get_authors():
        authors_2015_list.append(auth)
        authors_2015_set.add(auth)

#authors_2015_set.sort()
authors_2015_list.sort()
print(authors_2015_set)

d = dict()
for auth in authors_2015_set:
    d[auth] = authors_2015_list.count(auth)

auth_dict = OrderedDict(sorted(d.items(), key=lambda t: t[1]))

print(auth_dict)
# write the keywords to file
#f = open(infile + "_keywords", "wt")
#for ele in keywords_2015:
#    f.write(ele + "\n")
#f.close()
