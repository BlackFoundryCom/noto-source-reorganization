#!/opt/local/bin/python3

from fontTools.ttLib import TTFont
font = TTFont('/System/Library/Fonts/SFNSText.ttf')

GlyphNames = font.getGlyphOrder()
def glyphName(id):
    return GlyphNames[id]
GlyphIDs = {name:i for i,name in enumerate(GlyphNames)}
def glyphID(name):
    return GlyphIDs[name]

class RegisteredCoverage:
    def __init__(self, glyphList, name):
        self.list = glyphList
        self.name = name

AllCoveragesStartingAtGlyph = {}
def registerCoverage(cov, name):
    first = cov[0]
    registeredCovs = []
    if first not in AllCoveragesStartingAtGlyph:
        AllCoveragesStartingAtGlyph[first] = registeredCovs
    else:
        registeredCovs = AllCoveragesStartingAtGlyph[first]
    for rc in registeredCovs:
        if cov == rc.list:
            print("ALREADY REGISTERED!")
            return rc
    rc = RegisteredCoverage(cov, name)
    registeredCovs.append(rc)
    return rc

gOut = open("out.fea", 'w')

printSharp = True;
def com(*args, **kargs):
    global printSharp
    print(*args, **kargs)
    return
    if printSharp:
        print('#',*args, **kargs, file=gOut)
    else:
        print(*args, **kargs, file=gOut)
    printSharp = 'end' not in kargs

#gpos = font['GPOS'].table
gsub = font['GSUB'].table

# Languages and scripts

def analyzeScripts(sl):
    com("ScriptList has", sl.ScriptCount,"scripts")
    for sr in sl.ScriptRecord:
        com("ScriptTag", sr.ScriptTag)
        s = sr.Script
        com("\tDefaultLangSys:")
        analyzeLangSys(s.DefaultLangSys)
        com("\tLangSysCount", s.LangSysCount)
        com("\tLangSysRecord is list of size", len(s.LangSysRecord))
        for lsr in s.LangSysRecord:
            com("\t\tLangSysTag", lsr.LangSysTag)
            com("\t\tLangSys:")
            analyzeLangSys(lsr.LangSys)

def analyzeLangSys(ls):
    com("\t\t\tLookupOrder", ls.LookupOrder)
    com("\t\t\tReqFeatureIndex", ls.ReqFeatureIndex)
    com("\t\t\tFeatureCount", ls.FeatureCount)
    com("\t\t\tFeatureIndex", ls.FeatureIndex)

# Features

def analyzeFeatures(fl):
    com("FeatureList has", fl.FeatureCount,"features")
    byTags = {}
    for i, fr in enumerate(fl.FeatureRecord):
        q = fr.FeatureTag
        if q not in byTags:
            byTags[q] = []
        byTags[q].append((i,fr.Feature))
    for tag,feats in byTags.items():
        com('\t',len(feats),"features with tag", tag)

# Lookups

lkpSingle = 1
lkpMultiple = 2
lkpAlternate = 3
lkpLigature = 4
lkpContext = 5
lkpChaining = 6
lkpExtension = 7
lkpReverse = 8
LookupTypeToName = {lkpSingle:"Single", lkpMultiple:"Multiple", lkpAlternate:"Alternate", lkpLigature:"Ligature",
        lkpContext:"Context", lkpChaining:"Chaining Context", lkpExtension:"Extension Substitution", lkpReverse:"Reverse Chaining Context Single"}
def getHumanLookupType(i):
    return LookupTypeToName.get(i, "UNKNOWN")

# Ranges of glyphs

def printIntervals(l):
    com("<< ", end='')
    n = len(l)
    for i in range(n):
        lo, hi = l[i]
        if lo == hi: com("{}".format(lo), end='')
        else: com("({}--{})".format(lo,hi), end='')
        if i < n - 1: com(', ', end='')
    com(" >>")

