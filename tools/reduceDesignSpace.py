#!/usr/bin/env python3
#from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor, BaseDocReader
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
"""
Rebuilt designspace
"""

def prettyLog(msg):
    diese = "".join(["-" for i in range(len(msg))])
    print(diese + diese + "\n" + msg)

def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--showDS", help = "show the content of designspace. Input a designspace")
    parser.add_argument("--reduce", help = "Input the path of the designspace to modify")
    parser.add_argument("-a", help = "input the name of the axis kept in the reduced Designspace")
    parser.add_argument("-r", nargs = 2, help = "input the range of the instances to keep. Ex: 200-400")
    args = parser.parse_args()
    return args

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

def showDesignspaceInstances(ds):
	listInstances = list()
	axes = list()
	axisDict = dict()
	designSpace = openDesignSpace(ds)
	neutralPos = {}
	q = ""
	#default = float
	for a in designSpace.axes:
		if a.map:
			for m in a.map:
				if m[0] == a.default:
					default = m[1]
					#print("neutral: ", default, a.default)
				if m[0] == a.minimum:
					minimum = m[1]
				if m[0] == a.maximum:
					maximum = m[1]
			axes.append([a.name, minimum, maximum])
			neutralPos[a.name] = default
		else:
			axes.append([a.name, a.minimum, a.maximum])
			neutralPos[a.name] = a.default
	print(neutralPos)
	#INSTANCES
	for i in designSpace.instances:
	# 	print(i.location.values())
	# 	for dim in i.location:
	# 		print(dim)
		listInstances.append([i.styleName, i.location])
		family = i.familyName
	prettyLog("The designspace features {nb} axes : ".format(nb = str(len(axes))))
	for a in axes:
		print("—— {name} axis that goes from {min} to {max}".format(name = a[0], min = a[1], max = a[2]))
	for a in axes:
		axisDict[a[0][0:2]] = a[0]
		q += "——For " + str([a[0]]) + " input " + str(a[0][0:2]) + "\n"
	q+= "——For all variations input 'all'" + "\n"
	prettyLog("From which one do you want to see the possible instances?")
	question = input(q)
	print("##########################")
	if question == "all":
		for i in listInstances:
			print(family, i[0])
	elif question in axisDict:
		lenList = list()
		wantedAx = axisDict[question]
		for i in listInstances:
			dico = copy.deepcopy(i[1])
			toDel = [ax for ax in dico if ax == wantedAx]
			for ax in toDel:
				del dico[ax]
			neutral = True
			for ax in dico:
				if dico[ax] != neutralPos[ax]:
					neutral = False
			if neutral is True:
				print(family, i[0], "-->", round(i[1][wantedAx]))
	if question != "all":
		reducing = input("Do you want to reduce the designspace? Y / N\n:")
		if reducing.upper() == "Y":
			scale = input("From which value, to which one? input 2 values separated with hyphen\n:")
			scaleList = scale.split("-")
			minimum = int(scaleList[0])
			maximum = int(scaleList[1])
			dspace = openDesignSpace(ds)
			for a in designSpace.axes:
				mapDico = dict()
				if a.name == axisDict[question]:
					if a.map:
						for m in a.map:
							mapDico[round(m[1])] = round(m[0])
						minimum = mapDico[int(scaleList[0])]
						maximum = mapDico[int(scaleList[1])]
			reduceDesignSpace(ds, axisDict[question], minimum, maximum)


def main():
	args = create_arg_parser()
	if "--showDS" in sys.argv:
		showDesignspaceInstances(args.showDS)
		#print(args.showDS)
	if "--reduce" in sys.argv:
		mini, maxi = args.r[0], args.r[1]
		reduceDesignSpace(args.reduce, args.a, mini, maxi)


if __name__ == '__main__':
    import sys
    sys.exit(main())