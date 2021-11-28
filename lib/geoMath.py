import math
  
def getMidpoint(pLat,pLon,cLat,cLon):
    lat1=math.radians(pLat)
    lat2=math.radians(cLat)
    lon1=math.radians(pLon)
    lon2=math.radians(cLon)
    Bx=math.cos(lat2)*math.cos(lon2-lon1)
    By=math.cos(lat2)*math.sin(lon2-lon1)
    mlat=math.atan2(math.sin(lat1)+math.sin(lat2),math.sqrt((math.cos(lat1)+Bx)*(math.cos(lat1)+Bx)+By*By))
    mlon=lon1+math.atan2(By,math.cos(lat1)+Bx)

    return math.degrees(mlat),math.degrees(mlon)

# Get distance between two point using "Spherical law of cosines" https://mathworld.wolfram.com/SphericalTrigonometry.html
# This method is 30% faster that haversine
def getDistance(pLat,pLon,cLat,cLon):
    if pLat==cLat and pLon==cLon:
        return 0
      
    x=math.acos(math.cos(math.radians(90-pLat))*math.cos(math.radians(90-cLat))+math.sin(math.radians(90-pLat))*math.sin(math.radians(90-cLat))*math.cos(math.radians(pLon-cLon))) *6371*1000
    return x

# Get distance between two point using "Haversine" formula https://en.wikipedia.org/wiki/Haversine_formula
def getDistance2(pLat,pLon,cLat,cLon):
    if pLat==cLat and pLon==cLon:
        return 0

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

# Given a start point, initial bearing, and distance, this will calculate the destina­tion point and final bearing travelling along a (shortest distance) great circle arc
def getDestinationPoint(pLat,pLon,bearing,distance):
    R = 6371*1000
    lat1=math.radians(pLat)
    lon1=math.radians(pLon)
    
    dLat = math.asin( math.sin(lat1)*math.cos(distance/R) + math.cos(lat1)*math.sin(distance/R)*math.cos(bearing))

    dLon = lon1 + math.atan2(math.sin(bearing)*math.sin(distance/R)*math.cos(lat1),math.cos(distance/R)-math.sin(lat1)*math.sin(dLat))
    
    return math.degrees(dLat),math.degrees(dLon)

# Calculate bearing of segment (see http://www.movable-type.co.uk/scripts/latlong.html)

def getBearing(pLat,pLon,cLat,cLon,fDegrees=False):
    ax=math.cos(math.radians(pLat))*math.sin(math.radians(cLat))-math.sin(math.radians(pLat))*math.cos(math.radians(cLat))*math.cos(math.radians(cLon)-math.radians(pLon))
    ay=math.sin(math.radians(cLon)-math.radians(pLon))*math.cos(math.radians(cLat))
    x=math.atan2(ay,ax)
    
    if fDegrees:
        x=math.degrees(x)
        x=(x+360)%360
    
    return x
