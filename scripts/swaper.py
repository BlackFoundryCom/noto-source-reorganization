from fontTools import ttLib
from defcon import Font
from fontTools.designspaceLib import *
import ufo2ft
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.outlineCompiler import OutlineOTFCompiler
import os
from Lib.makeThings import ufo2font, ufosToGlyphs
from Lib.findThings import getFile, getFolder
import shutil
from Ufo2fontsFromdesignSpace import instances



def alterner(ufo):
    #Handle SALT 'I' and 'J'
    salts = []
    for g in ufo:
        if g.name.endswith('.salt'):
            salts.append(g)
            g.name += 'Temp'

    for g in salts:
        # g = ufo[name]
        dfltName = g.name[:-9] # name with .saltTemp removed
        saltName = g.name[:-4] # name ending .salt
        if dfltName in ufo.keys():
            dflt_g = ufo[dfltName]
            dfltUnicode = dflt_g.unicode
            g.unicode = dfltUnicode
            ufo[dfltName].name = saltName
            g.name = dfltName
            dflt_g.unicode = None
        elif '_' in dfltName: # handle the case of _sc.salt
            scName = '.'.join(saltName.split('_'))[:-5] # actual .sc name
            ufo[scName].name = '_'.join(scName.split('.'))+'.salt'
            g.name = scName

    # change also components
    for g in ufo:
        compoToRemove = []
        compoNamesToAdd = []
        for c in g.components:
            if c.baseGlyph in ['I.salt', 'J.salt']:
                compoToRemove.append(c)
                compoNamesToAdd.append(c.baseGlyph[:-5])
            if c.baseGlyph in ['I', 'J']:
                compoToRemove.append(c)
                compoNamesToAdd.append(c.baseGlyph+'.salt')

            if c.baseGlyph in['i_sc.salt', 'j_sc.salt']:
                compoToRemove.append(c)
                compoNamesToAdd.append('.'.join(c.baseGlyph.split('_'))[:-5])
            if c.baseGlyph in ['i.sc', 'j.sc']:
                compoToRemove.append(c)
                compoNamesToAdd.append('_'.join(c.baseGlyph.split('.')) + '.salt')

        for c, n in zip(compoToRemove, compoNamesToAdd):
            c.baseGlyph = n

    return ufo

    # Swap prop and tab (default) figures
    # prop = []
    # for g in ufo:
    #     if g.name.endswith('.lf'):
    #         g.name += 'Temp'
    #         for c in g.components:
    #             c.baseGlyph += '.lf'
    #         prop.append(g)

    # for g in prop:
    #     # print(g.name, 'temp glyph prop')
    #     dfltName = g.name[:-7] # name with .lfTemp removed
    #     tabName = g.name[:-4] # name ending .lf

    #     dflt_g = ufo[dfltName]
    #     # print(dflt_g.name, 'current default tab')
    #     dfltUnicode = dflt_g.unicode

    #     dflt_g.unicode = None
    #     dflt_g.name = tabName
    #     # print(dflt_g.name, 'new default name (tab)')

    #     g.unicode = dfltUnicode
    #     g.name = dfltName
        # print(g.name, 'prop name')


    # # compile OT features
    # outlines = OutlineOTFCompiler(ufo).compile()
    # feaCompiler = FeatureCompiler(ufo, outlines)
    # feaCompiler.compile()

    # # swap tnum and pnum features
    # ufo.features.text = rename_feature('pnum', 'Temp', ufo.features.text)
    # ufo.features.text = rename_feature('tnum', 'pnum', ufo.features.text)
    # ufo.features.text = rename_feature('Temp', 'tnum', ufo.features.text)

def swaper(family):
    ufosFolder = []
    folder = os.path.split(getFolder(family))[0]+"/"
    newFolder = os.path.abspath(os.path.join(folder, os.pardir, family+"AltIJ"))
    print(newFolder)
    ext = ["ufo", "designspace", "txt", "plist"]
    if not os.path.exists(newFolder):
        os.makedirs(newFolder)
    folderContent = list()
    for i in ext:
        temp = [folder + u for u in os.listdir(folder) if u.endswith(i)]
        for t in temp:
            folderContent.append(t)
    for i in folderContent:
        print(i)
    for i in folderContent:
        if i.endswith(".ufo"):
            name = os.path.basename(i)
            ufo = Font(i)
            modifiedUfo = alterner(ufo)
            modifiedUfo.save(os.path.join(newFolder, name))
        else:
            shutil.copy(i, newFolder)
    os.rename(newFolder+"/"+family+".designspace", newFolder+"/"+family+".designspace")
    instances(family+"AltIJ", newName=family+"AltIJ")