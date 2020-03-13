import os
import json
import shutil
import defcon

from fontTools.misc.plistlib    import load as readThePlist
from fontmake.font_project              import FontProject
from defcon                             import Font
from Lib.makeThings                     import ufo2font, ufosToGlyphs
from Lib.findThings                     import getFile, getFolder
from fontTools.designspaceLib           import *
from fontTools.ttLib                    import TTFont
from fontTools.ttLib.tables._n_a_m_e    import makeName
from fontTools.varLib.mutator           import instantiateVariableFont
from fontTools                          import varLib, ttLib
from fontTools.subset                   import Subsetter
from fontTools.subset                   import Options
from fontTools.merge                    import Merger
from ufo2ft.featureWriters              import (KernFeatureWriter,
                                        MarkFeatureWriter,
                                        loadFeatureWriters,
                                        ast
                                        )
from ufo2ft                             import (compileInterpolatableOTFsFromDS,
                                        compileInterpolatableTTFsFromDS,
                                        postProcessor,
                                        compileTTF
                                        )


"""
useful functions:
mastersUfos2fonts(familyName, formats you want) => read a design space, find masters files, generate fonts
designSpace2Var(familyName) => read designspace, make var font if ufos are compatible
makeTTFInstancesFromVF(familyName) => take the variable if it exists (if not make it)
                                        and extract static instances from it
                                        by reading the designspace
renameFonts(familyName, newName, formats you want) => needs the original fonts first, if not make
mergeFonts(baseFanmilyName, familyName of the fonts to inject) => WIP.

"""

pan_european_fonts = ["NotoSans", "NotoSans-Italic", "NotoSerif", "NotoSerif-Italic", "NotoSansDisplay", "NotoSansDisplay-Italic", "NotoSerifDisplay", "NotoSerifDisplay-Italic", "NotoSansMono"]
arabic_fonts = ["NotoKufiArabic", "NotoNaskhArabic", "NotoNaskhArabicUI", "NotoNastaliqUrdu", "NotoSansArabic", "NotoSansArabicUI"]



## Code from fontmake
def add_mti_features_to_master_ufos(family, masters):
    rdir = os.path.abspath("../src/" + family + "/")
    mti_paths = readThePlist(os.path.join(rdir, family+".plist")) # os.path.join(rdir, family+".plist")
    for master in masters:
        key = master.info.familyName.replace(" ", "")+"-"+master.info.styleName.replace(" ", "")
        for table, path in mti_paths[key].items():
            with open(os.path.join(mtiFolderPath, path), "rb") as mti_:
                ufo_path = (
                    "com.github.googlei18n.ufo2ft.mtiFeatures/%s.mti"
                    % table.strip()
                )
                master.data[ufo_path] = mti_.read()
            # If we have MTI sources, any Adobe feature files derived from
            # the Glyphs file should be ignored. We clear it here because
            # it only contains junk information anyway.
            master.features.text = ""
            master.save()
    print("\tufos updated with UI versioned MTI data")

def openDesignSpace(path):
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    return designSpace

def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

def renameFonts(family, newName, *flavors, codePageRange = []):
    saveName = newName.replace(" ", "")
    formats = ["OTF", "TTF", "WOFF2", "WOFF", 'instances']
    for i in flavors:
        if os.path.exists((getFolder(family) + "fonts/" + i.upper())):
            pass
        else:
            # mastersUfos2fonts(family, i)
            instances(family, i)
    path = getFolder(family) + "fonts/"
    fontsFolders = [path + i for i in os.listdir(path) if i.split("/")[-1] in formats]
    for folder in fontsFolders:
        fonts = [folder + "/" + font for font in os.listdir(folder) if font.split(".")[-1].upper() in formats]
        for f in fonts:
            renamedFont, WeightName = renamer(f, newName, codePageRange)
            format_ = f.split(".")[1].upper()
            destination = getFolder(family) + "/" + newName + "/" + format_
            fontName = saveName + "-" + ''.join(WeightName.split(' ')) + "." + f.split(".")[1]
            if not os.path.exists(destination):
                os.makedirs(destination)
            renamedFont.save(os.path.join(destination, fontName))


