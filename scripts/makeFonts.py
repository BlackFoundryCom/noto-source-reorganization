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



def ufo2font(directory, ufolist, output, fromInstances=False):
    path = os.path.abspath(os.path.join(os.pardir, "src", directory))
    for i in ufolist:
        ufoSource = os.path.join(path, i)
        destination = ""
        ufo = Font(ufoSource)
        folder = os.path.join(path, "fonts")
        if fromInstances is True:
            folder = os.path.abspath(os.path.join(path, os.pardir, "fonts"))
        featureWriters = [KernFeatureWriter(mode="append"), MarkFeatureWriter]
        if "otf" in output:
            destination = os.path.join(folder, "OTF")
            if not os.path.exists(destination):
                os.makedirs(destination)
            otf = compileOTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            otf.save(os.path.join(destination, i[:-4] + ".otf"))
            print(destination + i[:-4] + ".otf saved")
        if "ttf" in output:
            destination = os.path.join(folder, "TTF")
            if not os.path.exists(destination):
                os.makedirs(destination)
            ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.save(os.path.join(destination, i[:-4] + ".ttf"))
        if "woff2" in output:
            destination = os.path.join(folder, "WOFF2")
            if not os.path.exists(destination):
                os.makedirs(destination)
            if "ttf" not in output:
                ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.flavor = "woff2"
            ttf.save(os.path.join(destination, i[:-4] + ".woff2"))
        if "woff" in output:
            destination = os.path.join(folder, "WOFF")
            if not os.path.exists(destination):
                os.makedirs(destination)
            if "ttf" not in output and "woff2" not in output:
                ttf = compileTTF(ufo, removeOverlaps=True, useProductionNames = False, featureWriters = featureWriters)
            ttf.flavor = "woff"
            ttf.save(os.path.join(destination, i[:-4] + ".woff"))

if __name__ == '__main__':
    print("lib imported")