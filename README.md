# OSM Scripts
## GetOSMComments.py
*Usage*
GetOSMComments.py [-h] usernames discussionfile outfile

*Get changeset comments of specified users from an OSM discussions dump. Writes output (changeset id, user, comment date and comment) in a csv file

*positional arguments:

*usernames       comma separated list of OSM usernames

*discussionfile  OSM discussion dump obtained from planet.osm.org. N.B. must be already in .osm format

*outfile         csv output file

*optional arguments:

*-h, --help      show this help message and exit

## Checkroundabouts.py
Counts roundabouts in a json containing OSM data. Json file should contain ways and nodes already filtered for tag junction=roundabout

Usage
CheckRoundabouts.py jsonfile [-v]

-v  Verbose output

## NodeDensity.py
How can we determine if an OSM way is defined by too many (or too few) nodes ?
Let's define a "ND" parameter as a value which is function of the density of nodes in a way. It's value should be comparable among different ways. For example a 5 meters radius 90 degrees curve described with 10 nodes is more dense than the same curve with a 10 meters radius: the ND value should represent this accordingly

Density of curves can be thought as related to the length of the curve, the number of nodes that describe it and the total angle.
When talking about straight ways we should opt for a simple calculation based on the length of the way and the number of nodes.
That is to say that ND of straight ways cannot be compared to the ND of curved ways.
By the way what is a straight way ? a way in which the angle between each segment and the previous is below a certain amount (currently 8°).
The algorithm is currently in beta and under test so consider it as an experiment.

*Determines node density of ways. Accepts an OSM json file format as input*

*Usage*

*NodeDensity.py jsonfile [-v] [-d] [-csv]*

*-v    Verbose output*

*-d    Debug output*

*-csv  CSV output (overrides -d and -v switches)*