def renamer(f, newName, codePageRange = []):
    renamedFont = ttLib.TTFont(f)
    #First : GET THE STYLE NAME EITHER IN namerecord2 if the font is a RBIBI font or in namerecord 17 in other cases
    for namerecord in renamedFont['name'].names:
        namerecord.string = namerecord.toUnicode()
        if namerecord.nameID == 2:
            WeightName = namerecord.string
        if namerecord.nameID == 17:
            WeightName = namerecord.string
    #Then Change the name everywhere
    for namerecord in renamedFont['name'].names:
        namerecord.string = namerecord.toUnicode()
        # Create the naming of the font Family + style if the style is non RBIBI
        if namerecord.nameID == 1:
            if WeightName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                namerecord.string = newName
            else:
                namerecord.string = newName + " " + WeightName
        if namerecord.nameID == 3:
            unicID = namerecord.string.split(";")
            newUnicID = unicID[0] +";"+ unicID[1] +";"+ ''.join(newName.split(' ')) +"-"+ ''.join(WeightName.split(' '))
            namerecord.string = newUnicID
        if namerecord.nameID == 4:
            namerecord.string = newName + " " + WeightName
        if namerecord.nameID == 6:
            namerecord.string = ''.join(newName.split(' ')) + '-' + ''.join(WeightName.split(' '))
        if namerecord.nameID == 7:
            namerecord.string = "Noto (from which this font is a modification) is a trademark of Google Inc."
        if namerecord.nameID == 16:
            namerecord.string = newName
    os2cp1 = renamedFont['OS/2'].ulCodePageRange1
    # os2cp1 = 0
    if len(codePageRange) > 0:
        for i in codePageRange:
            os2cp1 = setBit(os2cp1, i)
    return renamedFont, WeightName

def designSpace2Var(family):
    """ syntax :
    """
    print("Load {}.designspace".format(family))
    path, folder = getFile(".designspace", "src", family)
    print("CWD:>",os.getcwd())
    designSpace = openDesignSpace(path)
    print("Load fonts")
    designSpace.loadSourceFonts(Font)
    print("Start to build Variable Tables")
    font, _, _ = varLib.build(compileInterpolatableTTFsFromDS(designSpace, \
                    featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter]), optimize=False)
    destination = folder + "/fonts/VAR"
    if not os.path.exists(destination):
        os.makedirs(destination)
    print("Variable font generated")
    font.save(os.path.join(destination, family + "-VF.ttf"))

def makeCompatibleOTF(family):
    path, folder = getFile("_cleaned.designspace", "src", family)
    designSpace = openDesignSpace(path)
    designSpace.loadSourceFonts(Font)
    for s in compileInterpolatableOTFsFromDS(designSpace).sources:
        name = s.name.replace(" ", "") + ".otf"
        otf = s.font
        otf.save(folder + "/_compatibles/" + name)

def stockDSstylename(designspace):
    loca2styleNameDict = dict()
    for instance in designspace.instances:
        loca2styleNameDict[str(instance.location)] = instance.styleName
        familyName = instance.familyName

    return loca2styleNameDict, familyName

