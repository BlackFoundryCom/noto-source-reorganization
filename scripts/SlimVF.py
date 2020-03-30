import os
import defcon

from fontTools.designspaceLib   import *
from fontTools.ttLib            import TTFont
from fontTools                  import varLib
from fontTools.varLib           import instancer
from ufo2ft                     import compileInterpolatableTTFsFromDS
from fontTools.misc.plistlib    import load as readPlist
from ufo2ft.featureCompiler     import MtiFeatureCompiler
from ufo2ft.featureWriters      import (
                                        KernFeatureWriter,
                                        MarkFeatureWriter,
                                        loadFeatureWriters,
                                        ast,
                                        )


class slimVariableFonts():

    def __init__(self, mtiFolderPath):
        self.dirpath = dirpath

    @property
    def familyName(self):
        return defcon.Font(self.ufos[0]).info.familyName.replace(" ", "")

    def load(self):
        self.ufos = [os.path.join(self.dirpath, i) for i in os.listdir(
            self.dirpath) if i.endswith(".ufo")]
        print("Start working on", self.familyName)
        designSpacePath = os.path.join(self.dirpath, os.path.basename(
            self.dirpath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)

    def findRegularBoldDefaultLocation(self):
        mini, maxi = 0, 0
        tag2Name = {a.tag:a.name for a in self.designSpaceDocument.axes}

        for ins in self.designSpaceDocument.instances:
            if ins.styleName in ["Regular", "Italic"]:
                for dim in ins.location:
                    if dim == tag2Name["wght"]:
                        mini = ins.location[dim]

            if ins.styleName in ["Bold", "Bold Italic"]:
                for dim in ins.location:
                    if dim == tag2Name["wght"]:
                        maxi = ins.location[dim]
        return self._mapping(self.designSpaceDocument, mini, maxi), tag2Name

    def _mapping(self, ds, mini, maxi):
        for a in ds.axes:
            if a.tag == "wght":
                default = a.default
                if a.map:
                    mapDico = {round(m[1]):round(m[0]) for m in a.map}
                    mini = mapDico[int(mini)]
                    maxi = mapDico[int(maxi)]
                    # default = mapDico[int(default)] ?
        return mini, maxi#, default

    def makeVarFont(self):
        (minimum, maximum), tag2name = self.findRegularBoldDefaultLocation()
        # check if defautl exist
        otherTags = [a.tag for a in self.designSpaceDocument.axes if a.tag != "wght"]
        print("\tLoad {}.designspace".format(self.familyName))
        self.designSpaceDocument.loadSourceFonts(defcon.Font)
        vfont, _, _ = varLib.build(compileInterpolatableTTFsFromDS(
            self.designSpaceDocument,
            featureWriters = [KernFeatureWriter(mode="append"),
            MarkFeatureWriter()]
            ), optimize=False)

        fullfontsFolder = os.path.join(self.dirpath, "fonts/VAR")
        if not os.path.exists(fullfontsFolder):
            os.makedirs(fullfontsFolder)
        path = os.path.join(fullfontsFolder, self.familyName+"-VF.ttf")
        vfont.save(path)
        vfont = TTFont(path)

        tags =  {"wght":(minimum, maximum)}
        if len(otherTags) == 0:
            slimft = instancer.instantiateVariableFont(vfont, tags)
        else:
            for t in otherTags:
                tags[t] = None
            slimft = instancer.instantiateVariableFont(vfont, tags)

        for namerecord in slimft['name'].names:
            namerecord.string = namerecord.toUnicode()
            if namerecord.nameID == 3:
                unicID = namerecord.string.split(";")
                newID = "4.444"+ ";" + unicID[1] + ";" + unicID[2]
                print("\tTagging the font as a 'slim' one:", newID)
                namerecord.string = newID
            if namerecord.nameID == 5:
                namerecord.string = "Version 4.444"
        print("\tSaving " + self.familyName + "Slim-VF.ttf\n")
        slimFontFolder = os.path.join(fullfontsFolder + "/SlimVF")
        if not os.path.exists(slimFontFolder):
            os.makedirs(slimFontFolder)
        slimft.save(os.path.join(slimFontFolder, "%sSlim-VF.ttf"%self.familyName))

class SlimVariableFontsWithMti():
    """docstring for ClassName"""
    def __init__(self, mtiFolderPath, UIVersionedFeatures=False, makeUIVersion=False):
        self.mtiFolderPath = mtiFolderPath
        self.UIVersionedFeaturesExists = UIVersionedFeatures
        self.makeUIVersion = makeUIVersion

    def renamer(self):
        renamedFont = self.slimft
        newName = self.familyName + " UI"
        #First : GET THE STYLE NAME EITHER IN namerecord2 if the font is a RBIBI font or in namerecord 17 in other cases
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            if namerecord.nameID == 2:
                WeightName = namerecord.string
            if namerecord.nameID == 17:
                WeightName = namerecord.string
        #Then Change the name everywhere
        for namerecord in renamedFont['name'].names:
            namerecord.string = namerecord.toUnicode()
            # Create the naming of the font Family + style if the style is non RBIBI
            if namerecord.nameID == 1:
                if WeightName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                    namerecord.string = newName
                else:
                    namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 3:
                unicID = namerecord.string.split(";")
                newUnicID = "4.444"+ ";"+ unicID[1] +";"+ ''.join(
                    newName.split(' ')) +"-"+ ''.join(WeightName.split(' '))
                namerecord.string = newUnicID
            if namerecord.nameID == 4:
                namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 5:
                namerecord.string = "Version 4.444"
            if namerecord.nameID == 6:
                namerecord.string = ''.join(newName.split(
                    ' ')) + '-' + ''.join(WeightName.split(' '))
            if namerecord.nameID == 7:
                namerecord.string = "Noto (from which this font is a modification) is a trademark of Google Inc."
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
        return self.designSpaceDocument.loadSourceFonts(defcon.Font)

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
                # master.save()
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
                # master.save()
        print("\tufos updated with UI versioned MTI data")

    def load(self):
        self.ufos = [os.path.join(self.mtiFolderPath, i) for i in os.listdir(
            self.mtiFolderPath) if i.endswith(".ufo")]
        print("Start working on", self.familyName)
        designSpacePath = os.path.join(self.mtiFolderPath, os.path.basename(
            self.mtiFolderPath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)


    def findRegularBoldDefaultLocation(self):
        mini, maxi = 0, 0
        tag2Name = {a.tag:a.name for a in self.designSpaceDocument.axes}

        for ins in self.designSpaceDocument.instances:
            if ins.styleName in ["Regular", "Italic"]:
                for dim in ins.location:
                    if dim == tag2Name["wght"]:
                        mini = ins.location[dim]

            if ins.styleName in ["Bold", "Bold Italic"]:
                for dim in ins.location:
                    if dim == tag2Name["wght"]:
                        maxi = ins.location[dim]
        return self._mapping(self.designSpaceDocument, mini, maxi), tag2Name

    def _mapping(self, ds, mini, maxi):
        for a in ds.axes:
            if a.tag == "wght":
                default = a.default
                if a.map:
                    mapDico = {round(m[1]):round(m[0]) for m in a.map}
                    mini = mapDico[int(mini)]
                    maxi = mapDico[int(maxi)]
                    # default = mapDico[int(default)]
        return mini, maxi#, default

    def makeVarFont(self, mti = False):
        (minimum, maximum), tag2name = self.findRegularBoldDefaultLocation()
        # check if defautl exist
        otherTags = [a.tag for a in self.designSpaceDocument.axes if a.tag != "wght"]
        print("\tLoad {}.designspace".format(self.familyName))
        # self.designSpaceDocument.loadSourceFonts(defcon.Font)

        vfont, _, _ = varLib.build(compileInterpolatableTTFsFromDS(
                self.designSpaceDocument,
                featureCompilerClass = MtiFeatureCompiler,
                featureWriters = None
                ), optimize=False)

        fullfontsFolder = os.path.join(self.mtiFolderPath, "fonts/VAR")
        if not os.path.exists(fullfontsFolder):
            os.makedirs(fullfontsFolder)
        if self.makeUIVersion is False:
            path = os.path.join(fullfontsFolder, self.familyName+"-VF.ttf")
            vfont.save(path)
        else:
            path = os.path.join(fullfontsFolder, self.familyName+"-UI-VF.ttf")
            vfont.save(path)

        vfont = TTFont(path)

        tags =  {"wght":(minimum, maximum)}
        # print(vfont)
        if len(otherTags) == 0:
            self.slimft = instancer.instantiateVariableFont(vfont, tags)
        else:
            for t in otherTags:
                tags[t] = None
            self.slimft = instancer.instantiateVariableFont(vfont, tags)
        if self.makeUIVersion is False:
            for namerecord in self.slimft['name'].names:
                namerecord.string = namerecord.toUnicode()
                if namerecord.nameID == 3:
                    unicID = namerecord.string.split(";")
                    newID = "4.444"+ ";" + unicID[1] + ";" + unicID[2]
                    print("\tnew unic ID:", newID)
                    namerecord.string = newID
                if namerecord.nameID == 5:
                    namerecord.string = "Version 4.444"
            print("\tSaving " + self.familyName + "-Slim-VF.ttf\n")
            slimFontFolder = os.path.join(fullfontsFolder + "/SlimVF")
            if not os.path.exists(slimFontFolder):
                os.makedirs(slimFontFolder)
            self.slimft.save(os.path.join(
                slimFontFolder, "%s-Slim-VF.ttf"%self.familyName))
        else:
            slimUIFont = self.renamer()
            print("\tSaving " + self.familyName + "-Slim-UI-VF.ttf\n")
            slimFontFolder = os.path.join(fullfontsFolder + "/SlimVF")
            if not os.path.exists(slimFontFolder):
                os.makedirs(slimFontFolder)
            slimUIFont.save(os.path.join(
                slimFontFolder, "%s-Slim-UI-VF.ttf"%self.familyName))

def getFolder(directory):
    rdir = os.path.abspath(os.path.join("../src/", directory))
    return rdir

def makeSlimVF(family):
    pathFolder = getFolder(family)
    ft = slimVariableFonts(dir_)
    ft.load()
    ft.makeVarFont()

def makeNormalAndUIVersions(family):
    pathFolder = getFolder(family)
    plistNumber = []
    for i in os.listdir(pathFolder):
        if i.endswith(".plist"):
            plistNumber.append(i)
    if len(plistNumber) > 1:
        vf = SlimVariableFontsWithMti(
            pathFolder, UIVersionedFeatures=True, makeUIVersion=False)
        vf.load()
        vf.add_mti_features_to_master_ufos()
        vf.makeVarFont()
        vfUI = SlimVariableFontsWithMti(
            pathFolder, UIVersionedFeatures=True, makeUIVersion=True)
        vfUI.load()
        vfUI.add_ui_mti_features_to_master_ufos()
        vfUI.makeVarFont()
    elif len(plistNumber) == 1:
        makeVFWithMti(family)