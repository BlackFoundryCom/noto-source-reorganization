# import subprocess
import os
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
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler

"""
    TODO:
    — dl noto sources repo with submodule with Action?
    — Convert Glyphs sources into UFO + Designspace folders
    — Clean Designspace
    — Clean glyph order
    — rewrite kerning.plist and groups.plist
    — Check if ufo2ft needs to have "featureCompilerClass = MtiFeatureCompiler" in arg to generate features
        or if it detects the com.github.googlei18n.ufo2ft.mtiFeatures/*.mti data
"""


class sourcesBuilder():

    def __init__(self, fileName):
        self.notoSourcesPath = "../Google_Noto_src/src"
        self.fileName = fileName
        self.foldername = self.fileName.split(".")[0].replace("-MM", "")
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



class complexSourcesBuilder():

    def __init__(self, folderName):
        print("init")
        self.notoSourcesPath = "../Google_Noto_src/src/"
        self.folderName = folderName
        for i in os.listdir(os.path.join(self.notoSourcesPath, self.folderName)):
            if i.endswith(".glyphs"):
                print("1")
                typeface = sourcesBuilder(self.folderName+"/"+i)
                self.designSpacePath, self.ufos = typeface.convertion()

    @property
    def designSpaceDocument(self):
        designSpace = DesignSpaceDocument()
        designSpace.read(self.designSpacePath)
        return designSpace

    @property
    def masters(self):
        return self.designSpaceDocument.loadSourceFonts(defcon.Font)

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


class rebuiltKerning():

    def __init__(self, folder):
        self.folder = folder

    def load(self):
        for ufo in self.folder:
            if ufo.endswith(".ufo"):
                ft = defcon.Font(os.path.join(self.folder, ufo))
                feaCompiler = FeatureCompiler(ufo, outlines, featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter()])
                feaCompiler.compile()
                # NOW : read the feature file and write kerning.plist and group.plist



# def organizeSources():
#     notoSourcesDir = "../Google_Noto_src/src"
#     destination = "../src"
#     os.change(os.path.basename(self.notoSourcesDir))
#     subprocess.run(["git submodule add https://github.com/googlefonts/noto-source"], shell=True, check=True)


if __name__ == '__main__':
    NotoSources = "../Google_Noto_src/src"
    for i in os.listdir(NotoSources):
        if i.endswith(".glyphs"):
            print(i)
            # typeface = sourcesBuilder(i)
            # typeface.convertion()
        else:
            if os.path.isdir(os.path.join(NotoSources, i)):
                print(i, "is dir")
                typeface = complexSourcesBuilder(i)
                typeface.add_mti_features_to_ufos()