def makeOneInstanceFromVF(family, loca):
    path, folder = getFile(".designspace", "src", family)
    ds = openDesignSpace(path)
    axesName = dict()
    ax = dict()
    maps = dict()
    for a in ds.axes:
        ax[a.tag] = a.name
        axesName[a.name] = a.tag
        if a.map:
            maps[a.name] = a.map
    locaStyleName, familyName = stockDSstylename(ds)
    location = str(loca)
    ##### READ THE MAP #####
    for tag in loca:
        print(loca, tag)
        name = ax[tag]
        if name in maps:
            for i in maps[name]:
                if int(loca[tag]) == int(i[1]):
                    locationValue = i[0]
                    loca[tag] = round(locationValue)
        else:
            pass
    for i in ax:
        location = location.replace(i, ax[i])
    styleName = locaStyleName[location]
    destination = folder + "/fonts/static/"
    if not os.path.exists(destination):
        os.makedirs(destination)
    varFontPath = folder + "/fonts/VAR/" + family + "-VF.ttf"
    if not os.path.exists(varFontPath):
        print("Make Variable first")
        designSpace2Var(family)
    varFont = TTFont(varFontPath)
    revision = varFont['head'].fontRevision
    V_major = str(revision).split(".")[0]
    V_minor = str(revision).split(".")[1]
    fontName = '-'.join([familyName, styleName.replace(" ", "")]) + '.ttf'
    # familyName = instance.familyName
    static = instantiateVariableFont(varFont, loca, inplace=False)
    # print(static['name'].names)
    #<NameRecord NameID=14; PlatformID=3; LanguageID=1033>
    for namerecord in static['name'].names:
        if namerecord.nameID == 1:
            if styleName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                namerecord.string = familyName
            else:
                namerecord.string = familyName + " " + styleName
                n16_p3 = makeName(familyName, 16, 3, 1, 0x409)
                n16_p1 = makeName(familyName, 16, 1, 0, 0x0)
                instance['name'].names.append(n16_p3)
                instance['name'].names.append(n16_p1)
                n17_p3 = (makeName(styleName, 17, 3, 1, 0x409))
                n17_p1 = (makeName(styleName, 17, 1, 0, 0x0))
                instance['name'].names.append(n17_p3)
                instance['name'].names.append(n17_p1)
        if namerecord.nameID == 2:
            if styleName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                namerecord.string = styleName
            elif "Italic" in styleName:
                namerecord.string = "Italic"
            else:
                namerecord.string = "Regular"
        if namerecord.nameID == 5:
            namerecord.string = 'Version %s.%s' % (V_major, V_minor)
        if namerecord.nameID == 3:
            PSName = ''.join(familyName.split(' ')) + '-' + ''.join(styleName.split(' '))
            namerecord.string = '%s.%s' % (V_major, V_minor) +';'+ '%s' % PSName + ';'
        if namerecord.nameID == 4:
            namerecord.string = familyName + " " + styleName
        if namerecord.nameID == 6:
            namerecord.string = ''.join(familyName.split(' ')) + '-' + ''.join(styleName.split(' '))
        if namerecord.nameID == 16:
            namerecord.string = familyName
        if namerecord.nameID == 17:
            namerecord.string = styleName
    static.save(os.path.join(destination, fontName))


def makeTTFInstancesFromVF(family):
    axesName = dict()
    path, folder = getFile(".designspace", "src", family)
    designSpace = openDesignSpace(path)
    loca = dict()
    maps = dict()
    for a in designSpace.axes:
        if a.map:
            maps[a.name] = a.map
    varFontPath = folder + "/fonts/VAR/" + family + "-VF.ttf"
    if not os.path.exists(varFontPath):
        print("Make Variable first")
        designSpace2Var(family)
    varFont = TTFont(varFontPath)
    revision = varFont['head'].fontRevision
    V_major = str(revision).split(".")[0]
    V_minor = str(revision).split(".")[1]
    #store axis name and axis tag in a dict for correspondance
    for a in designSpace.axes:
        axesName[a.name] = a.tag
    # read the location of instance and put in a new dict the tag
    # corresponding to the axis name as k and the location value as v
    for instance in designSpace.instances:
        location = dict(instance.location)
        for name in location:
            if name in maps:
                for i in maps[name]:
                    if int(location[name]) == int(i[1]):
                        locationValue = i[0]
                        # print(instance.name," entry: ", location[name], ", Real value:", locationValue)
                        loca[axesName[name]] = round(locationValue)
            else:
                loca[axesName[name]] = int(location[name])
        print(instance.name, loca)
        fontName = '-'.join([instance.familyName, \
                                instance.styleName.replace(" ", "")]) + '.ttf'
        fi = instantiateVariableFont(varFont, loca, inplace=False)
        #build name table entries
        styleName = instance.styleName
        familyName = instance.familyName
        for namerecord in fi['name'].names:
            if namerecord.nameID == 1:
                if styleName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                    namerecord.string = familyName
                else:
                    namerecord.string = familyName + " " + styleName
                    n16 = makeName(familyName, 16, 3, 1, 0x409)
                    n17 = (makeName(styleName, 17, 3, 1, 0x409))
                    fi['name'].names.append(n16)
                    fi['name'].names.append(n17)
            if namerecord.nameID == 2:
                if styleName == "Bold":
                    namerecord.string = "Bold"
                elif styleName == "Italic":
                    namerecord.string = "Italic"
                elif styleName == "Bold Italic":
                    namerecord.string = "Bold Italic"
                elif "Italic" in styleName:
                    namerecord.string = "Italic"
                else:
                    namerecord.string = "Regular"
            if namerecord.nameID == 5:
                namerecord.string = 'Version %s.%s' % (V_major, V_minor)
            if namerecord.nameID == 3:
                PSName = ''.join(familyName.split(' ')) + '-' + ''.join(styleName.split(' '))
                namerecord.string = '%s.%s' % (V_major, V_minor) +';'+ '%s' % PSName + ';'
            if namerecord.nameID == 4:
                namerecord.string = familyName + " " + styleName
            if namerecord.nameID == 6:
                namerecord.string = ''.join(familyName.split(' ')) + '-' + ''.join(styleName.split(' '))
        destination = folder + "/fonts/instances/"
        if not os.path.exists(destination):
            os.makedirs(destination)
        fi.save(os.path.join(destination, fontName))

