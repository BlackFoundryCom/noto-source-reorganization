#!/usr/bin/env python3
import os
import subprocess
import argparse
import swaper
from Ufo2fontsFromdesignSpace import *
from instancesMatcher import mergeFonts

def getFolder(directory):
    repo = "src/" + directory + "/"
    cwd = os.getcwd()
    # rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo)) + "/"
    rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo)) + "/"
    return rdir

def prettyLog(msg):
    diese = "".join(["-" for i in range(len(msg))])
    print(diese + "\n" + msg + "\n" + diese)

def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-sub", help = "input the folder path of the family \
                you want to subset, \n if you don't use the --script arg  \
                it will display the available subsets for this family, if any.")
    parser.add_argument("--script", nargs = '*', help =
                "Give the list of the writing scripts you want to subset")
    parser.add_argument("-gen", help =
                "Input the folder path of the family you want to generate")
    parser.add_argument("--fastgen", help =
                "create the whole family fonts from the variable font. \
                This option is faster than interpolate UFO, \
                but the contours are not merged. \
                This may cause issue with old app. \
                Input the folder path of the family you want to generate")
    parser.add_argument("-f", nargs = '*', help =
                "Input the list of the formats you want separated with comma. \
                If you don't specify formats, ttf will be choosen by default")
    parser.add_argument("-var", help =
                "Input the path folder of the family")
    parser.add_argument("-name", help=
                "Give a new name to the family")
    parser.add_argument("--static", help=
                "Extract one static instances from a variable font. \
                Give the path of the folder family")
    parser.add_argument("-r", nargs = "*", help=
                "Give a new name to the family. \
                In put the new name then the folder path\
                If no format is given, the script rename every \
                fonts folder it will find in /fonts")
    parser.add_argument("--allVF", nargs = '?', help=
                "Generate all typefaces as Variable fonts, when possible")
    parser.add_argument("--allOTF", nargs = '?', help=
                "Generate all typefaces as otf flavored fonts, when possible")
    parser.add_argument("--allTTF", nargs = '?', help=
                "Generate all typefaces as otf flavored fonts, when possible")
    parser.add_argument("--salt", help=
                "Set I.alt and J.alt stylistic alternate shapes as default")
    parser.add_argument("--merge", nargs = "*", help=
                "Merge the matching styles of 2 families. \
                Please give the folder path of each family.")
    args = parser.parse_args()
    return args

