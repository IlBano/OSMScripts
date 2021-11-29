####
#CheckHouseNumbers
####
_version="0.91"

import json
import sys

# function for correctly sorting housenumber when using sort function
def getSortKey(item):
    x=item[5].zfill(10)
    return x

# get way index from wayNames list or creates one in case it's not present
def getWay(street):
    x=-1
    for n in range(0,len(wayNames)):
        if wayNames[n]==street:
            x=n
    if x==-1:
        wayNames.append(street)
        wayNodes.append([])
    return x

# updates way nodes
def updateWay(street,hnumber,id,lat,lon):
    x=getWay(street)

    #extracts base number without suffixes
    for i in range(0,len(hnumber)):
        if hnumber[i].isdigit() == False:
            i-=1
            break
    i+=1
    temphn=hnumber[:i]
    
    # determines if housenumber is odd or even
    hn=int(temphn) % 2
    wayNodes[x].append((hnumber,id,lat,lon,hn,temphn))

# load nodes from JSON file
def loadData():
    
    for item in JSONdata['elements']:
        if item['type']=='node':
            try:
                addrStreet=item['tags']['addr:street']
            except:
                addrStreet="Unknown way"

            updateWay(addrStreet,item['tags']['addr:housenumber'],item['id'],item['lat'],item['lon'])


# check command line arguments
if len(sys.argv)==0:
    print('CheckHouseNumbers.py',_version)
    print('Starting from a JSON containing addr:housenumber nodes generates an OSM file with ways (2 for each highway name - odd numbers and even numbers) composed by those nodes sorted.')
    print('This OSM file can be opened in JOSM to get a visual aid for housenumbers QA/cleanup activities.\n')
    print('Usage')
    print('CheckHouseNumbers.py jsonfile [-nooddeven]\n')
    print('-nooddeven\tgenerates only 1 way per highway name with all housenumbers')
    quit()

fOddeven=True

for c in range(2,len(sys.argv)):
    tArg=sys.argv[c]
    if tArg=='-nooddeven':
        fOddeven=False
    else:
        #print("Ignoring argument",tArg)
        pass


try:
    fname=sys.argv[1]
    #fname='D:\\dev\\Python\\CheckHouseNumbers\\pezzana.json'
    mJSONFile=open(fname)
    
except:
    print('Cannot open file')
    quit()

# is it a real json ?
with mJSONFile as json_file:
    try:
        JSONdata = json.load(json_file)
    except:
        print('Not a JSON file!')
        quit()
    
    exFile = open(fname+".ex.txt","w")
    exFile.write("Exceptions\n")


    # declare lists
    wayNames=[]
    wayNodes=[]

    # load nodes and ways
    loadData()

    # .osm file preamble
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<osm version="0.6" generator="CheckHouseNumbers.py" upload="never">')

    # outputs all nodes
    for n in range(0,len(wayNodes)):
        wname=wayNames[n]
        wayNodes[n].sort(key=getSortKey)
        ntemp=wayNodes[n]
        for m in range(0,len(ntemp)):
            print('  <node id="',ntemp[m][1],'" lat="',ntemp[m][2],'" lon="',ntemp[m][3],'" version="10">',sep='')
            print('    <tag k="addr:housenumber" v="',ntemp[m][0],'"/>',sep='')
            print('    <tag k="addr:street" v="',wname,'"/>',sep='')
            
            
            if m<(len(ntemp)-1):
                chn=ntemp[m][5]
                nhn=ntemp[m+1][5]
                if int(nhn) > int(chn)+1:
                    exFile.write("way: "+wname+" missing "+str(int(chn)+1))
                    if int(nhn)-1 > int(chn)+1:
                        exFile.write("-"+str(int(nhn)-1))
                    exFile.write("\n")
         
            print('  </node>')

    # outputs all ways
    wid=-1
    for n in range(0,len(wayNames)):
        wname=wayNames[n]
        ntemp=wayNodes[n]
        if fOddeven:
            # cycle through even and odd numbers
            for p in range(0,2):
                
                if p==0:
                    wext="-even"
                    twid=wid
                else:
                    wext="-odd"
                    twid=wid-10000000000
                
                print('  <way id="',twid,'">',sep='')

                for m in range(0,len(ntemp)):
                    if ntemp[m][4]==p:
                        print('    <nd ref="',ntemp[m][1],'"/>',sep='')
                
                # here we use pedestrian key, but can be changed to whatever one likes
                # oneway=yes tag helps the visual representation
                print('    <tag k="highway" v="pedestrian"/>')
                print('    <tag k="name" v="',wname+wext,'"/>',sep='')
                print('    <tag k="oneway" v="yes"/>')
                print('  </way>')
            wid=wid-1
        else:
            print('  <way id="',wid,'">',sep='')
           
            for m in range(0,len(ntemp)):
                print('    <nd ref="',ntemp[m][1],'"/>',sep='')
        
            print('    <tag k="highway" v="pedestrian"/>')
            print('    <tag k="name" v="',wname,'"/>',sep='')
            print('    <tag k="oneway" v="yes"/>')
            print('  </way>')
            wid=wid-1

    print('</osm>')
    exFile.close()


    