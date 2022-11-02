import overpy
import html
import urllib.request
import argparse
import os
from lxml import objectify

_version="1.0"

def AddChangesetID(id):
	if id not in changesetIds: changesetIds.append(id)
	
parser = argparse.ArgumentParser(description='Retrieves a list of users that modified OSM data. OSM data is obtained through an Overpass API query')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--q', nargs=1, help='Specify the Overpass QL query in command line')
group.add_argument('--f', nargs=1, help='Reads the Overpass QL query from a file')

options = parser.parse_args()

if options.q!=None:
    overpassQry=options.q[0]
else:
	infile=options.f[0]
	if os.path.isfile(infile)==False:
		print("Cannot open %s" % infile )
		exit(1)
	else:
		fin=open(infile)
		overpassQry=fin.read()
		fin.close()

changesetIds=[]
fDebug=False
w=0
n=0
r=0
baseAPIUrl="https://api.openstreetmap.org/api/0.6/changeset/"

api = overpy.Overpass()
try:
	result = api.query(overpassQry)
except Exception as err:
	print(html.unescape(str(err)))
	quit()

if fDebug: print("Parsing ways")
for way in result.ways:
	AddChangesetID(way.attributes.get("changeset", "0"))
	w+=1
if fDebug: print("%s ways parsed" % w)	
if fDebug: print("Parsing nodes")
for node in result.nodes:
	AddChangesetID(node.attributes.get("changeset", "0"))
	n+=1
if fDebug: print("%s nodes parsed" % n)
if fDebug: print("Parsing relations")
for relation in result.relations:
	AddChangesetID(relation.attributes.get("changeset", "0"))
	r+=1
if fDebug: print("%s relations parsed" % r)

print('ChangesetID,OSMUser,OSMUserId,Changes,ChangesetTags')
for x in changesetIds:
	if x != '0':
		tURL='{}{}'.format(baseAPIUrl,x)
		chResponse=urllib.request.urlopen(tURL)
		chXML=chResponse.read()
		root = objectify.fromstring(chXML)
		ch=root.changeset
		OSMUser=ch.attrib['user']
		OSMUserID=ch.attrib['uid']
		OSMChanges=ch.attrib['changes_count']
		OSMChTags=''
		for attr in ch.getchildren():
			tag=attr.values()[0]
			key=attr.values()[1]
			OSMChTags+=",{}='{}'".format(tag,key)
		OSMChTags='"'+OSMChTags[1:]+'"'
		print('%s,"%s",%s,%s,%s' % (x,OSMUser,OSMUserID,OSMChanges,OSMChTags))
		