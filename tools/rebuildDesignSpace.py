"""
Just put this script in same folder than the designspace to rebuild and run it
"""
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor, RuleDescriptor, BaseDocReader
from fontTools import designspaceLib
import os

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

def newDS(designSpace, familyName):
	ufosources, instances, axes, rules = list(), list(), list(), list()
	newDS = DesignSpaceDocument()
	# axes
	for a in designSpace.axes:
		ax = AxisDescriptor()
		ax.maximum = a.maximum
		ax.minimum = a.minimum
		ax.default = a.default
		ax.name = a.name
		ax.tag = a.tag
		ax.map = a.map
		newDS.addAxis(ax)

	#-------#
	# RULES #
	#-------#
	for r in designSpace.rules:
		rl = RuleDescriptor()
		rl.name = r.name
		rl.conditionSets = r.conditionSets
		rl.subs = r.subs
		newDS.addRule(rl)

	#---------#
	# masters #
	#---------#
	for s in designSpace.sources:
		src = SourceDescriptor()
		#src.path = s.path
		src.filename = s.filename
		src.filename = s.filename
		src.name = s.name
		src.familyName = familyName
		src.styleName = s.styleName
		src.location = s.location
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
		instance.name = i.name
		instance.filename = i.filename
		instance.familyName = familyName
		instance.styleName = i.styleName
		#instance.path = i.name
		instance.location = i.location
		instance.kerning = True
		instance.info = True
		newDS.addInstance(instance)

	return newDS


def rebuiltDesignSpace(path):
	typeface = os.path.split(path)[1]
	ds = typeface + ".designspace"
	designSpace = openDesignSpace(os.path.join(path, ds))
	content = newDS(designSpace, typeface)
	content.write(os.path.join(path, typeface + "_cleaned.designspace"))
	return typeface

#folder = os.getcwd().split("/")[-1]
# rebuiltDesignSpace(folder)
