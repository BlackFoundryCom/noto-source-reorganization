# import subprocess
import os
import plistlib
import shutil

import defcon
import glyphsLib
import ufoLib2
from fontTools.misc.plistlib import load as readPlist
from fontTools.designspaceLib import DesignSpaceDocument

from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
    )
from ufo2ft.featureCompiler import FeatureCompiler, MtiFeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler


# compilateur => featureCompilerClass = MtiFeatureCompiler

"""
    TODO:
    — dl noto sources repo with submodule with Action?
    — Convert Glyphs sources into UFO + Designspace folders DONE
    — Clean Designspace ?
    — Clean glyph order Done
    — rewrite kerning.plist and groups.plist WIP
    — Check if ufo2ft needs to have "featureCompilerClass = MtiFeatureCompiler" in arg to generate features
        or if it detects the com.github.googlei18n.ufo2ft.mtiFeatures/*.mti data
    — For now copy mti files in the font folder
"""


class sourcesBuilder():

    def __init__(self, fileName, hasMtiFiles = False):
        self.notoSourcesPath = "../noto-source/src"
        self.fileName = fileName
        self.foldername = self.fileName.split(".")[0].replace("-MM", "")
        if hasMtiFiles:
            self.destination = os.path.join("../src", os.path.dirname(self.foldername))
        else:
            self.destination = os.path.join("../src", self.foldername)
        self.sourcePath = os.path.join(self.notoSourcesPath, self.fileName)

    def convertion(self):
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)
        self.ufos, self.designspace_path = glyphsLib.build_masters(self.sourcePath, self.destination)
        self.cleanedUfos = self.cleanUfos()

        return self.designspace_path, self.cleanUfos

    def cleanUfos(self):
        glyphOrder = list()
        for ufoPath in self.ufos:
            # if i.endswith(".ufo"):
            ufo = ufoLib2.Font.open(os.path.join(self.destination, ufoPath))
            for g in ufo:
                glyphOrder.append(g.name)
            ufo.glyphOrder = glyphOrder
            ufo.save()

# class test():
#     def __init__(self, folderName):
#         self.notoSourcesPath = "../noto-source/src/"
#         self.folderName = folderName
#         self.destination = os.path.join("../src", self.folderName)
#         for i in os.listdir(os.path.join(self.notoSourcesPath, self.folderName)):
#             if i.endswith(".glyphs"):
#                 print(self.folderName+"/"+i)
#                 tp = test2(self.folderName+"/"+i, hasMtiFiles=True)
#                 # self.designSpacePath, self.ufos = typeface.convertion()

# class test2():

#     def __init__(self, fileName, hasMtiFiles = False):
#         self.notoSourcesPath = "../noto-source/src"
#         self.fileName = fileName
#         self.foldername = self.fileName.split(".")[0].replace("-MM", "")
#         if hasMtiFiles:
#             self.destination = os.path.join("../src", os.path.dirname(self.foldername))
#         else:
#             self.destination = os.path.join("../src", self.foldername)
#         self.sourcePath = os.path.join(self.notoSourcesPath, self.fileName)
#         print(self.destination)


class complexSourcesBuilder():

    def __init__(self, folderName):
        self.notoSourcesPath = "../noto-source/src/"
        self.folderName = folderName
        self.destination = os.path.join("../src", self.folderName)
        for i in os.listdir(os.path.join(self.notoSourcesPath, self.folderName)):
            if i.endswith(".glyphs"):
                typeface = sourcesBuilder(self.folderName+"/"+i, hasMtiFiles=True)
                self.designSpacePath, self.ufos = typeface.convertion()

    @property
    def designSpaceDocument(self):
        designSpace = DesignSpaceDocument()
        designSpace.read(self.designSpacePath)
        return designSpace

    @property
    def masters(self):
        return self.designSpaceDocument.loadSourceFonts(defcon.Font)

    def copy_mti_files(self):
        familyFolder = os.path.join(self.notoSourcesPath, self.folderName)
        for i in os.listdir(familyFolder):
            if i.endswith(".txt") or i.endswith(".plist"):
                shutil.copyfile(os.path.join(familyFolder, i), os.path.join(self.destination, i))

    def add_mti_features_to_ufos(self):
        oneOrMorePlist = list()
        for i in os.listdir(os.path.join(self.notoSourcesPath, self.folderName)):
            if i.endswith(".plist"):
                oneOrMorePlist.append(i)
        if len(oneOrMorePlist) == 1:
            mti_source = os.path.join(self.notoSourcesPath+self.folderName, oneOrMorePlist[0])
            with open(mti_source, "rb") as mti:
                mti_paths = readPlist(mti)
                for master in self.masters:
                    key = master.info.familyName.replace(" ", "")+"-"+master.info.styleName.replace(" ", "")
                    for table, path in mti_paths[key].items():
                        with open(os.path.join(os.path.join(self.notoSourcesPath, self.folderName), path), "rb") as mti_:
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
                print("\tufos updated with MTI data")