def readJsonStoredSubset(jsonpath, writingSystem):
    toKeep, keep = list(), list()
    latinProCodePageRange = [0, 1, 4, 7, 8]
    cyrProCodePageRange = [2]
    greekProCodePageRange = [3]
    ASCII = [0, 1]
    SecureSet = [0]
    coreArabicCodePageRange = [0,6]
    unicodePageRangeDict = {"Cyrillic":latinProCodePageRange, "CyrillicPro":latinProCodePageRange, \
        "Greek" : greekProCodePageRange, "Latin" : latinProCodePageRange, "ASCII" : ASCII, "SecureSet" : SecureSet, "Core_Arabic" : coreArabicCodePageRange}
    pageRangeToApply = []
    with open(jsonpath, 'r') as subsetDict:
        subset = json.load(subsetDict)
    for i in subset:
        if i in writingSystem:
            toKeep.append(subset[i])
            # print(i)
            pageRangeToApply += unicodePageRangeDict[i]
    if "Latin" not in writingSystem:
        toKeep.append(subset["SecureSet"])
    for i in toKeep:
        keep += i
    return keep, pageRangeToApply

def subsetFonts(family, writingSystem, flavor=["ttf"], familyNewName=" ", jsonpath = " "):
    if len(flavor) == 0:
        flavor = ["ttf"]
    latinProCodePageRange = [0, 1, 4, 7, 8]
    cyrProCodePageRange = [2]
    greekProCodePageRange = [3]
    ASCII = [0, 1]
    SecureSet = [0]
    coreArabicCodePageRange = [0,6]
    unicodePageRangeDict = {"Cyrillic":latinProCodePageRange, "CyrillicPro":latinProCodePageRange, \
        "Greek" : greekProCodePageRange, "Latin" : latinProCodePageRange, "ASCII" : ASCII, "SecureSet" : SecureSet, "Core_Arabic" : coreArabicCodePageRange}
    pageRangeToApply = []
    subsetFolder = ""
    for i in writingSystem:
        subsetFolder += i
    formats = ["ttf", "woff", "woff2", "otf"]
    toKeep = list()
    folder = getFolder(family)
    options = Options()
    options.layout_features = '*'  # keep all GSUB/GPOS features
    # options.legacy_kern = True  # keep kern table
    options.glyph_names = False  # keep post glyph names
    options.legacy_cmap = True  # keep non-Unicode cmaps
    options.symbol_cmap = True  # keep Symbol cmaps
    options.name_legacy = True  # keep non-Unicode names
    options.name_IDs = ['*']  # keep all nameIDs
    options.name_languages = ['*']  # keep all name languages
    options.notdef_outline = True  # keep outline of .notdef
    options.ignore_missing_glyphs = True
    options.prune_unicode_ranges = True
    keep = []
    # if jsonpath == " ":
    #     jsonpath = [folder + json for json in os.listdir(folder) if ".json" in json]
    if family in pan_european_fonts:
        jsonpath = "lgc_glyphset.json"
    elif family in arabic_fonts:
        jsonpath = "arabic_glyphset.json"
    # keep, pageRangeToApply = readJsonStoredSubset(os.path.join(os.getcwd(), "lgc_glyphset.json"), writingSystem)
    keep, pageRangeToApply = readJsonStoredSubset(jsonpath, writingSystem)
    for i in flavor:
        if not os.path.exists(folder + "/fonts/" + i.upper()):
            instances(family, i)
    for i in flavor:
        fontspath = [folder + "fonts/" + i.upper() + "/" + font for font in os.listdir(folder + "fonts/" + i.upper())]
        for f in fontspath:
            if f.split(".")[-1] in formats:
                newfont = TTFont(f)
                for namerecord in newfont['name'].names:
                    namerecord.string = namerecord.toUnicode()
                    if namerecord.nameID == 2:
                        WeightName = namerecord.string
                    if namerecord.nameID == 17:
                        WeightName = "".join(namerecord.string.split(" "))
                        print(family, WeightName)
                subsetter = Subsetter(options=options)
                subsetter.populate(glyphs=keep)
                subsetter.subset(newfont)
                destination = folder + "fonts/" + subsetFolder + "_subset/fonts/"
                # print("destination>>", destination)
                if not os.path.exists(destination + i.upper()):
                    os.makedirs(destination + i.upper())
                newfont.save(destination + i.upper() + "/" + family + subsetFolder + "-" + WeightName +"." + i)
    folder = family + "/fonts/" + subsetFolder + "_subset"
    # print(pageRangeToApply)
    if familyNewName != " ":
        renameFonts(folder, familyNewName, codePageRange = pageRangeToApply)
    else:
        familyNewName = family + subsetFolder
        renameFonts(folder, familyNewName, codePageRange = pageRangeToApply)
    shutil.rmtree(destination)

