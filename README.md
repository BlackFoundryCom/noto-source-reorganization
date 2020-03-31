# noto-source-reorganization

This repository offers different functions to generate and manipulates Noto fonts.
The best way to use it is to run NotoMaker.py (located in the script folder) in a terminal followed by an argument and the path of the family folder you want to work on.
	`python3 ~/NotoMaker.py [generation option] <folder path if needed> [output option] <list of format(s) in lowercase>`

So far NotoMaker has the following options:

-sub :  For subsetting. It display the available subsets if the fnt is subsettable (like latin-greek-cyrillic or arabic typefaces).
  It displays the list and let the user input the needed one(s), then make the fonts. If you add the option -name you can rename the final fonts on the fly.

--script : same as previous, but you have to give yourself the subsets you want to apply.

--fastgen : make all instances from the variable font (faster than interpolating UFOs and then generating fonts. But limited to ttf, woff, woff2 formats, and contours are not merged)

-var : generate the variable font.

-gen : interpolate and then generate the family. If the writing system is not a latin one, it add a "secure set" of glyphs from NotoSans, NotoSerif, NotoSans-Italic or NotoSerif-Italic (depending if the style of the font).

--static : extract one or more instances from a variable font.

-r : rename the fonts.

--salt : Set I.alt and J.alt stylistic alternate shapes as default in the generated font(s).

--allVF, --allOTF and --allTTF : These 3 commands don't need folder path since they work on all families.

--merge : give 2 folder paths for 2 families you want to merge. The script will find common style and create new fonts only for theses matching styles. To ensure a fast generation, it will use instances extracted from a variable font (unless the family has only one style).

NotoMaker needs Python 3.6. Regarding the librairies, it requires:
	+[fontTools (4.6.0)](https://github.com/fonttools/fonttools)
	+[ufo2ft (2.9.1)](https://github.com/googlefonts/ufo2ft) []
	+[defcon (0.6.0)](https://github.com/robotools/defcon)
	+[fontmake (2.0.3)](https://github.com/googlefonts/fontmake)
	+[ufoLib2 (0.6.2)](https://github.com/fonttools/ufoLib2)

If you don't have them already installed in your OS, you can download them from github
and install them with pip3, using the  `pip3 install -e .` command once in the folder.