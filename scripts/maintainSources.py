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
        self.notoSourcesPath = "../temp"
        self.fileName = fileName
        self.foldername = self.fileName.split(".")[0].replace("MM", "").strip("-")
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
                if i.endswith(".plist") and "-" in i:
                    old = os.path.abspath(os.path.join(self.destination, i))
                    cleaned = i.split("-")[0] + ".plist"
                    new = os.path.abspath(os.path.join(self.destination, cleaned))
                    os.rename(old, new)

    """
        Don't add mti path in ufo datas,
        because it will prevent OpenType features to work, once added.
        Or Do it only if no OT fea could been added.
    """
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

# def organizeSources():
#     notoSourcesDir = "../noto-source/src"
#     destination = "../src"
#     os.change(os.path.basename(self.notoSourcesDir))
#     subprocess.run(["git submodule add https://github.com/googlefonts/noto-source"], shell=True, check=True)

if __name__ == '__main__':
    source2update = "../temp"
    fail = []
    glyphsFile = False
    for i in os.listdir(source2update):
        if i.startswith("Noto"):
            if i.endswith(".glyphs"):
                print(i)
                try:
                    typeface = sourcesBuilder(i)
                    typeface.convertion()
                    ####
                    # for j in os.listdir(os.path.join("../src", i)):
                    #     if j.endswith(".designspace"):
                    #         if "-" in j:
                    #             clean = i + ".designspace"
                    #             old = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, j))
                    #             new = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, clean))
                    #             os.rename(old, new)
                    ####
                except:
                    fail.append(i)
            elif os.path.isdir(os.path.join(source2update, i)):
                print(i)
                for i in os.listdir(os.path.join(source2update, i)):
                    if i.endswith(".glyphs"):
                        glyphsFile = True
                if glyphsFile is True:
                    try:
                        typeface = complexSourcesBuilder(i)
                        typeface.copy_mti_files()
                    except:
                        fail.append(i)
                else:
                    familyFolder = os.path.join(source2update, i)
                    for f in os.listdir(familyFolder):
                        if f.endswith(".txt") or f.endswith(".plist"):
                            shutil.copyfile(os.path.join(familyFolder, f), os.path.join(destination, f))
                            if f.endswith(".plist") and "-" in f:
                                old = os.path.abspath(os.path.join(destination, f))
                                cleaned = f.split("-")[0] + ".plist"
                                new = os.path.abspath(os.path.join(destination, cleaned))
                                os.rename(old, new)

    for f in fail:
        print(f, "didn't work")
    # for i in os.listdir("../src"):
    #     if "DS_Store" not in i:
    #         for j in os.listdir(os.path.join("../src", i)):
    #             if j.endswith(".designspace"):
    #                 if "-" in j:
    #                     clean = i + ".designspace"
    #                     old = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, j))
    #                     new = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, clean))
    #                     os.rename(old, new)
            # for j in os.listdir(os.path.join("../src", i)):
            #     if j.endswith(".designspace"):
            #         if j.split(".")[0] != i:
            #             print(i, "\n",j.split(".")[0])
            #             old = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, j))
            #             new = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, i+".designspace"))
            #             os.rename(old, new)