def newFolderForMerged(directory):
    repo = "src/" + directory + "/"
    cwd = os.getcwd()
    rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo)) + "/"
    return rdir

def basicMerger(masterfont, *fontsToAdd, onlySecureSet=False): #path of actual fonts
    fontsPath = []
    fontsPath.append(masterfont)
    for ft in fontsToAdd:
        fontsPath.append(ft)
    #merge
    merger = Merger()
    mergedFont = merger.merge(fontsPath)
    flavor = str(os.path.basename(masterfont).split(".")[-1])
    if onlySecureSet is True:
        destination = masterfont.replace(os.path.basename(masterfont), "")
    else:
        new = os.path.basename(masterfont).split("-")[0]
        for i in fontsToAdd:
            new += i.replace("Noto", "")
        destination = newFolderForMerged(new)
    if not os.path.exists(destination):
        os.makedirs(destination)
    mergedFontPath = os.path.join(destination, os.path.basename(masterfont))
    mergedFont.save(mergedFontPath)

    # return mergedFontPath

def secureSetFromLatin(family, formats, jsonpath):
    if len(jsonpath) != 0:
        for i in formats:
            subsetFonts(family, ["SecureSet"], flavor = [i], jsonpath=jsonpath)
    else:
        folder = getFolder(family)
        jsonpath = [folder + json for json in os.listdir(folder) if ".json" in json]
        for i in formats:
            subsetFonts(family, ["SecureSet"], flavor = [i], jsonpath=jsonpath)

def addSecureSet(family, flavorz):
    shared = ""
    flavors = ["OTF", "TTF", "WOFF2", "WOFF"]
    if family not in pan_european_fonts:
        if "Serif" in family:
            shared = "NotoSerif"
            if "Italic" in family:
                shared += "-Italic"
        else:
            shared = "NotoSans"
            if "Italic" in family:
                shared += "-Italic"
    print("A securet set of basic glyphs will be added from {}".format(shared))
    folder = getFolder(family)
    #READ THE JSON STORED IN THE FAMILY IN WICH YOU WANT TO ADD THE SECURE SET. IF THERE IS NO JSON.
    #IT RETURN AN EMPTY LIST. THEN THE secureSetFromLatin WILL USE THE DEFAULT ONE IN THE LATIN FAMILY TO SUBSET
    #(stored in the "shared" variable)
    jsonpath = [folder + json for json in os.listdir(folder) if ".json" in json]
    secureSetFromLatin(shared, flavorz, jsonpath)
    # sharedFolder = getFolder(shared + "fonts/SecureSet_subset/" + shared + "SecureSet")
    ftpath = getFolder(family) + "fonts/"
    fontsFolders = [ftpath + i for i in os.listdir(ftpath) if i.split("/")[-1] in flavors]
    sharedPath = getFolder(shared) + "fonts/SecureSet_subset/" + shared + "SecureSet/"
    secureSetFontsFolders = [sharedPath + i for i in os.listdir(sharedPath) if i.split("/")[-1] in flavors]
    for folder in fontsFolders:
        fonts = [folder + "/" + font for font in os.listdir(folder) if font.split(".")[-1].upper() in flavors]
        for f in fonts:
            style = os.path.split(f)[1].replace(family+"-", "").split(".")[0]
            #sharedFolder = getFolder(shared + "/fonts/SecureSet_subset/" + shared + "SecureSet/" + f.split(".")[-1].upper())
            #secureSetFontsFolder = [sharedPath + i for i in os.listdir(sharedPath) if i.split("/")[-1] == f.split("/")[-1]]
            # for secureSetFonts in os.listdir(sharedFolder):
            for secureSetFontsFolder in secureSetFontsFolders:
                if secureSetFontsFolder.split("/")[-1] == f.split(".")[-1].upper():
                    # print("ok", secureSetFontsFolder)
                    for secureSetFont in os.listdir(secureSetFontsFolder):
                        # print(secureSetFont)
                        styleShared = os.path.split(secureSetFont)[1].replace(shared+"SecureSet-", "").split(".")[0]
                        # print(styleShared)
                        if style == styleShared:
                            ft2add = secureSetFontsFolder+"/"+secureSetFont
                            basicMerger(f, ft2add, onlySecureSet=True)

