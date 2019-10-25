from Lib.makeThings import ufo2font, ufosToGlyphs
from Lib.findThings import getFile, getFolder
# from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor, BaseDocReader
from fontTools.designspaceLib import *
from fontTools.ttLib import TTFont
from defcon import Font
from fontTools.varLib.mutator import instantiateVariableFont
from fontTools import varLib, ttLib
from defcon import Font
from ufo2ft import compileInterpolatableOTFsFromDS, compileInterpolatableTTFsFromDS, postProcessor
from ufo2ft import compileTTF
from fontTools.subset import Subsetter
from fontTools.subset import Options
import os
import json
from fontTools.merge import Merger
import shutil
from fontmake.font_project import FontProject
from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
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

def mergeFonts(masterfont, *fontsToAdd):
    masters = list()
    dsList = list()
    fonts = list()
    masterLocation = dict()
    masterAxes = list()
    slaveAxes = list()
    localLocation = list()
    neutralLocation = dict()
    testLocation = list()
    trad = {"Weight": "wght", "Width" : "wdth"}
    toMerge = dict()

    path, folder = getFile(".designspace", "src", masterfont)
    print(folder)
    masterDesignSpace = DesignSpaceDocument()
    masterDesignSpace.read(path)
    for f in fontsToAdd:
        path = getFile(".designspace", "src", f)[0]
        designSpace = DesignSpaceDocument()
        designSpace.read(path)
        dsList.append(designSpace)
    # FIND COMMON AXIS IN MASTER AND SLAVE FAMILIES
    for ds in dsList:
        for a in ds.axes:
            slaveAxes.append(a.tag)
            neutralLocation[a.tag] = a.default
    for a in masterDesignSpace.axes:
        if a.tag in slaveAxes:
            masterAxes.append(a.tag)
    # COMPARE COMMON AXIS LOCATION IN MASTER AND SLAVES
    for s in masterDesignSpace.sources:
        localLocation = list()
        for d in s.location:
            localLocation.append([d, s.location[d]])
            for dsSlave in dsList:
                testLocation = list()
                for s2 in dsSlave.sources:
                    for d2 in s2.location:
                        # print(d2)
                        if trad[d2] in masterAxes:
                            testLocation.append([d2, s2.location[d2]])
                        # if there is a tag not shared add the location in list to prevent the 2 list to match
                        if d2 in neutralLocation and neutralLocation[d2] != d2.default:
                            testLocation.append([d2, s2.location[d2]])
                        # print(localLocation, testLocation)
                        if len(localLocation) > 0:
                            if localLocation == testLocation:
                                print(s.filename, s2.filename)
                                masterpath = folder + "/" + s.filename
                                slavepath = folder + "/" + s2.filename
                                toMerge[masterpath] = slavepath
                                # # print(slavepath)
                                # refactoredValue = list()
                                # if masterpath in toMerge:
                                #     # print(toMerge[masterpath])
                                #     for ufo in toMerge[masterpath]:
                                #         # print(ufo)
                                #         refactoredValue.append(str(ufo))
                                #     refactoredValue.append(slavepath)
                                #     # old = toMerge[masterpath]
                                    # toMerge[masterpath] = refactoredValue
                                # else:
                                #     toMerge[masterpath] = slavepath
                    testLocation = list()
    # for i in toMerge:
    #     ufo2font(family, masters, i)
    #     destination = folder + "OTF/"
    #         if not os.path.exists(destination):
    #             os.makedirs(destination)
    #         otf = compileOTF(ufo, removeOverlaps=True)
    #         otf.save(destination + i[:-4] + ".otf")
    #     print(i, ">", toMerge[i])

    newName = s.name + s2.name
    merger = Merger()
    mergedFont = merger.merge(fonts)
    mergedFontPath = os.path.join(cwd, newName + '.otf')
    mergedFont.save(mergedFontPath)





        #         if axis.name != tag:
        #             otherOne = (axis.name, axis.default)
            # for s2 in ds.sources:
            #     # src = SourceDescriptor()
            #     location = dict(s2.location)
            #     print(location)
            #     for t in location:
            #         if t == tag:
            #             if location[t] == dimension[tag]:
            #                 if otherOne[0] in location:
            #                     if location[otherOne[0]] == otherOne[1]:
            #                         print("ok")
                ####
                # for dimension in s2.location:
                #     if dimension == tag:
                #         print(s.name, s2.name)
                #         print("same location")
                        # masters.append(masterfont + "-" + s.styleName.replace(" ", "") + ".ufo")
                        # fonts.append(s2.name + "-" + s2.styleName.replace(" ", "") + ".ufo")
    # newName = s.name + s2.name
    # merger = Merger()
    # mergedFont = merger.merge(fonts)
    # mergedFontPath = os.path.join(cwd, newName + '.otf')
    # mergedFont.save(mergedFontPath)

