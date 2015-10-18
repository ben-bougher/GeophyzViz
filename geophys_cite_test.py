import json
import geophys_paper as gp
import os

#infile = './data/geophysics_70-79.json'
infile = './data/geophysics_hack.json'

with open(infile, 'r') as f:
    data = json.loads(f.read())

papers = []
for d in data:
    papers.append(gp.Paper(d))

print(papers[10]._citedby[1])
