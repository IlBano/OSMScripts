####
#NodeDensity
####
_version="0.8 beta"

import math
import json
import sys

# value in degrees under which a way is considered straight
straightAngle=8

# Get node lat/lon from nodes list
def getNode(id):
    for item in nodes:
        if item[0]==id:
            return [item[1],item[2]]
    return None

# Get distance between two point using "Spherical law of cosines" https://mathworld.wolfram.com/SphericalTrigonometry.html
# This method is 30% faster that haversine
def getDistance(pLat,pLon,cLat,cLon):
    x=math.acos(math.cos(math.radians(90-pLat))*math.cos(math.radians(90-cLat))+math.sin(math.radians(90-pLat))*math.sin(math.radians(90-cLat))*math.cos(math.radians(pLon-cLon))) *6371*1000
    return x

# Get distance between two point using "Haversine" formula https://en.wikipedia.org/wiki/Haversine_formula
def getDistance2(pLat,pLon,cLat,cLon):
    R = 6371*1000
    lat1=math.radians(pLat)
    lat2=math.radians(cLat)
    lon1=math.radians(pLon)
    lon2=math.radians(cLon)
    deltaLat=(lat2-lat1)
    deltaLon=(lon2-lon1)
    a=math.sin(deltaLat/2)*math.sin(deltaLat/2)+math.cos(lat1)*math.cos(lat2)*math.sin(deltaLon/2)*math.sin(deltaLon/2)
    c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))
    return R*c

# Calculate bearing of segment (see http://www.movable-type.co.uk/scripts/latlong.html)
# In general the heading will vary following a great circle path (orthodrome); the final heading will differ from the initial heading 
# by varying degrees according to distance and latitude (from 35°N,45°E (≈ Baghdad) to 35°N,135°E (≈ Osaka), you would start on a heading
# of 60° and end up on a heading of 120°)
# This formula is for the initial bearing (sometimes referred to as forward azimuth), but applied to short distances it will well
# approximate the real bearing
# Since atan2 returns values in the range -π ... +π, to normalise the result to a compass bearing (in the range 0° ... 360°)
# the result is converted to degrees and then the formula (θ+360) % 360 is used

def getBearing(pLat,pLon,cLat,cLon):
    ax=math.cos(math.radians(pLat))*math.sin(math.radians(cLat))-math.sin(math.radians(pLat))*math.cos(math.radians(cLat))*math.cos(math.radians(cLon)-math.radians(pLon))
    ay=math.sin(math.radians(cLon)-math.radians(pLon))*math.cos(math.radians(cLat))
    x=math.atan2(ay,ax)
    x=math.degrees(x)
    x=(x+360)%360
    
    return x

# Simple function to determine curve direction
def getSign(a):
    if a>0:
        x=1
    else:
        x=-1
    return x

# Calculate Node Density of curves
def CurveNodeDensity(nodes,meters,angle):
    mx=meters/nodes
    ax=angle/nodes
    cx=mx*ax
    nd=abs(1/cx*100)

    return nd

# Calculate Node Density of straight segments. N.B. this value cannot be compared with curve ND
def StraightNodeDensity(nodes,meters):
    mx=meters/nodes
    nd=1/mx*100

    return nd

# Parses a way by identifying curves and straights

