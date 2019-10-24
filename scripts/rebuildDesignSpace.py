"""
Just put this script in same folder than the designspace to rebuild and run it
"""
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor, BaseDocReader
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
	ufosources, instances, axes = list(), list(), list()
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

	#---------
	# masters
	#---------
	for s in designSpace.sources:
		src = SourceDescriptor()
		src.path = s.path
		src.name = s.name
		src.familyName = familyName
		src.styleName = s.styleName
		src.location = s.location
		src.layerName = s.layerName
		# src.copyLib = True
		# src.copyInfo = True
		# src.copyGroups = True
		# src.copyFeatures = True
		newDS.addSource(src)

	#-----------
	# instances
	#-----------

	for i in designSpace.instances:
		instance = InstanceDescriptor()
		instance.name = i.name
		instance.familyName = familyName
		instance.styleName = i.styleName
		instance.path = i.name
		instance.location = i.location
		instance.kerning = True
		instance.info = True
		newDS.addInstance(instance)

	return newDS


def rebuiltDesignSpace(typeface):
	path = typeface + ".designspace"
	designSpace = openDesignSpace(path)
	content = newDS(designSpace, typeface)
	content.write(os.path.abspath(os.path.join(path, os.pardir, typeface + "_cleaned.designspace")))

folder = os.getcwd().split("/")[-1]
rebuiltDesignSpace(folder)