class rebuiltKerningfromOTFea():

    def __init__(self, folder):
        self.folder = folder

    def generateFeatures(self):
        for ufo in os.listdir(self.folder):
            if ufo.endswith("-Condensed.ufo"):
                print(ufo)
                ft = defcon.Font(os.path.join(self.folder, ufo))
                outlines = OutlineOTFCompiler(ft).compile()
                feaCompiler = FeatureCompiler(ft, outlines, featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter()])
                # feaCompiler = FeatureCompiler(ft, outlines, featureCompilerClass = MtiFeatureCompiler)
                print("compile")
                feaCompiler.compile()
                with open(os.path.join(self.folder, "features_full.fea"), "w+") as fea:
                    fea.write(feaCompiler.features)
                self.feaAsList = feaCompiler.features.split(";")


    def dumpGroupsDotPlist(self):
        kernGrps = dict()
        for i in self.feaAsList:
            #Deals with Groups
            if "=" in i:
                if "@kern1." in i:
                    i = i.replace("@", "public.")
                    cleanUp = i.split("=")[1].replace("\n", "").split(" ")
                    cleanUp = [g.strip('[];') for g in cleanUp if cleanUp != '']
                    kernGrps[i.split("=")[0].replace("\n", "").strip(" ")] = cleanUp
                elif "@kern2." in i:
                    i = i.replace("@", "public.")
                    cleanUp = i.split("=")[1].replace("\n", "").split(" ")
                    cleanUp = [g.strip('[];') for g in cleanUp if cleanUp != '']
                    kernGrps[i.split("=")[0].replace("\n", "").strip(" ")] = cleanUp
        with open(os.path.join(self.folder, "test_groups.plist"), "bw+") as grp:
            grp.write(plistlib.dumps(kernGrps))


    def dumpKerningDotPlist(self):
        kerningDict = dict()
        for i in self.feaAsList:
            #Deals with kerning entries
            if "pos " in i or "positions " in i:
                if "<anchor" not in i and "[" not in i:
                    # RTL detection
                    if "<" in i: #kerning value written in the <int int int int> way is for RTL scripts
                        print(i)
                        k = i.replace("\n", "").strip(";").split(" ")[-6:-3] #keep glyph or group name and kerning value
                        print(k)
                        kernValue = int(k[2].strip("<"))
                        k[0] = k[0].replace("@", "public.")
                        k[1] = k[1].replace("@", "public.")
                        if k[1] not in kerningDict:
                            kerningDict[k[1]] = {k[0]:kernValue}
                        else:
                            kerningDict[k[1]][k[0]] = kernValue
                    else:# LTR kerning
                        k = i.replace("\n", "").strip(";").split(" ")[-3:] #keep glyph or group name and kerning value
                        kernValue = int(k[2])
                        k[0] = k[0].replace("@", "public.")
                        k[1] = k[1].replace("@", "public.")
                        if k[0] not in kerningDict:
                            kerningDict[k[0]] = {k[1]:kernValue}
                        else:
                            kerningDict[k[0]][k[1]] = kernValue
        with open(os.path.join(self.folder, "test_kerning.plist"), "bw+") as kerning:
            kerning.write(plistlib.dumps(kerningDict))


# ft = complexSourcesBuilder("NotoSerifKhmer")
# ft.copy_mti_files()
# kern = rebuiltKerning("/Users/JBMZ/Documents/PRO/BlackF/BF_GOOGLE_Noto_reorg/src/NotoSerifHebrew")
# kern.generateFeatures()
# kern.dumpGroupsDotPlist()
# kern.dumpKerningDotPlist()

# def organizeSources():
#     notoSourcesDir = "../noto-source/src"
#     destination = "../src"
#     os.change(os.path.basename(self.notoSourcesDir))
#     subprocess.run(["git submodule add https://github.com/googlefonts/noto-source"], shell=True, check=True)


if __name__ == '__main__':
    NotoSources = "../noto-source/src"
    fail = []
    for i in os.listdir(NotoSources):
        if i.startswith("Noto"):
            if i.endswith(".glyphs"):
                print(i)
                try:
                    typeface = sourcesBuilder(i)
                    typeface.convertion()
                except:
                    fail.append(i)
            elif os.path.isdir(os.path.join(NotoSources, i)):
                print(i)
                typeface = complexSourcesBuilder(i)
                typeface.copy_mti_files()
    for f in fail:
        print(f, "didn't work")