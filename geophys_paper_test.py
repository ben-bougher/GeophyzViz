import json
import geophys_paper as gp
import os

#infile = './data/geophysics_70-79.json'
infile = './data/seg2015.json'

with open(infile, 'r') as f:
    data = json.loads(f.read())

papers = []
for d in data:
    papers.append(gp.Paper(d))

papers[10].print_paper()
print(type(papers))
print(type(papers[0]))
print((papers[0].get_keywords()))
print((papers[0].get_keywords()[0]))
print()

keywords_2015 = set()
for art in papers:
    #print(art.get_keywords())
    for keys in art.get_keywords():
        keywords_2015.add(keys)

keywords_2015 = list(keywords_2015)
keywords_2015.sort()
print(keywords_2015)

# write the keywords to file
f = open(infile + "_keywords", "wt")
for ele in keywords_2015:
    f.write(ele + "\n")
f.close()
