import os

from fontTools                  import (ufoLib, ttLib)
from defcon                     import Font
from ufo2ft                     import (compileOTF, compileTTF)
from ufo2ft.featureCompiler     import FeatureCompiler
from ufo2ft.outlineCompiler     import OutlineOTFCompiler
from fontTools.designspaceLib   import DesignSpaceDocument
from ufo2ft.featureWriters      import (KernFeatureWriter,
                                        MarkFeatureWriter,
                                        loadFeatureWriters,
                                        ast,
                                        )
# import ttfautohint


def getFile(extension, directory):
    repo = "src/" + directory + "/"
    cwd = os.getcwd()
    rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
    source = rdir + "/" + directory + extension
    return source, rdir

def getFolder(directory):
    repo = "src/" + directory + "/"
    cwd = os.getcwd()
    rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo)) + "/"
    return rdir

def ufo2font(directory, ufolist, *output, fromInstances=False):
    path = getFolder(directory)
    for i in ufolist:
        ufoSource = path + i
        destination = ""
        ufo = Font(ufoSource)
        folder = path + "fonts/"
        if fromInstances is True:
            folder = os.path.abspath(os.path.join(path, os.pardir, "fonts")) + "/"
        featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter]
        # print(output)
        if "otf" in output:
            destination = folder + "OTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            otf = compileOTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            otf.save(destination + i[:-4] + ".otf")
            print(destination + i[:-4] + ".otf saved")
        if "ttf" in output:
            destination = folder + "TTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            # outlines = OutlineOTFCompiler(ufo).compile()
            # feaCompiler = FeatureCompiler(ufo, outlines, featureWriters = featureWriters)
            # feaCompiler.compile()
            # ufo.features.text = feaCompiler.features
            # print(feaCompiler.features)
            ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.save(destination + i[:-4] + ".ttf")
        if "woff2" in output:
            destination = folder + "WOFF2/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            if "ttf" not in output:
                ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.flavor = "woff2"
            ttf.save(destination + i[:-4] + ".woff2")
        if "woff" in output:
            destination = folder + "WOFF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            if "ttf" not in output and "woff2" not in output:
                ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.flavor = "woff"
            ttf.save(destination + i[:-4] + ".woff")


# def ufosToGlyphs(family):
#     repo = "src/" + family + "/"
#     cwd = os.getcwd()
#     rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
#     source = rdir + "/" + family + ".designspace"
#     ds = DesignSpaceDocument()
#     ds.read(source)
#     font = to_glyphs(ds)
#     destination = rdir + "/Glyphs/"
#     if not os.path.exists(destination):
#         os.makedirs(destination)
#     font.save(destination + family + ".glyphs")

if __name__ == '__main__':
    print("lib imported")