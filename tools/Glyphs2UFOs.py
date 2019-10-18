import os
from glyphsLib import build_masters

def main():
	path = sys.argv[1]
	if path[-7:] != ".glyphs":
		print("Please provide a glyphs file")
	else:
		folder, file = os.path.split(path)
		destination = folder + "/" + file[:-7] + "_UFOs"
		if not os.path.exists(destination):
			os.makedirs(destination)
		ufos, designspace_path = build_masters(path, destination)


if __name__ == '__main__':
	import sys
	sys.exit(main())