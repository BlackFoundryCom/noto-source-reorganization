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

class sourcesBuilder():

    def __init__(self, fileName, hasMtiFiles = False):
        self.notoSourcesPath = "../temp"
        self.fileName = fileName
        self.foldername = self.fileName.split(".")[0].replace("MM", "").strip("-")
        if hasMtiFiles:
            self.destination = os.path.join("../srcTest", os.path.dirname(self.foldername))
        else:
            self.destination = os.path.join("../srcTest", self.foldername)
        self.sourcePath = os.path.join(self.notoSourcesPath, self.fileName)

    def convertion(self):
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)
        self.ufos, self.designspace_path = glyphsLib.build_masters(self.sourcePath, self.destination)
        self.cleanedUfos = self.cleanUfos()

        for i in os.listdir(self.destination):
            if i.endswith(".designspace") and "-" in i:
                old = os.path.abspath(os.path.join(self.destination, i))
                print(self.foldername)
                new = os.path.abspath(os.path.join(self.destination, i.split("-")[0] + ".designspace"))
                print(old, "\n",new)
                os.rename(old, new)

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
#         self.notoSourcesPath = "../noto-source/srcTest/"
#         self.folderName = folderName
#         self.destination = os.path.join("../srcTest", self.folderName)
#         for i in os.listdir(os.path.join(self.notoSourcesPath, self.folderName)):
#             if i.endswith(".glyphs"):
#                 print(self.folderName+"/"+i)
#                 tp = test2(self.folderName+"/"+i, hasMtiFiles=True)
#                 # self.designSpacePath, self.ufos = typeface.convertion()

# class test2():

#     def __init__(self, fileName, hasMtiFiles = False):
#         self.notoSourcesPath = "../noto-source/srcTest"
#         self.fileName = fileName
#         self.foldername = self.fileName.split(".")[0].replace("-MM", "")
#         if hasMtiFiles:
#             self.destination = os.path.join("../srcTest", os.path.dirname(self.foldername))
#         else:
#             self.destination = os.path.join("../srcTest", self.foldername)
#         self.sourcePath = os.path.join(self.notoSourcesPath, self.fileName)
#         print(self.destination)


class complexSourcesBuilder():

    def __init__(self, folderName):
        self.notoSourcesPath = "../temp"
        self.folderName = folderName
        self.destination = os.path.join("../srcTest", self.folderName)
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
                    # for j in os.listdir(os.path.join("../srcTest", i)):
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
                for f in os.listdir(os.path.join(source2update, i)):
                    if f.endswith(".glyphs"):
                        glyphsFile = True
                if glyphsFile is True:
                    try:
                        typeface = complexSourcesBuilder(i)
                        typeface.copy_mti_files()
                    except:
                        fail.append(i)
                else:
                    if "MM" in i:
                        foldername.replace("MM", "").strip("-")
                    destination = os.path.join("../srcTest", foldername)
                    familyFolder = os.path.join(source2update, i)
                    for f in os.listdir(familyFolder):
                        if f.endswith(".ufo") or f.endswith(".fea") or f.endswith(".designspace"):
                            shutil.copyfile(os.path.join(familyFolder, f), os.path.join(destination, f))

    for f in fail:
        print(f, "didn't work")
    # for i in os.listdir(source2update):
    #     if i != ".DS_Store":
    #         shutil.rmtree(os.path.join(source2update,i))




    # for i in os.listdir("../srcTest"):
    #     if "DS_Store" not in i:
    #         for j in os.listdir(os.path.join("../srcTest", i)):
    #             if j.endswith(".designspace"):
    #                 if "-" in j:
    #                     clean = i + ".designspace"
    #                     old = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, j))
    #                     new = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, clean))
    #                     os.rename(old, new)
            # for j in os.listdir(os.path.join("../srcTest", i)):
            #     if j.endswith(".designspace"):
            #         if j.split(".")[0] != i:
            #             print(i, "\n",j.split(".")[0])
            #             old = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, j))
            #             new = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "src", i, i+".designspace"))
            #             os.rename(old, new)