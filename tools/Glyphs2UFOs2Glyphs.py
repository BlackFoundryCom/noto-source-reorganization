#!/usr/bin/env python3
import os
from glyphsLib import (build_masters,
    to_glyphs,
    )
from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
    )
from defcon import Font
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler
from fontTools.designspaceLib import DesignSpaceDocument

def main():
    """ Use (in console) : python3 <Glyphs2UFOs2Glyphs.py script path> [option] <input Glyphs file>

    Option:
    -k : output features with GPOS rules added in a separate features.fea file
                         use the 'include(<features file path>);'' syntax in ufo.features.text
                         instead of previous features rules parsed by glyphsLib
    """
    if sys.argv[-1][-7:] == ".glyphs":
        glyphs2ufos(sys.argv[-1])
    elif sys.argv[-1][-12:] == ".designspace":
        ufosToGlyphsFromDS(sys.argv[-1])
    else:
        print("Please provide either a Glyphs of a designspace file")

def ufosToGlyphsFromDS(path):
    ds = DesignSpaceDocument()
    ds.read(path)
    font = to_glyphs(ds)
    folderpath, file = os.path.split(path)
    destination = folderpath + "/Glyphs/"
    if not os.path.exists(destination):
        os.makedirs(destination)
    family = file[:-12]
    font.save(destination + family + ".glyphs")

def glyphs2ufos(path):
    folderpath, file = os.path.split(path)
    if "fixed_" in file:
        foldername = file[6:-7]
    else:
        foldername = file[:-7]
    destination = os.path.join(folderpath, foldername + "_UFOs")
    if not os.path.exists(destination):
        os.makedirs(destination)
    try:
        ufos, designspace_path = build_masters(path, destination)
    except:
        rewriteGlyphsFile(folderpath, path, file)
    if "-k" in sys.argv:
        insertGPOSinFEA(destination)

def insertGPOSinFEA(ufosFolder):
    #TODO : keep the GDEF table that Glyphs generate automatically
    ufolist = list()
    for file in os.listdir(ufosFolder):
        if file[-4:] == ".ufo":
            print(file)
            ufolist.append(os.path.join(ufosFolder, file))
    for ufosource in ufolist:
        ufo = Font(ufosource)
        print(ufo)
        outlines = OutlineOTFCompiler(ufo).compile()
        feaCompiler = FeatureCompiler(ufo, outlines, featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter])
        feaCompiler.compile()
        path, ufoname = os.path.split(ufosource)
        ufo.features.text = "include(" + ufoname[:-4] + "_features.fea);"
        ufo.save(ufosource)
        with open(ufosFolder + "/" + ufoname[:-4] + "_features.fea", "w+") as fea:
            fea.write(feaCompiler.features)

def rewriteGlyphsFile(folder, path, file):
    """
    An issue not handled by glyphsLib right now
    is the wrong storage of Panose data as string
    (only user infos should be stored as string in last GlyphsApp specs).
    This script outputs a new glyphs file prefixed with "_fixed"
    and then use it to create the UFOs + designspace files.
    This function should be updated when other issues appear.
    """
    with open(path, "r") as gf:
        gf_line = gf.readlines()
        coupure = 0
        index = 0
        end = len(gf_line)
        refactored = ""
        for i in gf_line:
            if "name = panose;" in i:
                new = "value = ("
                index = gf_line.index(i, coupure, end) + 1
                coupure = index + 1
                string = gf_line[index]
                ll = string.split("    ")
                for i in ll[1:]:
                    nb = i.replace("\\012", "")
                    if ')";' in nb:
                        nb = nb.replace(')";', "")
                    new += "\n" + str(nb)
                new += ");\n"
                gf_line[index] = new
        for i in gf_line:
            refactored += i
    with open(folder + "/" + "fixed_" + file, "w+") as rewrited:
        rewrited.write(refactored)
    glyphs2ufos(folder + "/" + "fixed_" + file)

if __name__ == '__main__':
    import sys
    sys.exit(main())