def mastersUfos2fonts(family, *flavors, instances = False):
    formats = ["OTF", "TTF", "WOFF2", "VAR", "WOFF", 'instances']
    # print(len(flavors), flavors)
    if len(flavors) == 0:
        flavors = "ttf"
    masters = []
    path, folder = getFile(".designspace", "src", family)
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    shared = ""
    for s in designSpace.sources:
        masters.append(family + "-" + s.styleName.replace(" ", "") + ".ufo")
    if "ttf" in flavors:
        if "woff2" in flavors:
            ufo2font(family, masters, "ttf", "woff2")
        else:
            ufo2font(family, masters, "ttf")
    elif "woff2" in flavors:
        ufo2font(family, masters, "woff2")
    if "otf" in flavors:
        ufo2font(family, masters, "otf")
    addSecureSet(family, flavors)

def removeData(family, masters):
    rdir = os.abspath("../src/"+family+"/")
    for master in masters:
        master.data = ""
        # If we have MTI sources, any Adobe feature files derived from
        # the Glyphs file should be ignored. We clear it here because
        # it only contains junk information anyway.
        master.save()
    print("\tremove mti info")

def instances(family, *output, newName=" "):
    securetSetIsIncluded = pan_european_fonts
    mergeable = ["ttf", "woff2"]
    if family not in securetSetIsIncluded:
        temp = list(set(mergeable) & set(output))
        if len(temp) == 0:
            output = ["ttf"]
        else:
            output = temp
    path, folder = getFile(".designspace", "src", family)
    designSpace = openDesignSpace(path)
    destination = folder + "/" + "Instances"
    ###
    ### test if mti
    for file in os.listdir(folder):
        if file.endswith(".plist"):
            masters = designSpace.loadSourceFonts(defcon.Font)
            add_mti_features_to_master_ufos(family, masters)
    ###
    fp = FontProject()
    fonts = fp.run_from_designspace(expand_features_to_instances=True, use_mutatormath=True, \
        designspace_path = path, interpolate = True, output=("otf"), output_dir = destination)
    ufolist = list()
    for ufo in os.listdir(os.path.join(folder, "instance_ufos")):
        if ufo[-4:] == ".ufo":
            ufolist.append(ufo)
    instancesFolder = family+"/instance_ufos"
    for i in output:
        ufo2font(instancesFolder, ufolist, i, fromInstances=True)
        addSecureSet(family, output)
    if newName != " ":
        renameFonts(family, newName)
    removeData()


### TEST FUNCTIONS ###
# mastersUfos2fonts("NotoSansThaana", "woff2")
# designSpace2Var("NotoSansThaana")
# subsetFonts("NotoSerif", "SecureSet")
instances("NotoSansCanadianAboriginal", "ttf")
# subsetFonts("NotoSerif", "CyrillicPro", familyNewName = "Avocado Sans", flavor=["otf"])
# subsetFonts("NotoKufiArabic", ["Core_Arabic"], flavor=["ttf"])
# mastersUfos2fonts("NotoSansThaana", "woff2")
# renameFonts("NotoSans", "Tomato Soup")
# mergeFonts("NotoSans","NotoNastaliqUrdu")
# designSpace2Var("NotoSansThaana")
# makeTTFInstancesFromVF("NotoSerif")
# makeOneInstanceFromVF("NotoSansThaana", {'wght': 190.0})
# mastersUfos2fonts("NotoSansThaana", "ttf")
# ufosToGlyphs("NotoSansThaana")
# ufo2font("NotoSans", ["NotoSans-Bold.ufo"], "ttf")
# instances("NotoSansThaana")
# mergeFonts("NotoSansThaana", "NotoSerifHebrew")