def main():
    """ A way to use Ufo2fontsFromdesignSpace in terminal
    """
    args = create_arg_parser()
    #SUBSETABLE FAMILIES (Pan-European and Arabic writing systems)
    pan_european_fonts =    ["NotoSans",
                            "NotoSans-Italic",
                            "NotoSerif", "NotoSerif-Italic",
                            "NotoSansDisplay",
                            "NotoSansDisplay-Italic",
                            "NotoSerifDisplay",
                            "NotoSerifDisplay-Italic",
                            "NotoSansMono"]
    arabic_fonts =          ["NotoKufiArabic",
                             "NotoNaskhArabic",
                             "NotoNaskhArabicUI",
                             "NotoNastaliqUrdu",
                             "NotoSansArabic",
                             "NotoSansArabicUI"]

    # IF A FOLDER PATH IS GIVEN, CHECK IF IT'S A VALID ONE
    # if len(sys.argv) > 1:
    #     path = os.path.abspath(os.path.join(os.path.dirname(sys.argv[len(sys.argv) - 1]), os.pardir, 'scripts'))
    #     if not os.path.exists(sys.argv[len(sys.argv) - 1]):
    #         prettyLog("You must enter a valid folder path")
    # else:
    #     prettyLog("Usage : script path [--option] list of options [--command] family folder path")


    ##############
    # SUBSETTING #
    ##############
    jsonpath = ""
    writingSys = []
    newName = " "
    if "-sub" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.sub), os.pardir, 'scripts'))
        familyPath = args.sub
        family = os.path.split(familyPath)[1]
        if "-name" in sys.argv:
            newName = str(args.name)
            print("The {} family will be renamed {}".format(family, newName))
        if family in pan_european_fonts + arabic_fonts:
            if args.script is None:
                if family in pan_european_fonts:
                    jsonpath = os.path.join(path, "subsets", "lgc_glyphset.json")
                else:
                    jsonpath = os.path.join(path, "subsets", "arabic_glyphset.json")
                prettyLog(
                    "You have not give a subset. List of available subsets:")
                with open(jsonpath, 'r') as subsetDict:
                    subsets = json.load(subsetDict)
                    for i in subsets:
                        print("— "+i)
                request = input("Give at least one subset: ").split(",")
                for sub in request:
                    sub = sub.strip(" ")
                    writingSys.append(sub)
                if "-f" in sys.argv:
                    formats = args.f
                    for phormat in formats:
                        os.chdir(path)
                        subsetFonts(family, writingSys,
                                    flavor=[str(phormat)],familyNewName=newName)
                else:
                    os.chdir(path)
                    subsetFonts(family, writingSys,
                                flavor=["ttf"], familyNewName=newName,)
            else:
                os.chdir(path)
                for sub in args.script:
                    sub = sub.replace(",","")
                    writingSys.append(sub)
                subsetFonts(family, writingSys,
                            flavor=["ttf"], familyNewName=newName,)
    ########################
    # GENERATING VARIABLES #
    ########################
    elif "-var" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.var), os.pardir, 'scripts'))
        familyPath = args.var
        failing = []
        if os.path.exists(familyPath):
            os.chdir(path)
            ufoList = list()
            for element in os.listdir(familyPath):
                if element.endswith(".ufo"):
                    ufoList.append(element)
            if len(ufoList) > 1:
                try:
                    makeVariableFonts(os.path.split(familyPath)[1])
                except:
                    failing.append(os.path.split(familyPath)[1])
            else:
                print("\n>>> " + os.path.split(familyPath)[1] + \
                    "family has only one master.\n"\
                    "A static ttf will be generated instead.")
                makeVanillaFamily(os.path.split(familyPath)[1], 'ttf')
        if len(failing) > 0:
            for i in failing:
                print("Warning: " + i + " has not been generated.")

    ############################################
    # FAST GENERATING INSTANCES FROM VARIABLES #
    ############################################
    elif "--fastgen" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.fastgen), os.pardir, 'scripts'))
        familyPath = args.fastgen
        family = os.path.split(familyPath)[1]
        if os.path.exists(familyPath):
            os.chdir(path)
            makeTTFInstancesFromVF(family)
        if family not in pan_european_fonts:
            addSecureSet(family, ["ttf"])
    ##############################
    # GENERATING THE FULL FAMILY #
    ##############################
    elif "-gen" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.gen), os.pardir, 'scripts'))
        familyPath = args.gen
        family = os.path.split(familyPath)[1]
        if os.path.exists(familyPath):
            os.chdir(path)
            if "-f" in sys.argv:
                output = []
                for f in args.f:
                    output.append(f.strip(','))
                if family in pan_european_fonts:
                    formats = args.f
                    for phormat in formats:
                        print("start")
                        designSpace2Instances(
                            os.path.split(familyPath)[1], str(phormat))
                else:
                    # prettyLog("A securet set of basic latin glyphs will be merged into {fam}.\
                    #     \nAnd since fontTools can only merge ttf fonts, {fam} will be outputed as such".format(fam = family))
                    if "otf" in output:
                        designSpace2Instances(
                            os.path.split(familyPath)[1], "otf")
                        output.remove("otf")
                        print(output)
                        if len(output) == 0:
                            return
                    # print(output)
                    if "woff" in output or "woff2" in output:
                        if "woff2" not in output:
                            designSpace2Instances(
                            os.path.split(familyPath)[1], "ttf", "woff")
                        else:
                            designSpace2Instances(
                            os.path.split(familyPath)[1], "ttf","woff2","woff")
                    else:
                        designSpace2Instances(
                            os.path.split(familyPath)[1], "ttf")
            else:
                prettyLog("The family will be generated as ttf."\
                          " If non-latin, a 'securet set'"\
                          " of basic latin glyphs will be added.")
                designSpace2Instances(os.path.split(familyPath)[1])
    #####################
    # RENAME THE FAMILY #
    #####################
    elif "-r" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.r[-1]), os.pardir, 'scripts'))
        newName = " ".join(args.r[:-1])
        familyPath = args.r[-1]
        family = os.path.split(familyPath)[1]
        if "-f" in sys.argv:
            formats = args.f
            for phormat in formats:
                os.chdir(path)
                prettyLog("The family will be generatedi as {}".format(phormat))
                renameFonts(family, str(newName), phormat)
        else:
            os.chdir(path)
            renameFonts(family, str(newName))
    ##########################################
    # Extract ONE OR SEVERAL STATIC INSTANCE #
    ##########################################
    elif "--static" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.static), os.pardir, 'scripts'))
        locationList = list()
        styles = list()
        os.chdir(path)
        axesName = dict()
        familPath = args.static
        familyName = os.path.split(familPath)[1]
        dsPath = os.path.join(familPath, familyName + ".designspace")
        ds = openDesignSpace(dsPath)
        ###
        ufoList = list()
        for element in os.listdir(familPath):
            if element.endswith(".ufo"):
                ufoList.append(element)
        if len(ufoList) > 1:
        ###
            for a in ds.axes:
                axesName[a.name] = a.tag
            for i in ds.instances:
                loca = dict()
                for loc in i.location:
                    loca[axesName[loc]] = i.location[loc]
                locationList.append(loca)
                print(familyName, i.styleName, "--> [" +\
                      str(locationList.index(loca)) +"]")
                styles.append(i.styleName)
            prettyLog("Which static instance(s) do you want?"\
                      "input the corresponding number(s):")
            static = input(":")
            if "-" in static:
                scale = static.split("-")
                for s in range(int(scale[0]), int(scale[1])):
                    makeOneInstanceFromVF(familyName, locationList[int(s)])
            elif "," in static:
                instancesList = static.split(", ")
                for il in instancesList:
                    makeOneInstanceFromVF(familyName, locationList[int(il)])
            else:
                makeOneInstanceFromVF(familyName, locationList[int(static)])
                print(familyName, styles[int(static)], "extracted")
        else:
            print("\n>>> " + familyName + " family has only one master.\n"\
                  "        A static ttf can be generated instead.")
            prettyLog("Do you want the static ttf to be generated? : y/n")
            static = input(">>> ")
            if "y" in static:
                makeVanillaFamily(familyName, 'ttf')
    #######################################################
    # 3 commands to generate all families in VF, TTF, OTF #
    #######################################################
    elif "--allVF" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(sys.argv[0]), os.pardir, 'scripts'))
        os.chdir(path)
        failing = []
        folders = [os.path.join("../src/", i) for i in list(
            filter(lambda x: x!=(".DS_Store"), os.listdir("../src")))]
        for familyPath in folders:
            n = os.path.split(familyPath)[1].strip()
            ufoList = list()
            for element in os.listdir(familyPath):
                if element.endswith(".ufo"):
                    ufoList.append(element)
            if len(ufoList) > 1:
                try:
                    makeVariableFonts(os.path.split(familyPath)[1])
                except:
                    print("    >>> " + n + "Variable has failed.\n"\
                          "        A static ttf version of the family"\
                          "will be generated.")
                    makeVanillaFamily(os.path.split(familyPath)[1], 'ttf')
                    failing.append(familyPath.split("/")[-1])
            else:
                print("    >>> " + n + "family has only one master.\n"\
                      "        A static ttf will be generated instead.")
                makeVanillaFamily(os.path.split(familyPath)[1], 'ttf')
        if len(failing) > 0:
            for i in failing:
                print(i + " has not been generated as a Variable.")
    elif "--allOTF" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(sys.argv[0]), os.pardir, 'scripts'))
        os.chdir(path)
        failing = []
        folders = [os.path.join("../src/", i) for i in list(
            filter(lambda x: x!=(".DS_Store"), os.listdir("../src")))]
        for familyPath in folders:
            try:
                makeOtfFamily(os.path.split(familyPath)[1],
                                newName=" ", onlyOtf=True)
            except:
                failing.append(familyPath.split("/")[-1])
        if len(failing) > 0:
            for i in failing:
                print(i + " has not been generated.")
    elif "--allTTF" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(sys.argv[0]), os.pardir, 'scripts'))
        os.chdir(path)
        failing = []
        folders = [os.path.join("../src/", i) for i in list(
            filter(lambda x: x!=(".DS_Store"), os.listdir("../src")))]
        for familyPath in folders:
            try:
                makeVanillaFamily(os.path.split(familyPath)[1], 'ttf')
            except:
                failing.append(familyPath.split("/")[-1])
        if len(failing) > 0:
            for i in failing:
                print(i + " has not been generated.")
    ############################
    # SWAP I/I.alt and J/J.alt #
    ############################
    elif "--salt" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.salt), os.pardir, 'scripts'))
        familyPath = args.salt
        family = os.path.split(familyPath)[1]
        if os.path.exists(familyPath):
            os.chdir(path)
        swaper.swaper(os.path.split(familyPath)[1])
    ###############
    # MERGE FONTS #
    ###############
    elif "--merge" in sys.argv:
        path = os.path.abspath(
            os.path.join(os.path.dirname(args.merge[0]), os.pardir, 'scripts'))
        os.chdir(path)
        master = os.path.basename(args.merge[0])
        slave = os.path.basename(args.merge[1])
        mergeFonts(master, slave)


if __name__ == '__main__':
    import sys
    sys.exit(main())