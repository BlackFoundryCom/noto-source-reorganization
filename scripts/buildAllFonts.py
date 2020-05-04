import sys
import os


from fontTools                  import (ufoLib, varLib, ttLib, mtiLib)
from fontTools.misc.plistlib    import load as readPlist
from fontTools.designspaceLib   import *
from defcon                     import Font
from ufo2ft                     import (compileOTF, compileTTF)
from ufo2ft.featureCompiler     import (FeatureCompiler, MtiFeatureCompiler)
from ufo2ft                     import compileInterpolatableTTFsFromDS
from ufo2ft.outlineCompiler     import OutlineOTFCompiler
from fontTools.designspaceLib   import DesignSpaceDocument
from ufo2ft.featureWriters      import (KernFeatureWriter,
                                        MarkFeatureWriter,
                                        loadFeatureWriters,
                                        ast)



class generate():

    def __init__(self, scriptsFolder):
        self.failing = list()
        self.MMfailing = list()
        self.scriptsFolder = scriptsFolder
        self.srcPath = os.path.join(self.scriptsFolder, os.pardir, "src")
        self.destination = os.path.join(
            self.scriptsFolder, os.pardir, "Fonts", "variable_ttf")
        self.sourcesFolders = [os.path.join(self.srcPath, i) for i in list(
            filter(lambda x: x!=(".DS_Store"), os.listdir(self.srcPath)))]
        self.staticPath = os.path.join(
            self.destination, os.pardir, "instances_ttf")
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)
        if not os.path.exists(self.staticPath):
            os.makedirs(self.staticPath)

    ############
    # PROPERTY #
    ############
    @property
    def checkIfMti(self):
        mti = []
        for i in os.listdir(self.familyPath):
            if i.endswith(".plist"):
                mti.append(i)
        return mti

    @property
    def designSpace(self):
        designspace = DesignSpaceDocument()
        designspace.read(self.designspace_path)
        return designspace

    @property
    def plistNumber(self):
        plistNumber = []
        for i in os.listdir(self.familyPath):
            if i.endswith(".plist"):
                plistNumber.append(i)
        return plistNumber

    @property
    def ufoList(self):
        ufoList_ = list()
        for element in os.listdir(self.familyPath):
            if element.endswith(".ufo"):
                ufoList_.append(element)
        return ufoList_

    @property
    def regularStylePath(self):
        if "Italic" not in os.path.basename(self.familyPath):
            basicStylePath_= os.path.join(self.familyPath, os.path.basename(
                                    self.familyPath).strip()+"-Regular.ufo")
            if not os.path.exists(basicStylePath_):
                basicStylePath_= os.path.join(self.familyPath, os.path.basename(
                                    self.familyPath).strip()+"-Light.ufo")
            if not os.path.exists(basicStylePath_):
                basicStylePath_= os.path.join(self.familyPath, os.path.basename(
                                    self.familyPath).strip()+"-Thin.ufo")
        else:
            basicStylePath_ = os.path.join(self.familyPath, os.basename(
                                        self.familyPath).strip()+"-Italic.ufo")
        print("    >>> " + self.n + "Variable has failed.\n        "\
              "        A static ttf version of the 'Regular' weight"\
              "\n        will be generated instead.")

        return basicStylePath_

    ######################
    # GENERATE FUNCTIONS #
    ######################
    def makeOneMaster(self, ufoSource):
        ufo = Font(ufoSource)
        ttf = compileTTF(ufo,
                         removeOverlaps=True,
                         useProductionNames = False,
                         featureWriters = [KernFeatureWriter(mode="append"),
                         MarkFeatureWriter])
        ttf.save(os.path.join(self.staticPath,
                        os.path.basename(ufoSource)[:-4] + ".ttf"))
        print("    " +os.path.basename(ufoSource)[:-4]+" has been generated.\n")

    def designSpace2Var(self):
        ds = self.designSpace
        family = os.path.basename(self.familyPath)
        print("\n>>> Load the {} designspace".format(family))
        print("    Load "+family+" files")
        ds.loadSourceFonts(Font)
        print("    Start to build Variable Tables")
        feature_Writers = [KernFeatureWriter(mode="append"), MarkFeatureWriter]
        font, _, _ = varLib.build(
                        compileInterpolatableTTFsFromDS(
                            ds,featureWriters = feature_Writers),optimize=False)
        font.save(os.path.join(self.destination, family + "-VF.ttf"))
        print("    " + family + " Variable Font generated\n")

    def makeAllversionsOfMtiVFonts(self):
        if len(self.plistNumber) > 1:
            vf = fontsWithMti(
                            self.familyPath,
                            self.destination,
                            UIVersionedFeatures=True,#help to discriminate
                            makeUIVersion=False)
            vf.load()
            vf.add_mti_features_to_master()
            vf.makeVarFont()
            vfUI = fontsWithMti(
                                self.familyPath,
                                self.destination,
                                UIVersionedFeatures=True,
                                makeUIVersion=True)
            vfUI.load()
            vfUI.add_ui_mti_features_to_master()
            vfUI.makeVarFont()
        elif len(self.plistNumber) == 1:
            vf = fontsWithMti(self.familyPath)
            vf.load()
            vf.add_mti_features_to_master()
            vf.makeVarFont()

    def makeAllVersionsOfMtiStaticFont(self):
        if len(self.plistNumber) > 1:
            sglMasterWthMti = fontsWithMti(
                                        self.familyPath,
                                        self.destination,
                                        UIVersionedFeatures=True,
                                        makeUIVersion=False)
            sglMasterWthMti.loadBasicStyle()
            sglMasterWthMti.add_mti_features_to_master()
            sglMasterWthMti.makeStaticFont()
            sglMstrWthMtiUI = fontsWithMti(
                                        self.familyPath,
                                        self.destination,
                                        UIVersionedFeatures=True,
                                        makeUIVersion=True)
            sglMstrWthMtiUI.loadBasicStyle()
            sglMstrWthMtiUI.add_ui_mti_features_to_master()
            sglMstrWthMtiUI.makeStaticFontUI()
        else:
            sglMasterWthMti = fontsWithMti(self.familyPath, self.destination)
            sglMasterWthMti.loadBasicStyle()
            sglMasterWthMti.add_mti_features_to_master()
            sglMasterWthMti.makeStaticFont()


    def make2VersionsForOneMasterWithMti(self):
        sglMasterWthMti = fontsWithMti(
                            self.familyPath,
                            self.destination,
                            UIVersionedFeatures=True,
                            makeUIVersion=False,
                            oneMaster=True)
        sglMasterWthMti.load()
        # sglMasterWthMti.add_mti_features_to_master()
        sglMasterWthMti.makeStaticFont()
        sglMstrWthMtiUI = fontsWithMti(
                            self.familyPath,
                            self.destination,
                            UIVersionedFeatures=True,
                            makeUIVersion=True,
                            oneMaster=True)
        sglMstrWthMtiUI.load()
        # sglMstrWthMtiUI.add_ui_mti_features_to_master()
        sglMstrWthMtiUI.makeStaticFontUI()

    def makeOneMasterFamilyWithMti(self):
        sglMasterWthMti = fontsWithMti(self.familyPath,
                                       self.destination,
                                       oneMaster=True)
        sglMasterWthMti.load()
        sglMasterWthMti.makeStaticFont()


    ####################################################################
    # INITIAL FUNCTION THAT FINDS IN WHICH CATEGORY THE FAMILY BELONGS #
    ####################################################################
    def multipleMastersVSsingleMaster(self):
        for self.familyPath in self.sourcesFolders:
            self.n = os.path.split(self.familyPath)[1].strip()
            self.designspace_path = os.path.join(
                                    self.familyPath, self.n + ".designspace")
            #####################################
            # CASE 1 => MULTIPLE MASTERS FAMILY #
            if len(self.ufoList) > 1:
                ########################################################
                # CASE 1.a => MULTIPLE MASTERS FAMILY WITH OT FEATURES #
                if len(self.checkIfMti) == 0:
                    try:
                        self.designSpace2Var()
                    except:
                        self.MMfailing.append(self.n)
                        try:
                            self.makeOneMaster(self.regularStylePath)
                        except:
                            self.failing.append(self.n)
                #########################################################
                # CASE 1.b => MULTIPLE MASTERS FAMILY WITH MTI FEATURES #
                else:
                    try:
                        self.makeAllversionsOfMtiVFonts()
                    except:
                        self.MMfailing.append(self.n)
                        try:
                            self.makeAllVersionsOfMtiStaticFont()
                        except:
                            self.failing.append(ufo)

            #############################
            # CASE 2 => ONLY ONE MASTER #
            else:
                print(">>> " + self.n + " family has only one master.\n"\
                      "    A static ttf will be generated instead.")
                ufo = self.ufoList[0]
                if len(self.checkIfMti) == 0:
                ################################################
                # CASE 2.a => ONLY ONE MASTER WITH OT FEATURES #
                    try:
                        self.makeOneMaster(os.path.join(self.familyPath, ufo))
                    except :
                        self.failing.append(ufo)
                #################################################
                # CASE 2.b => ONLY ONE MASTER WITH MTI FEATURES #
                else:
                    ###########################################################
                    # CASE 2.b.alpha => ONLY 1 MASTER WITH MTI AND UI VERSION #
                    if len(self.plistNumber) > 1:
                        try:
                            self.make2VersionsForOneMasterWithMti()
                        except:
                            self.failing.append(ufo)
                    ###########################################################
                    # CASE 2.b.beta => ONLY ONE MASTER WITH MTI AND 1 VERSION #
                    elif len(self.plistNumber) == 1:
                        try:
                            self.makeOneMasterFamilyWithMti()
                        except:
                            self.failing.append(ufo)

        if len(self.MMfailing) > 0:
            for i in self.MMfailing:
                if i not in self.failing:
                    print(i + " has not been generated as Variable")
                    print("but as fallback one static style has been built.")
                else:
                    print(i + " has not been generated.\n")

        if len(self.failing) > 0:
            for i in self.failing:
                print(i + " has not been generated.\n")


