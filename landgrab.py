# todo: handle cases where the boundary crosses the dateline

import requests, json, math, sys, os
import xml.etree.ElementTree as ET
import pprint
import urllib

OSMID=sys.argv[1]

if isinstance(sys.argv[2], basestring):
    zoom=[]
    for part in sys.argv[2].split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            zoom.extend(range(a, b + 1))
        else:
            a = int(part)
            zoom.append(a)
else:
    zoom=[int(sys.argv[2])]

coordsonly=0
if len(sys.argv) > 3:
    coordsonly=int(sys.argv[3])
    print coordsonly

success = False
try:
    INFILE = 'http://www.openstreetmap.org/api/0.6/relation/'+OSMID+'/full'
    print "Downloading", INFILE
    r = requests.get(INFILE)
    r.raise_for_status()
    success = True
except Exception, e:
    print e

if not success:
    try:
        INFILE = 'http://www.openstreetmap.org/api/0.6/way/'+OSMID+'/full'
        print "Downloading", INFILE
        r = requests.get(INFILE)
        r.raise_for_status()
        success = True
    except Exception, e:
        print e

if not success:
    try:
        INFILE = 'http://www.openstreetmap.org/api/0.6/node/'+OSMID
        print "Downloading", INFILE
        r = requests.get(INFILE)
        r.raise_for_status()
        success = True
    except Exception, e:
        print e
        print "Element not found, exiting"
        sys.exit()

# print r.encoding
open('outfile.xml', 'w').close() # clear existing OUTFILE

with open('outfile.xml', 'w') as fd:
  fd.write(r.text.encode("UTF-8"))
  fd.close()

try:
    tree = ET.parse('outfile.xml')
except Exception, e:
    print e
    print "XML parse failed, please check outfile.xml"
    sys.exit()

root = tree.getroot()

##
## HELPER FUNCTIONS
##

tile_size = 256
half_circumference_meters = 20037508.342789244;

# Convert lat-lng to mercator meters
def latLngToMeters( coords ):
    y = float(coords['y'])
    x = float(coords['x'])
    # Latitude
    y = math.log(math.tan(y*math.pi/360 + math.pi/4)) / math.pi
    y *= half_circumference_meters

    # Longitude
    x *= half_circumference_meters / 180;

    return {"x": x, "y": y}

# convert from tile-space coords to meters, depending on zoom
def tile_to_meters(zoom):
    return 40075016.68557849 / pow(2, zoom)

# Given a point in mercator meters and a zoom level, return the tile X/Y/Z that the point lies in
def tileForMeters(coords, zoom):
    y = float(coords['y'])
    x = float(coords['x'])
    return {
        "x": math.floor((x + half_circumference_meters) / (half_circumference_meters * 2 / pow(2, zoom))),
        "y": math.floor((-y + half_circumference_meters) / (half_circumference_meters * 2 / pow(2, zoom))),
        "z": zoom
    }

# Convert tile location to mercator meters - multiply by pixels per tile, then by meters per pixel, adjust for map origin
def metersForTile(tile):
    return {
        "x": tile['x'] * half_circumference_meters * 2 / pow(2, tile.z) - half_circumference_meters,
        "y": -(tile['y'] * half_circumference_meters * 2 / pow(2, tile.z) - half_circumference_meters)
    }

def getTiles(_points,_zoom):
    tiles = []

    ## find tile
    for point in _points:
        tiles.append(tileForMeters(latLngToMeters({'x':point['x'],'y':point['y']}), _zoom))

    ## de-dupe
    tiles = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in tiles)]

    ## patch holes in tileset

    ## get min and max tiles for lat and long

    minx = 1048577
    maxx = -1
    miny = 1048577
    maxy = -1

    for tile in tiles:
        minx = min(minx, tile['x'])
        maxx = max(maxx, tile['x'])
        miny = min(miny, tile['y'])
        maxy = max(maxy, tile['y'])
    # print miny, minx, maxy, maxx

    newtiles = []

    for tile in tiles:
        # find furthest tiles from this tile on x and y axes
        x = tile['x']
        lessx = 1048577
        morex = -1
        y = tile['y']
        lessy = 1048577
        morey = -1
        for t in tiles:
            if int(t['x']) == int(tile['x']):
                # check on y axis
                lessy = min(lessy, t['y'])
                morey = max(morey, t['y'])
            if int(t['y']) == int(tile['y']):
                # check on x axis
                lessx = min(lessx, t['x'])
                morex = max(morex, t['x'])

        # if a tile is found which is not directly adjacent, add all the tiles between the two
        if (lessy + 2) < tile['y']:
            for i in range(int(lessy+1), int(tile['y'])):
                newtiles.append({'x':tile['x'],'y':i, 'z':_zoom})
        if (morey - 2) > tile['y']:
            for i in range(int(morey-1), int(tile['y'])):
                newtiles.append({'x':tile['x'],'y':i, 'z':_zoom})
        if (lessx + 2) < tile['x']:
            for i in range(int(lessx+1), int(tile['x'])):
                newtiles.append({'x':i,'y':tile['y'], 'z':_zoom})
        if (morex - 2) > tile['x']:
            for i in range(int(morex-1), int(tile['x'])):
                newtiles.append({'x':i,'y':tile['y'], 'z':_zoom})

    ## de-dupe
    newtiles = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in newtiles)]
    ## add fill tiles to boundary tiles
    tiles = tiles + newtiles
    ## de-dupe
    tiles = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in tiles)]


    if coordsonly == 1:
        ## output coords
        pprint.pprint(tiles)
        print "\nFinished: %i tiles at zoom level %i" % (len(tiles), _zoom)
    else:
        ## download tiles
        print "\nDownloading %i tiles at zoom level %i" % (len(tiles), _zoom)

        ## make/empty the tiles folder
        folder = "build/bin/tiles"
        if not os.path.exists(folder):
            os.makedirs(folder)

        total = len(tiles)
        if total == 0:
            print("Error: no tiles")
            exit()
        count = 0
        sys.stdout.write("\r%d%%" % (float(count)/float(total)*100.))
        sys.stdout.flush()
        for tile in tiles:

            dstFile = "%i-%i-%i.json" % (_zoom,tile['x'],tile['y'])
            urllib.urlretrieve ("http://vector.mapzen.com/osm/all/%i/%i/%i.mvt?api_key=vector-tiles-HqUVidw" % (_zoom, tile['x'],tile['y']), 
                                "build/bin/tiles/%i-%i-%i.mvt" % (_zoom,tile['x'],tile['y']))

            count += 1
            sys.stdout.write("\r%d%%" % (float(count)/float(total)*100.))
            sys.stdout.flush()

##
## PROCESSING points
##

print "Processing:"

points = []
for node in root:
    if node.tag == "node":
        lat = float(node.attrib["lat"])
        lon = float(node.attrib["lon"])
        points.append({'y':lat, 'x':lon})

##
## GET TILES for all zoom levels
##
for z in zoom:
    getTiles(points,z)
        
