import os
from glyphsLib import build_masters
from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
)
from defcon import Font
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler

"""
Use (in console) : python3 <Glyphs2UFOs.py script path> [option] <input Glyphs file>
    Option:
    -k : output features with GPOS rules added as separate features.fea file
    use the keyword include(<features file path>); in ufo instead of previous features parsed by glyphsLib
"""

def main():
    glyphs2ufos(sys.argv[-1])

def glyphs2ufos(path):
    if path[-7:] != ".glyphs":
        print("Please provide a Glyphs file")
    else:
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
    ufolist = list()
    for file in os.listdir(ufosFolder):
        # print(ufo)
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
    This script rewrite the glyphs file prefixed with a "_fixed"
    and then use it to create the UFOs + designspace files.
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