#############################################
# CLASS TO GENERATE FONTS WITH MTI FEATURES #
#############################################
class fontsWithMti():

    def __init__(self,
                 mtiFolderPath,
                 destination,
                 UIVersionedFeatures=False,
                 makeUIVersion=False,
                 oneMaster=False):
        self.mtiFolderPath = mtiFolderPath
        self.UIVersionedFeaturesExists = UIVersionedFeatures
        self.makeUIVersion = makeUIVersion
        self.destination = destination
        self.oneMaster = oneMaster


    ############
    # PROPERTY #
    ############

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


    ###############
    #  FUNCTIONS  #
    ###############

    def load(self):
        self.ufos = [os.path.join(self.mtiFolderPath, i) for i in os.listdir(
            self.mtiFolderPath) if i.endswith(".ufo")]
        if self.oneMaster is False:
            print(">>> Load {}.designspace".format(self.familyName))
        else:
            print("    Load {}.designspace".format(self.familyName))
        designSpacePath = os.path.join(self.mtiFolderPath, os.path.basename(
            self.mtiFolderPath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)

    @property
    def basicStylePath(self):
        if "Italic" not in os.path.basename(self.mtiFolderPath):
            basicStylePath_= os.path.join(self.mtiFolderPath, os.path.basename(
                                    self.mtiFolderPath).strip()+"-Regular.ufo")
            if not os.path.exists(basicStylePath_):
                basicStylePath_= os.path.join(self.mtiFolderPath, os.path.basename(
                                    self.mtiFolderPath).strip()+"-Light.ufo")
            if not os.path.exists(basicStylePath_):
                basicStylePath_= os.path.join(self.mtiFolderPath, os.path.basename(
                                    self.mtiFolderPath).strip()+"-Thin.ufo")
        else:
            basicStylePath_ = os.path.join(self.mtiFolderPath, os.basename(
                                        self.mtiFolderPath).strip()+"-Italic.ufo")
        print("    >>> " + os.path.basename(self.mtiFolderPath) + "Variable has failed."\
              "\n        A static ttf version of the 'Regular' weight"\
              "\n        will be generated instead.")

        return basicStylePath_

    def loadBasicStyle(self):
        self.ufos = []
        self.ufos.append(self.basicStylePath)
        print(">>> Load {} as Basic Style Path".format(
            os.path.basename(self.basicStylePath)))
        # print("Start working on", self.familyName)
        designSpacePath = os.path.join(self.mtiFolderPath, os.path.basename(
            self.mtiFolderPath)+".designspace")
        self.designSpaceDocument = DesignSpaceDocument()
        self.designSpaceDocument.read(designSpacePath)

    def makeStaticFont(self):
        ufoSource = self.add_mti_features_to_master()[0]
        staticTTF = compileTTF(ufoSource,
                         removeOverlaps=True,
                         useProductionNames = False,
                         featureCompilerClass = MtiFeatureCompiler,
                         featureWriters = None)
        staticTTF.save(os.path.join(self.staticPath,
                            os.path.basename(self.ufos[0])[:-4] + ".ttf"))
        print("    " + os.path.basename(self.ufos[0])[:-4] +" generated\n")

    def makeStaticFontUI(self):
        ufoSource = self.add_ui_mti_features_to_master()[0]
        self.staticTTF_UI = compileTTF(ufoSource,
                         removeOverlaps=True,
                         useProductionNames = False,
                         featureCompilerClass = MtiFeatureCompiler,
                         featureWriters = None)
        self.staticTTF_UI = self.renamer_(single=True)
        self.staticTTF_UI.save(os.path.join(self.staticPath,
                            os.path.basename(self.ufos[0])[:-4] + "-UI.ttf"))
        print("    " + os.path.basename(self.ufos[0])[:-4] +"-UI generated\n")

    def makeVarFont(self, mti = False):
        self.designSpaceDocument.loadSourceFonts(Font)
        print("\tStart to build Variable Tables")
        self.vfont, _, _ = varLib.build(compileInterpolatableTTFsFromDS(
                self.designSpaceDocument,
                featureCompilerClass = MtiFeatureCompiler,
                featureWriters = None
                ), optimize=False)
        if self.makeUIVersion is False:
            path = os.path.join(self.destination, self.familyName+"-VF.ttf")
            print(path)
            self.vfont.save(path)
            print("\t"+self.familyName+" Variable Font generated\n")
        else:
            path = os.path.join(self.destination, self.familyName+"UI-VF.ttf")
            vfontUI = self.renamer_()
            vfontUI.save(path)
            print("\t"+self.familyName+"UI Variable Font generated\n")

    def renamer_(self, single=False):
        if single is True:
            renamedFont = self.staticTTF_UI
        else:
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

    def add_mti_features_to_master(self):
        ufoWithMtiData = []
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
                ufoWithMtiData.append(master)
                # Don't save the ufo, to keep them clean from mti data
        print("    ufos updated with MTI data")
        return ufoWithMtiData

    def add_ui_mti_features_to_master(self):
        ufoWithMtiData = []
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
                ufoWithMtiData.append(master)
        print("    ufos updated with UI versioned MTI data")
        return ufoWithMtiData


def main():
    mif = generate(os.path.split(sys.argv[0])[0])
    mif.multipleMastersVSsingleMaster()


if __name__ == '__main__':
    sys.exit(main())