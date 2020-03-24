from Lib.makeThings import ufo2font
from Lib.findThings import getFile, getFolder
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor, BaseDocReader
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
from Ufo2fontsFromdesignSpace import *

"""


"""

def compareLocation(masterDesignSpace, dsList, slaveAxes, masterAxes, neutralLocation):
    trad = {"Weight": "wght", "Width" : "wdth"}
    trad2 = {"wght": "Weight", "wdth" : "Width"}
    masterSourcesLoca, slaveSourcesLoca, allSlaveSourcesLoca = list(), list(), list()
    commonMasters = []
    commonAxes = set(slaveAxes) & set(masterAxes)
    diffAxes  = set(slaveAxes) - set(masterAxes)
    for s in masterDesignSpace.sources:
        for dimension in s.location:
            # print(dimension, s.location[dim], s.filename)
            masterSourcesLoca.append([dimension, s.location[dimension], s.filename])
    for dsSlave in dsList:
        for srcSlave in dsSlave.sources:
            for dimSlave in srcSlave.location:
                # print(dimSlave, srcSlave.location[dimSlave], srcSlave.filename)
                # if trad[dimSlave] in diffAxes:
                #     print(srcSlave.location[dimSlave], neutralLocation[trad[dimSlave]])
                if trad[dimSlave] in diffAxes and srcSlave.location[dimSlave] == neutralLocation[trad[dimSlave]]:
                    slaveSourcesLoca.append([dimSlave, srcSlave.location[dimSlave], srcSlave.filename])
                    # for aaa in commonAxes:
                    #     print(trad2[aaa])
                    #     print(srcSlave.filename, srcSlave.location[trad2[aaa]])
                # print(slaveSourcesLoca)
        allSlaveSourcesLoca.append(slaveSourcesLoca)
        print("all >> ", allSlaveSourcesLoca)
    # for family in allSlaveSourcesLoca:
    #     print(family)
        # for font in family:
        #     print(font)
            # for i in  masterSourcesLoca:
            #     # if font[1] == i[1]:
            # # if font[1] in masterSourcesLoca:
            #     print(font[1], i[1])

    # print(masterSourcesLoca, allSlaveSourcesLoca)

def compareStyles(masterDesignSpace, dsList):
    masterStyles = dict()
    slaveStyles = dict()
    allSlave = list()
    matchingStyles = list()
    todo = list()
    matchingInstances = list()
    for i in masterDesignSpace.instances:
        masterStyles[i.styleName] = (i.familyName, i.styleName, i.location)
    for ds in dsList:
        for i in ds.instances:
            if i.styleName in masterStyles:
                slaveStyles[i.styleName] = (i.familyName, i.styleName, i.location)
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
        print("\n", matchingInstances)
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
    path, folder = getFile(".designspace", "src", masterfont)
    masterDesignSpace = DesignSpaceDocument()
    masterDesignSpace.read(path)
    #read masterdesignspace of each fonts to merge into master family, and put it in a list
    for f in fontsToAdd:
        path = getFile(".designspace", "src", f)[0]
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
    #test with sets
    # commonAxes = set(slaveAxes) & set(masterAxes)
    # diffAxes  = set(slaveAxes) - set(masterAxes)
    # print("Axes in common: ",  commonAxes)
    # print("Axes NOT in common: ", diffAxes)
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
        varFontPath = getFile(".designspace", "src", i)[1] + "/fonts/VAR/" + i + "-VF.ttf"
        if not os.path.exists(varFontPath):
            designSpace2Var(i)
        else:
            print(i, "Variable already exists")
    print("todo", todo)
    for match in todo:
        if len(match) > 0:
            todolist = []
            for instance in match:
                loca = dict()
                style = instance[1]
                location = instance[2]
                for loc in location:
                    loca[trad[loc]] = location[loc]
                    #print("loca\t", loca, instance[0])
                makeOneInstanceFromVF(instance[0], loca)
                path = getFolder(instance[0]) + "fonts/static"
                todolist.append(os.path.join(path, instance[0]+"-"+instance[1]+".ttf"))
            newName = masterfont.replace("Noto", "")
            for i in fontsToAdd:
                newName += i.replace("Noto", "")
            temp = simpleMerger(todolist, style, newName)
    shutil.rmtree(temp)

    # if len(todo) != 0:
    #     print("Now it makes variable of each fam")
        # print(type(todo))
        # for match in todo:
        #     print(match)
            # for i in match:
            #     print(i)
            #     print("it extract the" % "instance, the merges all of them " % font)


#mergeFonts("NotoSans", "NotoSansArabic") #> working
mergeFonts("NotoSans", "NotoSansThaana") #> working
# mergeFonts("NotoSerifHebrew", "NotoKufiArabic", "NotoSerif") #> working
# mergeFonts("NotoSansThaana", "NotoSerifHebrew") # not woking because no GSUB in NotoSansThaana that is given in second to the merger