# def parseMap(descriptor, designSpace):
#     #descriptor is sources or instances, depending on what you want
#     loca = dict()
#     for a in designSpace.axes:
#     if a.map:
#         maps[a.name] = a.map
#     for source in designSpace.sources:
#     location = dict(source.location)
#     for name in location:
#         if name in maps:
#             for i in maps[name]:
#                 if int(location[name]) == int(i[1]):
#                     locationValue = i[0]
#                     # print(instance.name," entry: ", location[name], ", Real value:", locationValue)
#                     loca[axesName[name]] = round(locationValue)
#     return loca


def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

def renameFonts(family, newName, *flavor, codePageRange = []):
    saveName = newName.replace(" ", "")
    flavors = ["OTF", "TTF", "WOFF2", "VAR", "WOFF", 'instances']
    for i in flavor:
        if os.path.exists((getFolder(family) + "fonts/" + i.upper())):
            pass
        else:
            mastersUfos2fonts(family, i)
    path = getFolder(family) + "fonts/"
    fontsFolders = [path + i for i in os.listdir(path) if i.split("/")[-1] in flavors]
    for folder in fontsFolders:
        fonts = [folder + "/" + font for font in os.listdir(folder) if font.split(".")[-1].upper() in flavors]
        for f in fonts:
            renamedFont = ttLib.TTFont(f)
            for namerecord in renamedFont['name'].names:
                namerecord.string = namerecord.toUnicode()
                if namerecord.nameID == 2:
                    WeightName = namerecord.string
                if namerecord.nameID == 17:
                    WeightName = namerecord.string
            for namerecord in renamedFont['name'].names:
                namerecord.string = namerecord.toUnicode()
                if namerecord.nameID == 1:
                    if WeightName in ["Bold", "Regular"]:
                        namerecord.string = newName
                    else:
                        namerecord.string = newName + " " + WeightName
                if namerecord.nameID == 3:
                    for namerecord in renamedFont['name'].names:
                        namerecord.string = namerecord.toUnicode()
                        if namerecord.nameID == 4:
                            namerecord.string = newName + " " + WeightName
                        if namerecord.nameID == 5:
                            Version = namerecord.string.split(" ")[1]
                            V_major, V_minor = Version.split(".")[0], Version.split(".")[0]
                    namerecord.string = V_major + "." + V_minor + ";GOOG;" + newName + WeightName
                if namerecord.nameID == 17:
                    namerecord.string = WeightName
                        # unicID = namerecord.string.split(";")
                        # unicID = l[0] + ";" + l[1] + ";" + newName + "-"  + WeightName
                        # namerecord.string = unicID
                    # PSName = ''.join(newName.split(' ')) + '-' + ''.join(WeightName.split(' '))
                    # namerecord.string = '%s.%s' % (V_major, V_minor) +';'+ '%s' % PSName + ';'
                # if namerecord.nameID == 4:
                #     namerecord.string = newName + " " + WeightName
                if namerecord.nameID == 6:
                    namerecord.string = ''.join(newName.split(' ')) + '-' + ''.join(WeightName.split(' '))
                if namerecord.nameID == 16:
                    namerecord.string = newName
            os2cp1 = renamedFont['OS/2'].ulCodePageRange1
            os2cp1 = 0
            print("before", os2cp1)
            print('{0:b}'.format(os2cp1))
            for i in codePageRange:
                os2cp1 = setBit(os2cp1, i)
            print("after", os2cp1)
            format_ = f[-3:].upper()
            destination = getFolder(family) + "/" + newName + "/" + format_
            fontName = saveName + "-" + ''.join(WeightName.split(' ')) + f[-4:]
            if not os.path.exists(destination):
                os.makedirs(destination)
            renamedFont.save(os.path.join(destination, fontName))

def mastersUfos2fonts(family, *flavor):
    print(len(flavor), flavor)
    if len(flavor) == 0:
        flavor = "ttf"
    masters = []
    path, folder = getFile(".designspace", "src", family)
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    for s in designSpace.sources:
        masters.append(family + "-" + s.styleName.replace(" ", "") + ".ufo")
    if "ttf" in flavor:
        print("in flavor")
        if "woff2" in flavor:
            ufo2font(family, masters, "ttf", "woff2")
        else:
            ufo2font(family, masters, "ttf")
    elif "woff2" in flavor:
        ufo2font(family, masters, "woff2")
    if "otf" in flavor:
        ufo2font(family, masters, "otf")

def openDesignSpace(path):
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    return designSpace