def parseWay(wayId,wayNodes):
    
    # previous node values of lat/lon
    pLat=0
    pLon=0

    # current node values of lat/lon
    cLat=0
    cLon=0

    # previous and current values of segment bearing
    cBearing=0
    pBearing=0

    # the direction of a curve -1=left, 1=right
    curveDirection=0

    # are we on a straight?
    fStraight=False

    # Current curve and straight meters
    tCurveMeters=0
    tStraightMeters=0

    # total meters of way
    gtMeters=0
    
    # Current curve angle
    tAngle=0
    
    # Current curve and straight number of nodes
    tCurveNodes=0
    tStraightNodes=1
    
    # Sum of all straight and curve ND of the way
    tStraightND=0
    tCurveND=0
    
    # number of straight and curves of the way
    tStraightNDCount=0
    tCurveNDCount=0

    #if the ways has less than 2 nodes (if they ever exist) we exit 
    if len(wayNodes)<=1:
        return
    

    isClosed=False
    
    # if first and last node are equal then we have a closed way
    if wayNodes[0]==wayNodes[len(wayNodes)-1]: isClosed=True
    
    if not fCSV: print("Processing way:",wayId," isClosed=",isClosed," # nodes: ",len(wayNodes),sep='')
    
    # main cycle to analyze all nodes of the way
    for n in range(0,len(wayNodes)):
        
        if fDebug: print('Processing node: ',wayNodes[n])
        
        # get current lat/lon of node
        cLat,cLon=getNode(wayNodes[n])
        
        # check if we have a previous set of lat/lon value. In the negative case we cannot yet calculate distance
        if pLat!=0:
            distance=getDistance(pLat,pLon,cLat,cLon)

            if fDebug: distance2=getDistance2(pLat,pLon,cLat,cLon)
            gtMeters=gtMeters+distance

            if fDebug: print("distance SLC :",distance,"distance haversine :",distance2)

            # calculate current bearing
            cBearing=getBearing(pLat,pLon,cLat,cLon)
            
            # check if we have a previous bearing value. In the negative case we cannot yet calculate the angle between the two segments
            if pBearing!=0:
                angle=cBearing-pBearing
                #CHECK PENDING if abs(angle)>straightAngle or curveDirection!=0:
                # if the angle is above straightAngle we have a curve
                if abs(angle)>straightAngle:
                    # check if the curve is starting
                    if curveDirection==0:
                        curveDirection=getSign(angle)
                        tCurveMeters=distance
                        tAngle=angle
                        tCurveNodes=1
                        # check if before we had a straight
                        if fStraight:
                            nd=StraightNodeDensity(tStraightNodes+1,tStraightMeters)
                            tStraightND=tStraightND+nd
                            tStraightNDCount=tStraightNDCount+1
                            if fDebug: print("Straight ends",tStraightMeters,nd)
                            if fVerbose: print("\tStraight ",'{:.2f}'.format(tStraightMeters),"m ND=",'{:.3f}'.format(nd),sep='')
                            tStraightNodes=1
                            tStraightMeters=0
                            fStraight=False
                        if fDebug: print("Curve begins",angle)
                    # here we enter if the curve in ending or changing direction
                    else:
                        # if the direction is the same the curve continues
                        if getSign(angle)==curveDirection:
                            tCurveMeters=tCurveMeters+distance
                            tAngle=tAngle+angle
                            tCurveNodes=tCurveNodes+1
                            if fDebug: print("Curve continues",angle)
                        # otherwise it changes direction
                        else:
                            nd=CurveNodeDensity(tCurveNodes,tCurveMeters,tAngle)
                            tCurveND=tCurveND+nd
                            tCurveNDCount=tCurveNDCount+1
                            if fDebug: print("Curve changes",angle,tCurveMeters,tAngle,nd)
                            if fVerbose: print("\tCurve ",'{:.2f}'.format(tAngle),"° ",'{:.2f}'.format(tCurveMeters),"m ND=",'{:.4f}'.format(nd),sep='')
                            tCurveMeters=distance
                            tAngle=angle
                            tCurveNodes=1
                            curveDirection=getSign(angle)
                # we enter here if we have a straight
                else:
                    # check if we have a curve to "close"
                    if curveDirection!=0:
                        nd=CurveNodeDensity(tCurveNodes,tCurveMeters,tAngle)
                        tCurveND=tCurveND+nd
                        tCurveNDCount=tCurveNDCount+1
                        if fDebug: print("Curve ends1",angle,tCurveMeters,tAngle,nd)
                        if fVerbose: print("\tCurve ",'{:.2f}'.format(tAngle),"° ",'{:.2f}'.format(tCurveMeters),"m ND=",'{:.4f}'.format(nd),sep='')
                        tCurveMeters=0
                        tAngle=0
                        tCurveNodes=0
                        curveDirection=0
                    else:
                        if fDebug: print("Straight",angle)
                        fStraight=True
                        tStraightNodes=tStraightNodes+1
                        tStraightMeters=tStraightMeters+distance
                        curveDirection=0
            pBearing=cBearing
            if not fStraight:
                tStraightMeters=distance
        pLat=cLat
        pLon=cLon

    # report data about a straight
    if fStraight:
        nd=StraightNodeDensity(tStraightNodes+1,tStraightMeters)
        tStraightND=tStraightND+nd
        tStraightNDCount=tStraightNDCount+1
        if fDebug: print("Straight ends",tStraightMeters,nd)
        if fVerbose: print("\tStraight ",'{:.2f}'.format(tStraightMeters),"m ND=",'{:.3f}'.format(StraightNodeDensity(tStraightNodes+1,tStraightMeters)),sep='')

    # report data about a curve
    if curveDirection!=0:
        nd=CurveNodeDensity(tCurveNodes,tCurveMeters,tAngle)
        tCurveND=tCurveND+nd
        tCurveNDCount=tCurveNDCount+1
        if fDebug: print("Curve ends2",angle,tCurveMeters,tAngle,nd)
        if fVerbose: print("\tCurve ",'{:.2f}'.format(tAngle),"° ",'{:.2f}'.format(tCurveMeters),"m ND=",'{:.3f}'.format(CurveNodeDensity(tCurveNodes,tCurveMeters,tAngle)),sep='')
    
    # calculate average ND for both straight and curve values
    avgStraight=0
    avgCurve=0

    if tStraightNDCount!=0:
        avgStraight=tStraightND/tStraightNDCount

    if tCurveNDCount!=0:
        avgCurve=tCurveND/tCurveNDCount

    if fCSV:
        # if the way has only 2 nodes we need to calculate ND here
        if len(wayNodes)==2:
            avgStraight=StraightNodeDensity(2,distance)
        print(wayId,len(wayNodes),isClosed,"{:.0f}".format(gtMeters),'{:.3f}'.format(avgCurve),'{:.3f}'.format(avgStraight),sep=",")
    else:
        if gtMeters<1000:
            print("Length","{:.0f}".format(gtMeters),"m")
        else:
            if gtMeters<10000:
                print("Length","{:.2f}".format(gtMeters/1000),"km")
            else:
                print("Length","{:.1f}".format(gtMeters/1000),"km")

        # if the way has only 2 nodes we need to calculate ND here
        if tStraightNDCount!=0:
            print("Straight ND Average",'{:.3f}'.format(tStraightND/tStraightNDCount))
        elif len(wayNodes)==2:
            print("Straight ND Average",'{:.3f}'.format(StraightNodeDensity(2,distance)))
        
        if tCurveNDCount!=0:   
            print("Curve ND Average",'{:.3f}'.format(tCurveND/tCurveNDCount))

