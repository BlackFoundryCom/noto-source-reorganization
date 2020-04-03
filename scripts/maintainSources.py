import os
import shutil
import glyphsLib
import ufoLib2
import sys
from fontTools.designspaceLib   import DesignSpaceDocument

class sourcesBuilder():

    def __init__(self, fileName, hasMtiFiles = False):
        self.scriptsFolder = os.path.split(sys.argv[0])[0]
        self.notoSourcesPath = os.path.join(
            self.scriptsFolder, os.pardir, "sandbox")
        self.fileName = fileName
        self.foldername=self.fileName.split(".")[0].replace("MM","").strip("-")
        if hasMtiFiles:
            self.destination = os.path.join(
            self.scriptsFolder,os.pardir,"src",os.path.dirname(self.foldername))
        else:
            self.destination = os.path.join(
                self.scriptsFolder, os.pardir,"src", self.foldername)
        self.sourcePath = os.path.join(self.notoSourcesPath, self.fileName)
        ### delete previous folder
        if os.path.exists(self.destination):
            shutil.rmtree(self.destination)

    @property
    def notExportedGlyphs(self):
        notExportedGlyphsList = []
        GSft = glyphsLib.GSFont(self.sourcePath)
        for g in GSft.glyphs:
            if g.export is False:
                notExportedGlyphsList.append(g.name)
        return notExportedGlyphsList

    def convertion(self):
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)
        self.ufos, self.designspace_path = glyphsLib.build_masters(
                                            self.sourcePath, self.destination)
        self.cleanedUfos = self.cleanUfos()
        self.addSkipExport2designspace()

        for i in os.listdir(self.destination):
            if i.endswith(".designspace") and "-" in i:
                old = os.path.abspath(os.path.join(self.destination, i))
                new=os.path.abspath(os.path.join(self.destination, i.split(
                        ".")[0].replace("MM","").strip("-") + ".designspace"))
                if "Regular" in new:
                    new=new.replace("-Regular","")
                os.rename(old, new)

        return self.designspace_path, self.cleanUfos

    @property
    def designSpace(self):
        designspace = DesignSpaceDocument()
        designspace.read(self.designspace_path)
        return designspace

    def addSkipExport2designspace(self):
        ds = self.designSpace
        notExportedGlyphsList_ = self.notExportedGlyphs
        if len(notExportedGlyphsList_) != 0:
            ds.lib["public.skipExportGlyphs"]=notExportedGlyphsList_
        ds.write(self.designspace_path)

    def cleanUfos(self):
        glyphOrder = list()
        notExportedGlyphsList_ = self.notExportedGlyphs
        for ufoPath in self.ufos:
            ufo = ufoLib2.Font.open(os.path.join(self.destination, ufoPath))
            for g in ufo:
                # if g.name not in notExportedGlyphsList_:
                glyphOrder.append(g.name)
            ufo.glyphOrder = glyphOrder
            if len(notExportedGlyphsList_) != 0:
                ufo.lib["public.skipExportGlyphs"] = notExportedGlyphsList_
                ufo = self.cleanFeaFromSkippedGlyphs(ufo, notExportedGlyphsList_)
            ufo.save()

    def cleanFeaFromSkippedGlyphs(self, ufo, skippedGLyphs):
        cleanFea = ufo.features.text
        for gname in skippedGLyphs:
            cleanFea = cleanFea.replace(" "+gname+" ", " ")
            cleanFea = cleanFea.replace("["+gname+" ", "[ ")
            cleanFea = cleanFea.replace(" "+gname+"]", " ]")
        ufo.features.text = cleanFea

        return ufo


class complexSourcesBuilder():

    def __init__(self, folderName):
        self.scriptsFolder = os.path.split(sys.argv[0])[0]
        self.notoSourcesPath = os.path.join(
            self.scriptsFolder, os.pardir, "sandbox")
        self.folderName = folderName
        self.destination = os.path.join(
            self.scriptsFolder, os.pardir,"src", self.folderName)
        for i in os.listdir(os.path.join(self.notoSourcesPath,self.folderName)):
            if i.endswith(".glyphs"):
                typeface=sourcesBuilder(self.folderName+"/"+i, hasMtiFiles=True)
                self.designSpacePath, self.ufos = typeface.convertion()

    def copy_mti_files(self):
        familyFolder = os.path.join(self.notoSourcesPath, self.folderName)
        for i in os.listdir(familyFolder):
            if i.endswith(".txt") or i.endswith(".plist"):
                shutil.copyfile(os.path.join(familyFolder, i),
                                os.path.join(self.destination, i))
                if i.endswith(".plist") and "-" in i:
                    old=os.path.abspath(os.path.join(self.destination, i))
                    cleaned=i.split("-")[0] + ".plist"
                    new=os.path.abspath(os.path.join(self.destination, cleaned))
                    os.rename(old, new)

def copyContent(family, scriptsFolder):
    source2update=os.path.join(scriptsFolder, os.pardir, "sandbox")
    foldername = family
    print(">>> start to copy", family, "folder content in src folder")
    if "MM" in family:
        foldername = family.replace("MM", "").strip("-")
    destination = os.path.join(scriptsFolder, os.pardir, "src", foldername)
    familyFolder = os.path.join(source2update, family)
    src = os.path.abspath(familyFolder)
    dst = os.path.abspath(destination)
    if os.path.exists(destination):
        shutil.rmtree(destination)
    shutil.copytree(src, dst)
    print("    ", family.strip(), "folder content copied.\n")


def main():
    # translated = ["NotoMusic"]
    scriptsFolder = os.path.split(sys.argv[0])[0]
    # os.chdir(os.path.split(sys.argv[0])[0])
    source2update = os.path.join(scriptsFolder,"../sandbox")
    fail = []
    for i in os.listdir(source2update):
        glyphsFile = False
        # Case 1. parse glyphs files
        if i.startswith("Noto"):
            if i.endswith(".glyphs"):
                print(">>> start to convert", i)
                try:
                    typeface = sourcesBuilder(i)
                    typeface.convertion()
                    print("    ", i.strip(), "converted.\n")
                except:
                    fail.append(i)
                    print("    ", i.strip(), "NOT converted.\n")

        # Case 2. It's a folder. I can contains GLyphs file + mti files
        # or ufo + designspace + features files
            elif os.path.isdir(os.path.join(source2update, i)):
                # test if there is a .glyphs file in the folder
                for f in os.listdir(os.path.join(source2update, i)):
                    if f.endswith(".glyphs"):
                        glyphsFile = True

                # Case 2a. It's a folder with Glyphs file + mti features
                if glyphsFile is True:
                    print(">>> start to convert", i)
                    try:
                        typeface = complexSourcesBuilder(i)
                        typeface.copy_mti_files()
                        print("    ", i.strip(), "converted. MTI files copied.\n")
                    except:
                        fail.append(i)
                        print("    ", i.strip(), "NOT converted.\n")

                # Case 2b. No Glyphs file. We assume it containes ufos
                # and directly copy it the src folder
                else:
                    copyContent(i, scriptsFolder)
    for f in fail:
        print(f, "didn't work")

    # REMOVE GLYPHS AND UFO SOURCE FROM TEMP FOLDER
    for to_rm in os.listdir(source2update):
        if to_rm != ".DS_Store" and to_rm != "update.md":
            if os.path.isdir(os.path.join(source2update, to_rm)):
                shutil.rmtree(os.path.join(source2update, to_rm))
            else:
                os.remove(os.path.join(source2update, to_rm))

if __name__ == '__main__':
    import sys
    sys.exit(main())