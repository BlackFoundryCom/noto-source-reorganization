from Lib.findThings import getFile
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

"""


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
    #Read Master designspace
    path, folder = getFile(".designspace", "src", masterfont)
    print(folder)
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
    commonAxes = set(slaveAxes) & set(masterAxes)
    diffAxes  = set(slaveAxes) - set(masterAxes)
    print("Axes in common: ",  commonAxes)
    print("Axes NOT in common: ", diffAxes)
    # COMPARE COMMON AXIS LOCATION IN MASTER AND SLAVES
    for s in masterDesignSpace.sources:
        localLocation = list()
        for d in s.location:
            localLocation.append([d, s.location[d]])
            # print(([d, s.location[d]]))
            for dsSlave in dsList:
                testLocation = list()
                for srcSlave in dsSlave.sources:
                    for d2 in srcSlave.location:
                        if trad[d2] in masterAxes:
                            # print(d2, trad[d2], masterAxes)
                            testLocation.append([d2, srcSlave.location[d2]])
                            print(testLocation)
                        # if there is a tag not shared add the location in list to prevent the 2 list to match
                        if d2 in neutralLocation and neutralLocation[d2] != d2.default:
                            testLocation.append([d2, srcSlave.location[d2]])
                        # print(localLocation, testLocation)
                        if len(localLocation) > 0:
                            if localLocation == testLocation:
                                # print(s.filename, srcSlave.filename)
                                masterpath = folder + "/" + s.filename
                                slavepath = folder + "/" + srcSlave.filename
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

    # newName = s.name + srcSlave.name
    # merger = Merger()
    # mergedFont = merger.merge(fonts)
    # mergedFontPath = os.path.join(cwd, newName + '.otf')
    # mergedFont.save(mergedFontPath)





        #         if axis.name != tag:
        #             otherOne = (axis.name, axis.default)
            # for srcSlave in ds.sources:
            #     # src = SourceDescriptor()
            #     location = dict(srcSlave.location)
            #     print(location)
            #     for t in location:
            #         if t == tag:
            #             if location[t] == dimension[tag]:
            #                 if otherOne[0] in location:
            #                     if location[otherOne[0]] == otherOne[1]:
            #                         print("ok")
                ####
                # for dimension in srcSlave.location:
                #     if dimension == tag:
                #         print(s.name, srcSlave.name)
                #         print("same location")
                        # masters.append(masterfont + "-" + s.styleName.replace(" ", "") + ".ufo")
                        # fonts.append(srcSlave.name + "-" + srcSlave.styleName.replace(" ", "") + ".ufo")
    # newName = s.name + srcSlave.name
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

mergeFonts("NotoSansThaana", "NotoSerifHebrew")