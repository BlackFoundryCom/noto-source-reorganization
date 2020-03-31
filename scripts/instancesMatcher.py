import os
import json
import shutil

from Ufo2fontsFromdesignSpace import *

from fontTools.designspaceLib import *
from fontTools.ttLib          import TTFont
from fontTools.varLib.mutator import instantiateVariableFont
from fontTools                import varLib, ttLib
from defcon                   import Font
from ufo2ft                   import compileInterpolatableOTFsFromDS, compileInterpolatableTTFsFromDS, postProcessor
from ufo2ft                   import compileTTF
from fontTools.subset         import Subsetter
from fontTools.subset         import Options
from fontTools.merge          import Merger
from fontmake.font_project    import FontProject
from ufo2ft.featureWriters    import (
                                     KernFeatureWriter,
                                     MarkFeatureWriter,
                                     loadFeatureWriters,
                                     ast,
                                     )
from fontTools.designspaceLib import (
                                     DesignSpaceDocument,
                                     AxisDescriptor,
                                     SourceDescriptor,
                                     InstanceDescriptor,
                                     BaseDocReader
                                     )


# def getFile(extension, directory):
#     repo = "../src/" + directory + "/"
#     cwd = os.getcwd()
#     rdir = os.path.abspath(repo)
#     source = rdir + "/" + directory + extension
#     return source, rdir

# def getFolder(directory):
#     rdir = os.path.abspath(os.path.join("../src/", directory))
#     return rdir

def compareLocation(masterDesignSpace, dsList, slaveAxes, masterAxes, neutralLocation):
    trad = {"Weight": "wght", "Width" : "wdth"}
    trad2 = {"wght": "Weight", "wdth" : "Width"}
    masterSourcesLoca, slaveSourcesLoca, allSlaveSourcesLoca = list(), list(), list()
    commonMasters = []
    commonAxes = set(slaveAxes) & set(masterAxes)
    diffAxes  = set(slaveAxes) - set(masterAxes)
    for s in masterDesignSpace.sources:
        for dimension in s.location:
            masterSourcesLoca.append([dimension, s.location[dimension], s.filename])
    for dsSlave in dsList:
        for srcSlave in dsSlave.sources:
            for dimSlave in srcSlave.location:
                if trad[dimSlave] in diffAxes and srcSlave.location[dimSlave] == neutralLocation[trad[dimSlave]]:
                    slaveSourcesLoca.append([dimSlave, srcSlave.location[dimSlave], srcSlave.filename])
        allSlaveSourcesLoca.append(slaveSourcesLoca)
        print("all >> ", allSlaveSourcesLoca)

def compareStyles(masterDesignSpace, dsList):
    masterStyles = dict()
    slaveStyles = dict()
    allSlave = list()
    matchingStyles = list()
    todo = list()
    matchingInstances = list()
    for i in masterDesignSpace.instances:
        masterStyles[i.styleName] = ("".join(i.familyName.split(" ")), i.styleName, i.location)
    for ds in dsList:
        for i in ds.instances:
            if i.styleName in masterStyles:
                slaveStyles[i.styleName] = ("".join(i.familyName.split(" ")), i.styleName, i.location)
                if i.styleName not in matchingStyles:
                    refactoredStyleName = i.styleName.replace(" ", "")
                    matchingStyles.append(refactoredStyleName)
        allSlave.append(slaveStyles)
        slaveStyles = dict()
    for i in matchingStyles:
        try:
            for s in allSlave:
                matchingInstances.append(s[i])
            matchingInstances.append(masterStyles[i])
        except:
            pass
        todo.append(matchingInstances)
        matchingInstances = []

    return todo


