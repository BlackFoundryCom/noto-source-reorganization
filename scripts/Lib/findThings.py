import os

def getFile(extension, branche, directory):
	repo = branche + "/" + directory + "/"
	cwd = os.getcwd()
	rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
	source = rdir + "/" + directory + extension
	return source, rdir

def getTxtFile(directory, GTXT):
	repo = "src/" + directory + "/"
	cwd = os.getcwd()
	rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
	GTXTpath = [rdir + "/" + i for i in os.listdir(rdir) if i[-8:] == GTXT + ".txt"]
	return GTXTpath, rdir

def getFolder(directory):
	repo = "src/" + directory + "/"
	cwd = os.getcwd()
	rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo)) + "/"
	return rdir

def getGtxt(directory, GTXT):
	repo = "src/" + directory + "/"
	cwd = os.getcwd()
	rdir = os.path.abspath(os.path.join(cwd, os.pardir, repo))
	GTXTpath = [rdir + "/" + i for i in os.listdir(rdir) if i[-8:] == GTXT + ".txt"]
	return str(GTXTpath)