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
from ufo2ft import compileOTF
import os
# from ufo2ft import compileOTF
# from defcon import Font


def makeGTables(family):
    masters = []
    path, folder = getFile(".designspace", "src", family)
    designSpace = DesignSpaceDocument()
    designSpace.read(path)
    for s in designSpace.sources:
        masters.append(family + "-" + s.styleName.replace(" ", "") + ".ufo")
    ufo = folder + "/" +masters[0]
    ufo = ufoLib.UFOReader(ufo)
    go = Font(folder + "/" +masters[0]).glyphOrder
    print(go)
    glyphSet = list(ufo.getGlyphSet().contents.keys())
    fileSub = getTxtFile(family, "GSUB")[0]
    fileDef = getTxtFile(family, "GDEF")[0]
    filePos = getTxtFile(family, "GPOS")[0]
    tables = [fileDef, fileSub, filePos]
    font = testTools.FakeFont(glyphSet)
    #to do : write the glyphOrder Table ?
    TABLES = list()
    for i in tables:
        mtiFile = open(i[0], 'rt', encoding="utf-8")
        tokenizer = mtiLib.Tokenizer(mtiFile)
        TABLES.append(mtiLib.parseTable(tokenizer, font))
    return TABLES


def ufo2font(directory, ufolist, *output):
    TABLES = makeGTables(directory)
    path = getFolder(directory)
    for i in ufolist:
        ufoSource = path + i
        destination = ""
        ufo = Font(ufoSource)
        folder = path + "fonts/"
        print(output)
        if "otf" in output:
            destination = folder + "OTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            otf = compileOTF(ufo, removeOverlaps=True)
            otf.save(destination + i[:-4] + ".otf")
            otf2 = ttLib.TTFont(destination + i[:-4] + ".otf")
            otf2['GDEF'] = TABLES[0]
            otf2['GSUB'] = TABLES[1]
            otf2['GPOS'] = TABLES[2]
            os.remove(destination + i[:-4] + ".otf")
            otf2.save(destination + i[:-4] + ".otf")

ufo2font("NotoMusic", ["NotoMusic-Regular.ufo"], "otf")