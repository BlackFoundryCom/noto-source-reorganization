from fontTools import ttLib
from fontTools import mtiLib
from fontTools.feaLib import ast
from fontTools.misc import testTools
from fontTools import ufoLib
from Lib.findThings import getTxtFile, getFile, getFolder
from fontTools.otlLib import builder
from fontTools.ttLib.tables import otTables, otBase
from fontTools.designspaceLib import DesignSpaceDocument, SourceDescriptor
from defcon import Font
from ufo2ft import compileOTF, compileTTF
import os
import plistlib
# from defcon import Font

def readPlistFile(ufo, family):
    path, folder = getFile(".plist", "src", family)
    with open(path, "rb") as plist:
        pl = plistlib.load(plist)
        gxxxPath = (pl[ufo])
    gpostxt = folder + "/" +(gxxxPath['GPOS'])
    return gpostxt

def makeGTables(family, u):
    masters = []
    path, folder = getFile(".designspace", "src", family)
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    for s in designSpace.sources:
        masters.append(family + "-" + s.styleName.replace(" ", "") + ".ufo")
    # ufo = folder + "/" + masters[0]
    ufo = folder + "/" + u
    ufo = ufoLib.UFOReader(ufo)
    go = Font(folder + "/" + masters[0]).glyphOrder
    glyphSet = list(ufo.getGlyphSet().contents.keys())
    fileSub = getTxtFile(family, "GSUB")[0]
    fileDef = getTxtFile(family, "GDEF")[0]
    # since there is different GPOS table per weight,
    # the scripts reads the plist that provide the matching GPOS .txt file for each ufo
    filePos = [readPlistFile(u[:-4], family)]
    tables = [fileDef, fileSub, filePos]
    font = testTools.FakeFont(glyphSet)
    #to do : write the glyphOrder Table ?
    TABLES = list()
    for i in tables:
        print(i)
        mtiFile = open(i[0], 'rt', encoding="utf-8")
        tokenizer = mtiLib.Tokenizer(mtiFile)
        TABLES.append(mtiLib.parseTable(tokenizer, font))
    return TABLES


def ufoWithMTIfeatures2font(directory, *output):
    # TABLES = makeGTables(directory)
    path = getFolder(directory)
    ufolist = [x for x in os.listdir(path) if x[-3:] == "ufo"]
    print(ufolist)
    for u in ufolist:
        TABLES = makeGTables(directory, u)
        ufoSource = path + u
        destination = ""
        ufo = Font(ufoSource)
        folder = path + "fonts/"
        print(output)
        if "otf" in output:
            destination = folder + "OTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            otf = compileOTF(ufo, removeOverlaps=True)
            otf.save(destination + u[:-4] + ".otf")
            otf2 = ttLib.TTFont(destination + u[:-4] + ".otf")
            otf2['GDEF'] = TABLES[0]
            otf2['GSUB'] = TABLES[1]
            otf2['GPOS'] = TABLES[2]
            os.remove(destination + u[:-4] + ".otf")
            otf2.save(destination + u[:-4] + ".otf")
            print(destination + u[:-4] + ".otf")
            print("done")
        if "ttf" in output:
            destination = folder + "TTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            ttf = compileTTF(ufo, removeOverlaps=True)
            ttf.save(destination + u[:-4] + ".ttf")
            ttf2 = ttLib.TTFont(destination + u[:-4] + ".ttf")
            ttf2['GDEF'] = TABLES[0]
            ttf2['GSUB'] = TABLES[1]
            ttf2['GPOS'] = TABLES[2]
            os.remove(destination + u[:-4] + ".ttf")
            ttf2.save(destination + u[:-4] + ".ttf")
        ### WEB
        # if "woff2" in output:
        #     destination = folder + "WOFF2/"
        #     if not os.path.exists(destination):
        #         os.makedirs(destination)
        #     if "ttf" not in output:
        #         ttf = compileTTF(ufo, removeOverlaps=True)
        #         ttf['GDEF'] = TABLES[0]
        #         ttf['GSUB'] = TABLES[1]
        #         ttf['GPOS'] = TABLES[2]
        #     ttf.flavor = "woff2"
        #     ttf.save(destination + u[:-4] + ".woff2")
        # if "woff" in output:
        #     destination = folder + "WOFF/"
        #     if not os.path.exists(destination):
        #         os.makedirs(destination)
        #     if "ttf" not in output and "woff2" not in output:
        #         ttf = compileTTF(ufo, removeOverlaps=True)
        #     ttf.flavor = "woff"
        #     ttf.save(destination + u[:-4] + ".woff")


# ufoWithMTIfeatures2font("NotoMusic", "otf")
# readPlistFile("NotoMusic-Regular", "NotoMusic")