# load nodes from JSON file
def loadNodes():
    c=0
    for mobj in JSONdata['elements']:
        if mobj['type']=='node':
            nodes.append([mobj['id'],mobj['lat'],mobj['lon']])
            c=c+1
    if fDebug: print(c," nodes loaded\n")

# declare nodes list
nodes=[]

# check command line arguments
if len(sys.argv)==1:
    print('NodeDensity.py',_version)
    print('Determines node density of ways. Accepts an OSM json file format as input\n')
    print('Usage')
    print('NodeDensity.py jsonfile [-v] [-d] [-csv]\n')
    print('-v\tVerbose output')
    print('-d\tDebug output')
    print('-csv\tCSV output (overrides any -d and -v switches)')
    quit()

fDebug=False
fVerbose=False
fCSV=False

for c in range(2,len(sys.argv)):
    tArg=sys.argv[c]
    if tArg=='-v':
        fVerbose=True
    elif tArg=='-d':
        fDebug=True
    elif tArg=='-csv':
        fCSV=True
    else:
        #print("Ignoring argument",tArg)
        pass

# try to open file...
try:
    mJSONFile=open(sys.argv[1])
except:
    print('Cannot open file')
    quit()

if fCSV:
    fDebug=False
    fVerbose=False
else:
    print('Opening ', sys.argv[1])

# ... and understand if it's a real json
with mJSONFile as json_file:
    try:
        JSONdata = json.load(json_file)
    except:
        print('Not a JSON file!')
        quit()
    
    if fCSV:
        print("way,nodes,closed,length,curvend,straightnd")
    else:
        print('Loading nodes...')
    
    # load nodes in nodes list
    # CHECK what happens in case of a huge amount of nodes. In case of memory problem we should opt for a direct search of nodes in the
    # JSONdata structure

    loadNodes()

    if not fCSV: print('Parsing ways...')

    # Search for ways and parse them
    for mobj in JSONdata['elements']:
        if mobj['type']=='way':
            parseWay(mobj['id'],mobj['nodes'])
            