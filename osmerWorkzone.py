####
#osmerWorkzone
####
_version="1.0"

import xml.etree.ElementTree as ET
import requests
import sqlite3
import os.path
import argparse
import urllib.parse
from openlocationcode import openlocationcode as olc
from sqlite3 import Error
from urllib.request import pathname2url
from lib.geoMath import getDistance
from lib.geoMath import getMidpoint


def printNode(id,lat,lon):
    print('<node id="{}" lat="{}" lon="{}">'.format(id,lat,lon))
    print('</node>')


parser = argparse.ArgumentParser(description='Retrieves latest user work zone based on last changesets') #,usage='%(prog)s [options] path'
parser.add_argument('username', type=str, help='OSM username')
parser.add_argument('--nchangesets', type=int, help='number of changesets to process (default 100, max 1000)')
parser.add_argument('--verbose', action='store_true', help='verbose output')
parser.add_argument('--maxarea', type=int, help='skip changeset with bbox area greater than this value in km2')
parser.add_argument('--osm', action='store_true', help='outputs an OSM file')
options = parser.parse_args()

username = urllib.parse.quote(options.username)
if options.nchangesets==None:
    csToProcess=100
else:
    csToProcess=min(options.nchangesets,1000)

if options.maxarea==None:
    csMaxArea=510100000 #area of earth
else:
    csMaxArea=options.maxarea

if options.verbose:
    fVerbose=True
else:
    fVerbose=False

if options.osm:
    fOSM=True
else:
    fOSM=False

getHeaders={"User-Agent":"osmerWorkzone.py/%s" % _version}
dbName='places.db'
fDebug=False

if fDebug:
    CSTree = ET.parse('d:\\josm\\amchangesets.xml')
    root = CSTree.getroot()
else:

    usersCS = requests.get("https://api.openstreetmap.org/api/0.6/changesets?display_name=%s" % username,headers=getHeaders)
    
    if usersCS.status_code==200:
        root=ET.fromstring(usersCS.content)
    else:
        print("Cannot find user %s" % username)
        exit()

nodeid=-1
zones={}
ignore_hashtags = ["#osmitaly-", "#hotosm-project-"]

dbPresence=os.path.isfile(dbName)

sqlDB=sqlite3.connect('places.db')

cur = sqlDB.cursor()
if not dbPresence:
    if fVerbose:
        print("Creating places.db")
    cur.execute('''CREATE TABLE places (olc text, place text)''')
    sqlDB.commit()

if fVerbose:
    print("Opening places.db")

csProcessed=0
nCS=0
fExit=False

while csProcessed<csToProcess and not fExit:
    fExit=False
    nCS=0

    for changeset in root:
        fSkip = False
        nCS+=1
                
        for tag in changeset:
            if tag.attrib['k'] == 'hashtags':
                hashtags = tag.attrib['v'].split(";")
                if fDebug:
                    print("hashtags: ",hashtags)
                matching = [s for s in hashtags if any(xs in s for xs in ignore_hashtags)]
                if len(matching) > 0 :
                    fSkip=True
        
        csId=changeset.attrib['id']

        if fVerbose:
            if fSkip:
                print("Skipping changeset %s" % csId)

        changes=int(changeset.attrib['changes_count'])
        created=changeset.attrib['created_at']

        if changes!=0 and not fSkip:
            minLat=float(changeset.attrib['min_lat'])
            minLon=float(changeset.attrib['min_lon'])
            maxLat=float(changeset.attrib['max_lat'])
            maxLon=float(changeset.attrib['max_lon'])
            
            csHeight=getDistance(minLat,minLon,maxLat,minLon)
            csWidth=getDistance(minLat,minLon,minLat,maxLon)
            csArea=csHeight*csWidth/1000000

            if csArea<csMaxArea and csArea>0:
                if fVerbose:
                    print("changeset id={} area={:.2f} km2".format(csId,csArea))

                currentCenterLat,currentCenterLon=getMidpoint(minLat,minLon,maxLat,maxLon)
                
                tolc=olc.encode(currentCenterLat,currentCenterLon,6)

                cValue=zones.get(tolc)

                if cValue==None:
                    zones[tolc]=1
                else:
                    zones[tolc]=cValue+1
                
                csProcessed+=1
            else:
                if fVerbose:
                    print("Skipping changeset {} area={:.2f}>{}".format(csId,csArea,csMaxArea))

        if csProcessed==csToProcess:
            break
    
    if csProcessed<csToProcess and nCS==100:
        usersCS = requests.get("https://api.openstreetmap.org/api/0.6/changesets?display_name=%s&time=2013-05-12T00:00:00Z,%s" % (username,created),headers=getHeaders)
        root=ET.fromstring(usersCS.content)
    else:
        fExit=True

if fVerbose:
    print("Processed %i changesets" % csProcessed)

sortedZones={k: v for k,v in sorted(zones.items(), key=lambda item: item[1], reverse=True)}

#print(x)
nodeid=-1

tolc=list(sortedZones)[0]
box=olc.decode(tolc)

rowPlace=cur.execute("SELECT place FROM places WHERE olc='{}'".format(tolc)).fetchone()
if rowPlace==None:
    if fVerbose:
        print("Zone %s not in DB searching nominatim" % tolc)
    reverseURL="https://nominatim.openstreetmap.org/reverse.php?lat={:.5f}&lon={:.5f}&zoom=10&format=xml".format(box.latitudeCenter,box.longitudeCenter)
    #reverseXML=open('d:\\dev\\python\\osmerWorkzone\\test\\nominatim.xml').read()

    reverseXML = requests.get(reverseURL,headers={"User-Agent": "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"})

    text=reverseXML.text
    text=text.replace("&","&#38;")
    root=ET.fromstring(text)

    place=""
    province=""

    for addrParts in root.findall(".//addressparts/*"):
        if addrParts.tag=="city" or addrParts.tag=="village" or addrParts.tag=="town" or addrParts.tag=="place":
            place=addrParts.text
        if addrParts.tag=="province" or addrParts.tag=="county":
            province=addrParts.text
    
    if place=="":
        fullPlace=province
    else:
        if province=="":
            fullPlace=place
        else:
            fullPlace="{}, {}".format(place,province)

    cur.execute("INSERT INTO places VALUES ('{}','{}')".format(tolc,fullPlace))
    sqlDB.commit()
else:
    if fVerbose:
        print("Zone %s present in DB" % tolc)
    fullPlace=rowPlace[0]

if fVerbose:
        print("Decoded zone: %s" % fullPlace)

sqlDB.close()

if fOSM:
    print('<osm version="0.6" generator="OsmAnd">')
    printNode(-1,box.latitudeLo,box.longitudeLo)
    printNode(-2,box.latitudeLo,box.longitudeHi)
    printNode(-3,box.latitudeHi,box.longitudeHi)
    printNode(-4,box.latitudeHi,box.longitudeLo)


    print('<way id="-5">')
    print('<nd ref="-1" />')
    print('<nd ref="-2" />')
    print('<nd ref="-3" />')
    print('<nd ref="-4" />')
    print('<nd ref="-1" />')
    print('<tag k="landuse" v="commercial" />')
    print('<tag k="name" v="{}" />'.format(fullPlace))
    print('</way>')

    print('</osm>')
else:
    print(fullPlace)
