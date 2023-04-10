####
#GetOSMComments
####
_version="0.2"

import argparse
import xml.etree.ElementTree as ET
import time

parser = argparse.ArgumentParser(description='Get changeset comments of specified users from an OSM discussions dump. Writes output (changeset id, user, comment date and comment) in a csv file')
parser.add_argument('usernames', type=str, help='comma separated list of OSM usernames')
parser.add_argument('discussionfile', type=str, help='OSM discussion dump obtained from planet.osm.org. N.B. must be already in .osm format')
parser.add_argument('outfile', type=str, help='csv output file')
options = parser.parse_args()

# Get an iterable object
discussions = ET.iterparse(options.discussionfile, events=("start", "end"))

# create output file and CSV header
outFile = open(options.outfile,"w",encoding="utf-8")
outFile.write("changesetId;user;commentDate;comment\n")

usersToSearch=options.usernames.split(",")
csCount=0

fSkipUser=False
tic = time.perf_counter()
for index, (event, elem) in enumerate(discussions):
    # Get the root element.
    if index == 0:
        root = elem
    x=elem.tag
    if event == "start":
        if x=="changeset":
            csCount+=1
            if csCount % 10e4 == 0:
                print(f"Parsed {csCount/10e5:4.1f} M changesets")
            csId=elem.attrib["id"]

        if x=="comment":
            tuser=elem.attrib["user"]
            tdate=elem.attrib["date"]
            fSkipUser=False
            if tuser not in usersToSearch:
                fSkipUser=True
        
        if x=="text" and not fSkipUser:
            if elem.text != None:
                comment=elem.text.replace("\n","\\n")
                outFile.write('{};{};{};"{}"\n'.format(csId,tuser,tdate,comment))
    root.clear()

outFile.close()
d=time.perf_counter()-tic
print(f"Parsed a total of {csCount} changesets in {d:4.2f} s")