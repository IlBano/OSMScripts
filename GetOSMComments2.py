####
#GetOSMComments2
####
_version="0.5"

import argparse
import time
import bz2

# get value of a named tag. Some assumptions:tag preceded by a space, value enclosed in double quotes
def getTag(tid,tline):
    pid=tline.find(" "+tid)
    pvalueb=tline.find('"',pid)
    pvaluee=tline.find('"',pvalueb+1)
    tvalue=tline[pvalueb+1:pvaluee]
    return tvalue

parser = argparse.ArgumentParser(description='Get changeset comments of specified users from an OSM discussions dump. Writes output (changeset id, user, comment date and comment) in a csv file')
parser.add_argument('usernames', type=str, help='comma separated list of OSM usernames')
parser.add_argument('discussionfile', type=str, help='OSM discussion dump obtained from planet.osm.org. (.bz2 or .osm format')
parser.add_argument('outfile', type=str, help='csv output file')
options = parser.parse_args()

# check whether file is compressed or not by looking at extension
if options.discussionfile.endswith("bz2"):
    inFile = bz2.open(options.discussionfile,mode="rt",encoding="utf-8",newline="")
else:
    inFile = open(options.discussionfile,"r",encoding="utf-8")


# create output file and CSV header
outFile = open(options.outfile,"w",encoding="utf-8")
outFile.write("changesetId;user;commentDate;comment\n")

usersToSearch=options.usernames.split(",")
csCount=0 # number of processed changesets
fSkipUser=False # user is not part of search list
fAppendText=False # marks the presence of a comment spanning over multiple lines
csId="" # changeset id
coUser="" # comment user
coDate="" # comment date
coText="" # comment text

tic = time.perf_counter()
for tline in inFile:
    tline=tline.lstrip(' \t') # strip any leading space or tabs
    if tline.startswith("<changeset"):
        csId=getTag("id",tline) # since we have a changeset start tag, store its id
        csCount+=1
        if csCount % 10e4 == 0:
            print(f"Parsed {csCount/10e5:4.1f} M changesets")
    elif tline.startswith("<comment"):
        coUser=getTag("user",tline)
        fSkipUser=False
        if coUser not in usersToSearch: #if user of comment is not part of the search list, mark skip flag
            fSkipUser=True
        else:
            coDate=getTag("date",tline) # ... otherwise get comment date
    elif tline.startswith("<text") or fAppendText: # if we have a text tag or if we have a comment spanning on several lines
        if not fSkipUser: # check if user has been flagged as good
            pTextEnd=tline.find("</text>") # store position of text end tag, if any
            if fAppendText: # we enter here only if we saw a text start tag before
                if pTextEnd==-1: # if no text end tag we simply append text to previous parts...
                    coText+=tline
                else: # ...otherwise we found the last line of the comment
                    fAppendText=False # flag to mark end of comment text
                    coText+=tline[:pTextEnd] # get text up to beginning of text end tag
            else: # we enter here on the first line of the comment
                if pTextEnd==-1: # if no text end tag
                    fAppendText=True # flag to mark the presence of further comment lines
                    coText=tline[6:] # get first line of the comment starting from first char after <text> tag
                else: # we have a text end tag, so the comment is on a single line. We copy what's between text start and end tags
                    coText=tline[6:pTextEnd]
    
    if not fAppendText and coText!="": # if we have nothing more to append and the text is not empty, it's time to write the comment and its metadata
        coText=coText.replace("\n","\\n")
        outFile.write('{};{};{};"{}"\n'.format(csId,coUser,coDate,coText))
        coText=""
    #print(tline)

inFile.close()
outFile.close()

d=time.perf_counter()-tic
print(f"Parsed a total of {csCount} changesets in {d:4.2f} s")
