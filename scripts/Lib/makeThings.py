from fontTools import ufoLib, ttLib
from defcon import Font
from ufo2ft import compileOTF, compileTTF
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler
from glyphsLib import to_ufos, to_ufos, to_glyphs
import glyphsLib
from Lib.findThings import getFile, getFolder
import brotli
import glob
from fontTools.designspaceLib import DesignSpaceDocument
# from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
import os
from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
)
# import ttfautohint


def ufo2font(directory, ufolist, *output):
    path = getFolder(directory)
    for i in ufolist:
        ufoSource = path + i
        destination = ""
        ufo = Font(ufoSource)
        folder = path + "fonts/"
        featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter]
        print(output)
        if "otf" in output:
            destination = folder + "OTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            otf = compileOTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            otf.save(destination + i[:-4] + ".otf")
        if "ttf" in output:
            destination = folder + "TTF/"
            if not os.path.exists(destination):
                os.makedirs(destination)
            outlines = OutlineOTFCompiler(ufo).compile()
            feaCompiler = FeatureCompiler(ufo, outlines, featureWriters = featureWriters)
            feaCompiler.compile()
            # ufo.features.text = feaCompiler.features
            print(feaCompiler.features)
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


def ufosToGlyphs(family):
    repo = "src/" + family + "/"
    cwd = os.getcwd()
    rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
    source = rdir + "/" + family + ".designspace"
    ds = DesignSpaceDocument()
    ds.read(source)
    font = to_glyphs(ds)
    destination = rdir + "/Glyphs/"
    if not os.path.exists(destination):
        os.makedirs(destination)
    print(destination)
    font.save(destination + family + ".glyphs")

if __name__ == '__main__':
    print("lib imported")