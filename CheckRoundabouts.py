####
#Checkroundabouts 1.0
####

import json
import sys

def SeekAndClear(wid,mnode):

    found=False

    for lobj in JSONdata['elements']:
        if lobj['type']=='way':
            lwid=lobj['id']
            lpos=len(lobj['nodes'])-1
            fnode=lobj['nodes'][0]
            lnode=lobj['nodes'][lpos]

            if lwid !=wid:
                if lnode==mnode:
                    found=True
                    lobj['nodes'][0]=-1
                    lobj['nodes'][lpos]=-1
                    if verbose: print('Id ', lwid, ' Clearing nodes', fnode, lnode)
                    if verbose: print('Seeking for fnode ', fnode)
                    SeekAndClear(lwid, fnode)
                    break
    if verbose: print('Found flag: ', found)
    return found

tsplit=0
tclosed=0
tnodes=0
tbroken=0
lbroken=''

if len(sys.argv)==1:
    print('CheckRoundabouts.py')
    print('Counts roundabouts in a json containing OSM data. Json file should contain ways and nodes already filtered for tag junction=roundabout\n')
    print('Usage')
    print('CheckRoundabouts.py jsonfile [-v]\n')
    print('-v\tVerbose output')
    quit()

try:
    mJSONFile=open(sys.argv[1])
except:
    print('Cannot open file')
    quit()

print('Opening ', sys.argv[1])
verbose=False

try:
    if sys.argv[2]=='-v':
        verbose=True
except:
    pass

with mJSONFile as json_file:
    try:
        JSONdata = json.load(json_file)
    except:
        print('Not a JSON file!')
        quit()

    print('Parsing JSON...')
    for mobj in JSONdata['elements']:
        if mobj['type'] == 'way':
            wid=mobj['id']
            lpos = len(mobj['nodes']) - 1
            fnode=mobj['nodes'][0]
            lnode=mobj['nodes'][lpos]
            if verbose: print('Checking ', wid, ' fnode ', fnode, ' lnode ', lnode)

            if fnode==lnode:
                if fnode!=-1:
                    tclosed+=1
                    mobj['nodes'][0]=-1
                    mobj['nodes'][lpos]=-1
            else:
                if fnode!=-1:
                    found=SeekAndClear(wid,fnode)

                if found:
                    tsplit+= 1
                else:
                    if verbose: print('Broken ',wid,fnode)
                    lbroken+=str(wid)+','
                    tbroken+=1

        if mobj['type'] == 'node':
            try:
                tags=mobj['tags']
                if 'junction' in tags:
                    tnodes+=1
            except:
                pass

print('Split into several ways\t',tsplit)
print ('Single closed way\t',tclosed)
print ('Single nodes with tag\t',tnodes)
print ('TOTAL\t\t\t',tsplit+tclosed+tnodes)
if tbroken>0:
    lbroken=lbroken[:-1]
    print ('\nFound',tbroken,'broken roundabouts (split into several ways but with open end). Ways:',lbroken)