def getDesignspace(masterfont, *fontsToAdd):
    dsList = []
    slaveAxes = []
    localLocation = list()
    neutralLocation = dict()
    testLocation = list()
    masterAxes = list()
    trad = {"Weight": "wght", "Width" : "wdth"}
    path, folder = getFile(".designspace", masterfont)
    masterDesignSpace = DesignSpaceDocument()
    masterDesignSpace.read(path)
    # read masterdesignspace of each fonts to merge into master family,
    # and put it in a list
    for f in fontsToAdd:
        path = getFile(".designspace", f)[0]
        designSpace = DesignSpaceDocument()
        designSpace.read(path)
        dsList.append(designSpace)
    # FIND COMMON NAME AXIS IN MASTER AND SLAVE FAMILIES
    for ds in dsList:
        for a in ds.axes:
            slaveAxes.append(a.tag)
            neutralLocation[a.tag] = a.default
    for a in masterDesignSpace.axes:
        if a.tag in slaveAxes:
            masterAxes.append(a.tag)

    return masterDesignSpace, dsList, slaveAxes, masterAxes, neutralLocation

def simpleMerger(fontsPath, style, newName, onlySecureSet=False): #path of actual fonts
    print("start merging")
    merger = Merger()
    print(fontsPath)
    mergedFont = merger.merge(fontsPath)
    destination = newFolderForMerged("NotoCombined/fonts/TTF")
    if not os.path.exists(destination):
        os.makedirs(destination)
    mergedFontPath = os.path.join(destination, "NotoCombined"+style+".ttf")
    mergedFont.save(mergedFontPath)
    print(mergedFontPath)
    renameFonts("NotoCombined", newName)

    return os.path.abspath(os.path.join(destination, os.pardir))

def mergeFonts(masterfont, *fontsToAdd):
    trad = {"Weight": "wght", "Width" : "wdth"}
    masterDesignSpace, dsList, slaveAxes, masterAxes, neutralLocation = getDesignspace(masterfont, *fontsToAdd)
    # compareLocation(masterDesignSpace, dsList, slaveAxes, masterAxes, neutralLocation)
    todo = compareStyles(masterDesignSpace, dsList)
    basefonts = [masterfont]
    for i in fontsToAdd:
        basefonts.append(i)
    for i in basefonts:
        varFontPath = getFile(".designspace", i)[1] + "/fonts/VAR/" + i + "-VF.ttf"
    for match in todo:
        if len(match) > 0:
            todolist = []
            for instance in match:
                ufoList = list()
                familyPath = getFolder(instance[0])
                for element in os.listdir(familyPath):
                    if element.endswith(".ufo"):
                        ufoList.append(element)
                if len(ufoList) > 1:
                    loca = dict()
                    style = instance[1]
                    location = instance[2]
                    for loc in location:
                        loca[trad[loc]] = location[loc]
                    makeOneInstanceFromVF(instance[0], loca)
                    path = getFolder(instance[0]) + "/fonts/static"
                    todolist.append(os.path.join(path, instance[0]+"-"+instance[1]+".ttf"))
                else:
                    style = instance[1]
                    makeVanillaFamily(os.path.split(familyPath)[1], 'ttf')
                    path = getFolder(instance[0]) + "/fonts/TTF"
                    todolist.append(os.path.join(path, instance[0]+"-"+instance[1]+".ttf"))
            # print(todolist)
            newName = masterfont.replace("Noto", "")
            for i in fontsToAdd:
                newName += i.replace("Noto", "")
            temp = simpleMerger(todolist, style, newName)
    shutil.rmtree(temp)

#############
### TEST ####
#############
def testMerge():
    l = [mergeFonts("NotoSans", "NotoSansArabic"), #> working
        mergeFonts("NotoMusic", "NotoSansThaana"), #> working
        mergeFonts("NotoSerifHebrew", "NotoKufiArabic", "NotoSerif"), #> working
        mergeFonts("NotoSansThaana", "NotoSerifHebrew") # not woking
        ]                                               # because no GSUB in NotoSansThaana
                                                        # that is given in second to the merger
    for i in l:
        try:
            i
        except Exception as e:
            pass