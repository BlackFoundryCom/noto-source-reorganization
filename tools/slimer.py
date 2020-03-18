from fontTools.designspaceLib import *
import os
import argparse
import copy
from ufo2ft.featureWriters import (
    KernFeatureWriter,
    MarkFeatureWriter,
    loadFeatureWriters,
    ast,
)
from defcon import Font
from fontTools import varLib
from ufo2ft import compileInterpolatableTTFsFromDS, postProcessor


def getFile(extension, branche, directory):
	repo = branche + "/" + directory + "/"
	cwd = os.getcwd()
	rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
	source = rdir + "/" + directory + extension
	return source

def openDesignSpace(path):
	designSpace = DesignSpaceDocument()
	designSpace.read(path)
	return designSpace

def designSpace2Var(designSpace):
	designSpace.loadSourceFonts(Font)
	font, _, _ = varLib.build(compileInterpolatableTTFsFromDS(designSpace), optimize=False)
	return font

def reducer(designSpace, axe2keep, mini, maxi):
	print("Kept axe >> ", axe2keep)
	variationToExclude = dict()
	ufosources, instances, axes = list(), list(), list()
	newDS = DesignSpaceDocument()
	mini_, maxi_ = int(), int()
	# axes
	for a in designSpace.axes:
		ax = AxisDescriptor()
		if a.name == axe2keep:
			mappy = []
			ax.maximum = maxi
			ax.minimum = mini
			ax.default = mini
			ax.name = a.name
			ax.tag = a.tag
			if a.map:
				for m in a.map:
					#print(m, m[0], m[1])
					if m[0] >= mini and m[0] <= maxi:
						print("map >>", m)
						mappy.append(m)
					if m[0] == mini:
						mini = m[1]
					if m[0] == maxi:
						maxi = m[1]
				ax.map = mappy
			newDS.addAxis(ax)
		else:
			variationToExclude[a.name] = a.default
			if a.map:
				for m in a.map:
					if m[0] == a.default:
						variationToExclude[a.name] = m[1]

	#---------
	# masters
	#---------
	for s in designSpace.sources:
		src = SourceDescriptor()
		for dim in s.location:
			if dim == axe2keep:
				addSource = True
				if len(variationToExclude) > 0:
					for exclude in variationToExclude:
						if s.location[exclude] != variationToExclude[exclude]:
							# print("STOP")
							addSource = False
						if addSource:
							# print("GO FOR IT", s.location)
							if mini <= s.location[dim] <= maxi:
								# print("\tIT'S IN THE NEW SCALE")
								dico = dict()
								dico[dim] = s.location[dim]
								# print("DICO", dico)
								src.filename = s.filename
								src.name = s.name
								src.familyName = s.familyName
								src.styleName = s.styleName
								src.location = dico
								src.layerName = s.layerName
								# Do we need to keep this True or False ?
								src.copyLib = True
								src.copyInfo = True
								src.copyGroups = True
								src.copyFeatures = True
								newDS.addSource(src)
				elif mini <= s.location[dim] <= maxi:
					# print("\tIT'S IN THE NEW SCALE")
					dico = dict()
					dico[dim] = s.location[dim]
					# print("DICO", dico)
					src.filename = s.filename
					src.name = s.name
					src.familyName = s.familyName
					src.styleName = s.styleName
					src.location = dico
					src.layerName = s.layerName
					# Do we need to keep this True or False ?
					src.copyLib = True
					src.copyInfo = True
					src.copyGroups = True
					src.copyFeatures = True
					newDS.addSource(src)

	#-----------
	# instances
	#-----------

	for i in designSpace.instances:
		instance = InstanceDescriptor()
		for dim in i.location:
			if dim == axe2keep:
				addInstance = True
				if len(variationToExclude) > 0:
					for exclude in variationToExclude:
						if i.location[exclude] != variationToExclude[exclude]:
							# print("STOP")
							addInstance = False
						if addInstance:
							if mini <= i.location[dim] <= maxi:
								dico = dict()
								dico[dim] = i.location[dim]
								instance.name = i.name
								instance.filename = i.filename
								instance.familyName = i.familyName
								instance.styleName = i.styleName
								instance.location = dico
								instance.kerning = True
								instance.info = True
								newDS.addInstance(instance)
				elif mini <= i.location[dim] <= maxi:
					dico = dict()
					dico[dim] = i.location[dim]
					instance.name = i.name
					instance.filename = i.filename
					instance.familyName = i.familyName
					instance.styleName = i.styleName
					instance.location = dico
					instance.kerning = True
					instance.info = True
					newDS.addInstance(instance)

	return newDS


def reduceDesignSpace(designspacePath, axe2keep, mini, maxi):
	default = min
	designSpace = openDesignSpace(designspacePath)
	path, name  = os.path.split(designspacePath)
	filename = name.split(".")[0]
	content = reducer(designSpace, axe2keep, int(mini), int(maxi))
	content.write((os.path.join(path, filename + "_reduced.designspace")))
	#print(os.path.join(path, filename + "_reduced.designspace"))
	fontname = name[:-12]+"-VF.ttf"
	destination = os.path.join(path, "SLIMVAR")
	if not os.path.exists(destination):
		os.makedirs(destination)
	ft = designSpace2Var(openDesignSpace(os.path.join(path, filename + "_reduced.designspace")))
	ft.save(os.path.join(destination, fontname))


def mapping(ds, mini, maxi):
	for a in ds.axes:
		if a.tag == "wght":
			if a.map:
				mapDico = dict()
				for m in a.map:
					mapDico[round(m[1])] = round(m[0])
				mini = mapDico[int(mini)]
				maxi = mapDico[int(maxi)]
			else:
				mini = mini
				maxi = maxi
	return mini, maxi

def findRegBoldLocation(path):
	mini, maxi = 0, 0
	ds = openDesignSpace(path)
	tag2Name = dict()
	for a in ds.axes:
		tag2Name[a.tag] = a.name
	for ins in ds.instances:
		if ins.styleName == "Regular" or ins.styleName == "Italic":
			for dim in ins.location:
				if dim == tag2Name["wght"]:
					mini = ins.location[dim]
		if ins.styleName == "Bold" or ins.styleName == "Bold Italic":
			for dim in ins.location:
				if dim == tag2Name["wght"]:
					maxi = ins.location[dim]
	minimum, maximum = mapping(ds, mini, maxi)
	return minimum, maximum, tag2Name


def slimer(family):
	path = getFile(".designspace", "src", family)
	mini, maxi, tag2Name = findRegBoldLocation(path)
	print(family, "Regular is located at", mini, "and", family, "Bold is located at", maxi)
	reduceDesignSpace(path, tag2Name["wght"], mini, maxi)

slimer("NotoSans-Italic")
