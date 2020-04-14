import os
import plistlib

from fontTools.misc             import testTools
from fontTools                  import ufoLib
from fontTools                  import varLib, ttLib, mtiLib
from fontTools.otlLib           import builder
from fontTools.ttLib.tables     import otTables, otBase
from fontTools.designspaceLib   import DesignSpaceDocument
from defcon                     import Font
from ufo2ft                     import compileOTF, compileTTF
from ufo2ft                     import compileInterpolatableTTFsFromDS
from fontTools.misc.plistlib    import load as readPlist
from ufo2ft.featureCompiler     import MtiFeatureCompiler
from ufo2ft.featureWriters      import (
                                        KernFeatureWriter,
                                        MarkFeatureWriter,
                                        loadFeatureWriters,
                                        ast,
                                        )


def ufoWithMTIfeatures2font(family, output):
    if len(output) == 0:
        output = "ttf"
    ft = fontsWithMti(family, output)
    ft.ufoWithMTIfeatures2fonts()


##########################################################
class fontsWithMti():

    def __init__(self,
                directory,
                output):
        self.mtiFolderPath = os.path.abspath(os.path.join("../src/", directory))
        self.directory = directory
        self.output = output

    def load(self):
        self.ufos = [os.path.join(self.mtiFolderPath, i) for i in os.listdir(
            self.mtiFolderPath) if i.endswith(".ufo")]
        print(">>> Load {}.designspace".format(self.familyName))
        designSpacePath = os.path.join(self.mtiFolderPath, os.path.basename(
            self.mtiFolderPath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)

    def makeStaticFont(self, ufoSource, otfFlavor = False):
        if otfFlavor is True:
            staticTTF = compileOTF(ufoSource,
                         removeOverlaps=True,
                         useProductionNames = False,
                         featureCompilerClass = MtiFeatureCompiler,
                         featureWriters = None)
        else:
            staticTTF = compileTTF(ufoSource,
                         removeOverlaps=True,
                         useProductionNames = False,
                         featureCompilerClass = MtiFeatureCompiler,
                         featureWriters = None)
        return staticTTF

    def makeStaticFontUI(self, ufoSource, otfFlavor = False):
        if otfFlavor is True:
            self.static_UI = compileOTF(ufoSource,
                     removeOverlaps=True,
                     useProductionNames = False,
                     featureCompilerClass = MtiFeatureCompiler,
                     featureWriters = None)
        else:
            self.static_UI = compileTTF(ufoSource,
                     removeOverlaps=True,
                     useProductionNames = False,
                     featureCompilerClass = MtiFeatureCompiler,
                     featureWriters = None)
        self.static_UI = self.renamer_(single=True)
        print("    " + os.path.basename(self.ufos[0])[:-4] +"-UI generated\n")
        return self.static_UI


    def renamer_(self):
        renamedFont = self.static_UI
        # if single is True:
        #     renamedFont = self.staticTTF_UI
        # else:
        #     renamedFont = self.vfont
        newName = self.familyName + " UI"
        # First : GET THE STYLE NAME EITHER IN namerecord *2*
        # IF the font is a RBIBI font
        # and in namerecord *17* in other cases
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            if namerecord.nameID == 2:
                WeightName = namerecord.string
            if namerecord.nameID == 5:
                version = namerecord.string
            if namerecord.nameID == 17:
                WeightName = namerecord.string
        #Then Change the name everywhere
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            # Create the naming of the font Family
            # (+ StyleName if the style is non RBIBI)
            if namerecord.nameID == 1:
                if WeightName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                    namerecord.string = newName
                else:
                    namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 3:
                unicID = namerecord.string.split(";")
                newUnicID = version + ";"+ unicID[1] +";"+ ''.join(
                    newName.split(' ')) +"-"+ ''.join(WeightName.split(' '))
                namerecord.string = newUnicID
            if namerecord.nameID == 4:
                namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 6:
                namerecord.string = ''.join(newName.split(
                    ' ')) + '-' + ''.join(WeightName.split(' '))
            if namerecord.nameID == 16:
                namerecord.string = newName

        return renamedFont

    @property
    def plistNumber(self):
        plistNumber = []
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist"):
                plistNumber.append(i)
        return plistNumber

    @property
    def mti_file(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist") and "UI" not in i:
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")

    @property
    def simple_mti_file(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist"):
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")

    @property
    def mti_file_for_UI_Version(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist") and "UI" in i:
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")

    @property
    def masters(self):
        return self.designSpaceDocument.loadSourceFonts(Font)

    @property
    def familyName(self):
        return self.mtiFolderPath.split("/")[-1]

    def add_mti_features_to_masters(self, UIVersionedFeaturesExists=False):
        ufosWithMtiData = []
        if UIVersionedFeaturesExists:
            mti_source = self.mti_file
        else:
            mti_source = self.simple_mti_file
        mti_paths = readPlist(mti_source)
        for master in self.masters:
            key = master.info.familyName.replace(
                " ", "")+"-"+master.info.styleName.replace(" ", "")
            for table, path in mti_paths[key].items():
                with open(os.path.join(self.mtiFolderPath, path), "rb") as mti_:
                    ufo_path = (
                        "com.github.googlei18n.ufo2ft.mtiFeatures/%s.mti"
                        % table.strip()
                    )
                    master.data[ufo_path] = mti_.read()
                # If we have MTI sources, any Adobe feature files derived from
                # the Glyphs file should be ignored. We clear it here because
                # it only contains junk information anyway.
                master.features.text = ""
                ufosWithMtiData.append(master)
                # Don't save the ufo, to keep them clean from mti data
        print("    ufos updated with MTI data")
        return ufosWithMtiData

    def add_ui_mti_features_to_masters(self):
        ufosWithMtiData = []
        mti_source = self.mti_file_for_UI_Version
        mti_paths = readPlist(mti_source)
        for master in self.masters:
            key = master.info.familyName.replace(
                " ", "")+"UI-"+master.info.styleName.replace(" ", "")
            for table, path in mti_paths[key].items():
                with open(os.path.join(self.mtiFolderPath, path), "rb") as mti_:
                    ufo_path = (
                        "com.github.googlei18n.ufo2ft.mtiFeatures/%s.mti"
                        % table.strip()
                    )
                    master.data[ufo_path] = mti_.read()
                # If we have MTI sources, any Adobe feature files derived from
                # the Glyphs file should be ignored. We clear it here because
                # it only contains junk information anyway.
                master.features.text = ""
                # Don't save the ufo, to keep them clean from mti data
                ufosWithMtiData.append(master)
        print("    ufos updated with UI versioned MTI data")
        return ufosWithMtiData

    def ufoWithMTIfeatures2fonts(self):
        self.load()
        if len(self.plistNumber) == 1:
            ufoWithMtiData = self.add_mti_features_to_masters()
            for u in ufoWithMtiData:
                destination = ""
                folder = os.path.join(self.mtiFolderPath, "fonts")
                if "otf" in self.output:
                    destination = os.path.join(folder, "OTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    otf = self.makeStaticFont(u, otfFlavor = True)
                    otf.save(os.path.join(destination, os.path.basename(u._path)[:-4] + ".otf"))
                if "ttf" in self.output:
                    destination = os.path.join(folder, "TTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    ttf = self.makeStaticFont(u)
                    ttf.save(os.path.join(destination, os.path.basename(u._path)[:-4] + ".ttf"))
        else:
            ufoWithMtiData = self.add_mti_features_to_masters(UIVersionedFeaturesExists=True)
            for u in ufoWithMtiData:
                destination = ""
                folder = os.path.join(self.mtiFolderPath, "fonts")
                if "ttf" in self.output:
                    destination = os.path.join(folder, "TTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    ttf = self.makeStaticFont(u)
                    ttf.save(os.path.join(destination, os.path.basename(u._path)[:-4] + ".ttf"))
                if "otf" in self.output:
                    destination = os.path.join(folder, "OTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    otf = self.makeStaticFont(u, otfFlavor = True)
                    otf.save(os.path.join(destination, os.path.basename(u._path)[:-4] + ".otf"))

            ufoWithMtiUIData = self.add_ui_mti_features_to_masters()
            for u in ufoWithMtiUIData:
                destination = ""
                folder = os.path.join(self.mtiFolderPath, self.familyName)
                if "ttf" in self.output:
                    destination = os.path.join(folder, "TTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    UIttf = self.makeUIVersion()
                    UIttf.save(os.path.join(destination, os.path.basename(u._path) + "UI.ttf"))
                if "otf" in self.output:
                    destination = os.path.join(folder, "OTF")
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    UIttf = self.makeUIVersion(otfFlavor = True)
                    UIttf.save(os.path.join(destination, os.path.basename(u._path) + "UI.otf"))


##########################################################
class variableFontsWithMti():

    def __init__(self, mtiFolderPath,
                 UIVersionedFeatures=False,
                 makeUIVersion=False):
        self.mtiFolderPath = mtiFolderPath
        self.UIVersionedFeaturesExists = UIVersionedFeatures
        self.makeUIVersion = makeUIVersion

    def load(self):
        self.ufos = [os.path.join(self.mtiFolderPath, i) for i in os.listdir(
            self.mtiFolderPath) if i.endswith(".ufo")]
        print(">>Load {}.designspace".format(self.familyName))
        # print("Start working on", self.familyName)
        designSpacePath = os.path.join(self.mtiFolderPath, os.path.basename(
            self.mtiFolderPath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)

    def makeVarFont(self, mti = False):
        # self.designSpaceDocument.loadSourceFonts(Font)
        print("\tStart to build Variable Tables")
        self.vfont, _, _ = varLib.build(compileInterpolatableTTFsFromDS(
                self.designSpaceDocument,
                featureCompilerClass = MtiFeatureCompiler,
                featureWriters = None
                ), optimize=False)
        if self.makeUIVersion is False:
            destination = os.path.join(self.mtiFolderPath, "fonts/VAR")
            if not os.path.exists(destination):
                os.makedirs(destination)
            path = os.path.join(destination, self.familyName+"-VF.ttf")
            self.vfont.save(path)
            print("\t"+self.familyName+" Variable Font generated\n")
        else:
            destination = os.path.join(
                self.mtiFolderPath, "fonts/"+self.familyName+"UI/VAR")
            if not os.path.exists(destination):
                os.makedirs(destination)
            path = os.path.join(destination, self.familyName+"UI-VF.ttf")
            vfontUI = self.renamer_()
            vfontUI.save(path)
            print("\t"+self.familyName+"UI Variable Font generated\n")

    def renamer_(self):
        renamedFont = self.vfont
        newName = self.familyName + " UI"
        # First : GET THE STYLE NAME EITHER IN namerecord *2*
        # IF the font is a RBIBI font
        # and in namerecord *17* in other cases
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            if namerecord.nameID == 2:
                WeightName = namerecord.string
            if namerecord.nameID == 5:
                version = namerecord.string
            if namerecord.nameID == 17:
                WeightName = namerecord.string
        #Then Change the name everywhere
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            # Create the naming of the font Family
            # (+ StyleName if the style is non RBIBI)
            if namerecord.nameID == 1:
                if WeightName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                    namerecord.string = newName
                else:
                    namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 3:
                unicID = namerecord.string.split(";")
                newUnicID = version + ";"+ unicID[1] +";"+ ''.join(
                    newName.split(' ')) +"-"+ ''.join(WeightName.split(' '))
                namerecord.string = newUnicID
            if namerecord.nameID == 4:
                namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 6:
                namerecord.string = ''.join(newName.split(
                    ' ')) + '-' + ''.join(WeightName.split(' '))
            if namerecord.nameID == 16:
                namerecord.string = newName

        return renamedFont

    @property
    def mti_file(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist") and "UI" not in i:
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")
        # return self.mti_source

    @property
    def simple_mti_file(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist"):
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")

    @property
    def mti_file_for_UI_Version(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".plist") and "UI" in i:
                path = os.path.join(self.mtiFolderPath, i)
                return open(path, "rb")

    @property
    def masters(self):
        return self.designSpaceDocument.loadSourceFonts(Font)

    @property
    def familyName(self):
        return self.mtiFolderPath.split("/")[-1]

    def add_mti_features_to_master_ufos(self):
        if self.UIVersionedFeaturesExists:
            mti_source = self.mti_file
        else:
            mti_source = self.simple_mti_file
        mti_paths = readPlist(mti_source)
        for master in self.masters:
            key = master.info.familyName.replace(
                " ", "")+"-"+master.info.styleName.replace(" ", "")
            for table, path in mti_paths[key].items():
                with open(os.path.join(self.mtiFolderPath, path), "rb") as mti_:
                    ufo_path = (
                        "com.github.googlei18n.ufo2ft.mtiFeatures/%s.mti"
                        % table.strip()
                    )
                    master.data[ufo_path] = mti_.read()
                # If we have MTI sources, any Adobe feature files derived from
                # the Glyphs file should be ignored. We clear it here because
                # it only contains junk information anyway.
                master.features.text = ""
                # Don't save the ufo, to keep them clean from mti data
        print("\tufos updated with MTI data")

    def add_ui_mti_features_to_master_ufos(self):
        mti_source = self.mti_file_for_UI_Version
        mti_paths = readPlist(mti_source)
        for master in self.masters:
            key = master.info.familyName.replace(
                " ", "")+"UI-"+master.info.styleName.replace(" ", "")
            for table, path in mti_paths[key].items():
                with open(os.path.join(self.mtiFolderPath, path), "rb") as mti_:
                    ufo_path = (
                        "com.github.googlei18n.ufo2ft.mtiFeatures/%s.mti"
                        % table.strip()
                    )
                    master.data[ufo_path] = mti_.read()
                # If we have MTI sources, any Adobe feature files derived from
                # the Glyphs file should be ignored. We clear it here because
                # it only contains junk information anyway.
                master.features.text = ""
                # Don't save the ufo, to keep them clean from mti data
        print("\tufos updated with UI versioned MTI data")

def makeVFWithMti(family):
    path = os.path.join("../src", family)
    vf = variableFontsWithMti(path)
    vf.load()
    vf.add_mti_features_to_master_ufos()
    vf.makeVarFont()

def makeAllVFversions(family):
    path = os.path.join("../src", family)
    plistNumber = []
    for i in os.listdir(path):
        if i.endswith(".plist"):
            plistNumber.append(i)
    if len(plistNumber) > 1:
        vf = variableFontsWithMti(
            path, UIVersionedFeatures=True, makeUIVersion=False)
        vf.load()
        vf.add_mti_features_to_master_ufos()
        vf.makeVarFont()
        vfUI = variableFontsWithMti(
            path, UIVersionedFeatures=True, makeUIVersion=True)
        vfUI.load()
        vfUI.add_ui_mti_features_to_master_ufos()
        vfUI.makeVarFont()
    elif len(plistNumber) == 1:
        makeVFWithMti(family)


# TEST
# ufoWithMTIfeatures2font("NotoSansOldHungarian", "otf")