from Ufo2fontsFromdesignSpace import *
from makeFontsWithTablesFromMtiFiles import *

# *************************
# GENARATE VARIABLE FONT **
#**************************
#POSSIBLE FUNCTIONS :
# renameFonts("NotoSerif", "Tomate")
# designSpace2Var(familyName)
# subsetFonts(familyName, [subset], flavor = [formats])
# mergeFonts()
# makeTTFInstancesFromVF("NotoSerif")
# makeOneInstanceFromVF(familyName, locationDict)
# instances(familyName, formats, newName = "newName")
# mastersUfos2fonts(familyName, formats)

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
                newUnicID = "4.444"+ ";"+ unicID[1] +";"+ ''.join(newName.split(' ')) +"-"+ ''.join(WeightName.split(' '))
                namerecord.string = newUnicID
            if namerecord.nameID == 4:
                namerecord.string = newName + " " + WeightName
            if namerecord.nameID == 5:
                namerecord.string = "Version 4.444"
            if namerecord.nameID == 6:
                namerecord.string = ''.join(newName.split(' ')) + '-' + ''.join(WeightName.split(' '))
            if namerecord.nameID == 7:
                namerecord.string = "Noto (from which this font is a modification) is a trademark of Google Inc."
            if namerecord.nameID == 16:
                namerecord.string = newName

        return renamedFont

    @property
    def glyphFiles(self):
        for i in os.listdir(self.mtiFolderPath):
            if i.endswith(".glyphs"):
                # gl = open(i)
                gl = open(os.path.join(self.mtiFolderPath, i))
        return gl

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
        return self.masters[0].info.familyName.replace(" ", "")

    def add_mti_features_to_master_ufos(self):
        if self.UIVersionedFeaturesExists:
            mti_source = self.mti_file
        else:
            mti_source = self.simple_mti_file
        mti_paths = readPlist(mti_source)
        for master in self.masters:
            key = master.info.familyName.replace(" ", "")+"-"+master.info.styleName.replace(" ", "")
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
            key = master.info.familyName.replace(" ", "")+"UI-"+master.info.styleName.replace(" ", "")
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
        font = glyphsLib.parser.load(self.glyphFiles)
        self.designSpaceDocument = glyphsLib.builder.to_designspace(font)


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
                featureWriters = [KernFeatureWriter(mode="append"),
                MarkFeatureWriter()]
                ), optimize=False)

        fullfontsFolder = "../fullfonts"
        if not os.path.exists(fullfontsFolder):
            os.makedirs(fullfontsFolder)
        path = os.path.join(fullfontsFolder, self.familyName+"-VF.ttf")
        vfont.save(path)


if __name__ == '__main__':
    l = []
    for i in os.listdir("../src"):
        uiVersion = []
        if "DS_Store" not in i:
            for j in os.listdir(os.path.join("../src", i)):
                if j.endswith(".plist"):
                    uiVersion.append(j)
            if len(uiVersion) == 0:
                try:
                    print(i)
                    designSpace2Var(i)
                except:
                    print("fail to generate", i)
                    l.append(i)
print("failed VF: ", l)