def instances(family, *output):
    path, folder = getFile(".designspace", "src", family)
    designSpace = openDesignSpace(path)
    destination = folder + "/" + "Instances"
    # if not os.path.exists(destination):
    #     os.makedirs(destination)
    ft = FontProject()
    fonts = ft.run_from_designspace(use_mutatormath=True, designspace_path = path, interpolate = True, output=("otf"), output_dir = destination)
    print(fonts)

def designSpace2Var(family):
    print("1")
    path, folder = getFile(".designspace", "src", family)
    designSpace = openDesignSpace(path)
    designSpace.loadSourceFonts(Font)
    print("2")
    font, _, _ = varLib.build(compileInterpolatableTTFsFromDS(designSpace, \
                    featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter]), optimize=False)
    destination = folder + "/fonts/VAR"
    if not os.path.exists(destination):
        os.makedirs(destination)
    print("3")
    font.save(os.path.join(destination, family + "_VF.ttf"))

def makeCompatibleOTF(family):
    path, folder = getFile("_cleaned.designspace", "src", family)
    designSpace = openDesignSpace(path)
    designSpace.loadSourceFonts(Font)
    for s in compileInterpolatableOTFsFromDS(designSpace).sources:
        name = s.name.replace(" ", "") + ".otf"
        otf = s.font
        otf.save(folder + "/_compatibles/" + name)

def makeTTFInstancesFromVF(family):
    axesName = dict()
    path, folder = getFile(".designspace", "src", family)
    designSpace = openDesignSpace(path)
    loca = dict()
    maps = dict()
    for a in designSpace.axes:
        if a.map:
            maps[a.name] = a.map
    varFontPath = folder + "/fonts/VAR/" + family + "_VF.ttf"
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
                namerecord.string = familyName
            if namerecord.nameID == 2:
                namerecord.string = styleName
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

def subsetFonts(family, *writingSystem, flavor=["ttf"], familyNewName=" "):
    latinProCodePageRange = [0, 1, 4, 7, 8]
    cyrProCodePageRange = [2]
    greekProCodePageRange = [3]
    unicodePageRangeDict = {"Cyrillic":latinProCodePageRange, "CyrillicPro":latinProCodePageRange, "Greek" : greekProCodePageRange, "Latin" : latinProCodePageRange}
    pageRangeToApply = []
    subsetFolder = ""
    for i in writingSystem:
        subsetFolder += i
    formats = ["ttf", "woff", "woff2", "otf"]
    toKeep = list()
    folder = getFolder(family)
    options = Options()
    options.layout_features = '*'  # keep no GSUB/GPOS features
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
    jsonpath = [folder + json for json in os.listdir(folder) if ".json" in json]
    for i in jsonpath:
        with open(i, 'r') as subsetDict:
            subset = json.load(subsetDict)
    for i in subset:
        if i in writingSystem:
            toKeep.append(subset[i])
        if i in writingSystem:
            print(i)
            pageRangeToApply += unicodePageRangeDict[i]
    print(pageRangeToApply)
    for i in toKeep:
        keep += i
    for i in flavor:
        if not os.path.exists(folder + "/fonts/" + i.upper()):
            mastersUfos2fonts(family, i)
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
                        print(WeightName)
                subsetter = Subsetter(options=options)
                subsetter.populate(glyphs=keep)
                subsetter.subset(newfont)
                destination = folder + "fonts/" + subsetFolder + "_subset/fonts/"
                if not os.path.exists(destination + i.upper()):
                    os.makedirs(destination + i.upper())
                newfont.save(destination + i.upper() + "/" + family + subsetFolder + "-" + WeightName +"." + i)
    folder = family + "/fonts/" + subsetFolder + "_subset"
    print(pageRangeToApply)
    if familyNewName != " ":
        renameFonts(folder, familyNewName, codePageRange = pageRangeToApply)
    else:
        familyNewName = family + subsetFolder
        renameFonts(folder, familyNewName, codePageRange = pageRangeToApply)
    shutil.rmtree(destination)

# subsetFonts("NotoSans", "Cyrillic")
subsetFonts("NotoSans", "Latin", familyNewName = "Avocado Sans")
# subsetFonts("NotoSans", "Cyrillic", "ttf")
# mastersUfos2fonts("NotoSansThaana", "woff2")
# renameFonts("NotoSans", "Never Sans")
# mergeFonts("NotoSans","NotoNastaliqUrdu")
# designSpace2Var("NotoSansThaana")
# makeTTFInstancesFromVF("NotoSansThaana")
# mastersUfos2fonts("NotoSans", "ttf")
# ufosToGlyphs("NotoSansThaana")
# ufo2font("NotoSans", ["NotoSans-Bold.ufo"], "ttf")
# instances("NotoSansThaana")
# mergeFonts("NotoSansThaana", "NotoSerifHebrew")