def toIntervals(l): # list of numbers -> list of closed intervals
    r = []
    first = 0
    for i,v in enumerate(l):
        if i == 0: continue
        if v == l[i-1]+1:
            pass
        else:
            r.append((l[first],l[i-1]))
            first = i
    r.append((l[first],l[-1]))
    printIntervals(r)

def writeGlyphOrGlyphClass(cov):
    if len(cov) == 1:
        gOut.write(cov[0])
    else:
        gOut.write('[')
        for c in cov:
            gOut.write(' '+c)
        gOut.write(' ]')

# Lookup of type 1 : single substitution

def analyseSingleSubTable(i,j,t):
    com("\t\t[Lkp {} Single] subtable {}: format = {}:".format(i, j, t.Format))
    coverage = [glyphID(n) for n in t.mapping.keys()]
    name = "SingleLookup_{}_sub_{}_".format(i,j)
    old = registerCoverage(list(t.mapping.keys()),name+"old")
    new = registerCoverage(list(t.mapping.values()),name+'new')
    if t.Format == 1: # check constant offset
        #com("\t\t\tKeys:", coverage)
        com("\t\t\tKeys:", end='')
        toIntervals(coverage)
        offsets = set(glyphID(v)-glyphID(k) for k,v in t.mapping.items())
        com("\t\t\tOffset:", offsets)
        assert(len(offsets) == 1)
    else:
        com("\t\t\tInput glyphs:", end='')
        toIntervals(coverage)
        com("\t\t\tmaps to:", end='')
        toIntervals([glyphID(n) for n in t.mapping.values()])
    gOut.write('\tsub ')
    writeGlyphOrGlyphClass(old.list)
    gOut.write(' by ')
    writeGlyphOrGlyphClass(new.list)
    gOut.write(';\n')

# Lookup of type 2 : multiple substitution

def analyseMultipleSubTable(i,j,t):
    com("\t\t[TODO Lkp {} Multiple] subtable {}: format = {}:".format(i, j, t.Format))

# Lookup of type 4 : ligature substitution

def analyseLigature(a, ligatureList):
    com("[{}:{}]".format(a, len(ligatureList)),end='')

def analyseLigatureSubTable(i,j,t):
    com("\t\t[Lkp {} Ligature] subtable {}: format = {}:".format(i, j, t.Format))
    com("\t\tSubTable has", len(t.ligatures),"ligatures first-letters")
    for a,liga in  t.ligatures.items():
        analyseLigature(a,liga)

# Lookups

def analyzeLookups(ll):
    com("LookupList has", ll.LookupCount,"lookups")
    for il in enumerate(ll.Lookup):
        analyseLookup(*il)

def analyseLookup(i, l):
    com("\tLookup",i,"of type", getHumanLookupType(l.LookupType), end="")
    com(", LookupFlag =", l.LookupFlag, end="")
    com(", SubTableCount = {}:".format(l.SubTableCount))
    lookupName = "LKUP_"+str(i)
    gOut.write("lookup {} {{\n".format(lookupName))
    for j,t in enumerate(l.SubTable):
        if l.LookupType == lkpSingle:
            analyseSingleSubTable(i,j,t)
        elif l.LookupType == lkpMultiple:
            analyseMultipleSubTable(i,j,t)
        elif l.LookupType == lkpAlternate:
            pass
        elif l.LookupType == lkpLigature:
            analyseLigatureSubTable(i,j,t)
        else:
            pass
    gOut.write("}} {};\n".format(lookupName))

def analyzeGsub(gsub):
    # ScriptList, FeatureList, LookupList
    com("GSUB table version {}.{}".format(gsub.Version // 0x10000, gsub.Version % 0x10000))
    analyzeScripts(gsub.ScriptList)
    analyzeFeatures(gsub.FeatureList)
    analyzeLookups(gsub.LookupList)

analyzeGsub(gsub)
gOut.close()
