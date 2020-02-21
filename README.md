# noto-source-reorganization

This repository offers different functions to generate and manipulates Noto fonts. 
The best way to use it is to run NotoMaker.py (located in the script folder) in a terminal followed by the path of the folder of the family you want to work on.

So far NotoMaker has the following options:

-sub for subsetting. It display the available subsets if the fnt is subsettable (like latin-greek-cyrillic or arabic typefaces). 
  It displays the list and let the user input the needed one(s), then make the fonts. If you add the option -name you can rename the final fonts on the fly.

--script same as previous, but you have to give yourself the subsets you want to apply.

--fastgen : make all instances from the variable font (faster than interpolating UFOs and then generating fonts. But limited to ttf, woff, woff2 formats, and contours are not merged)

-var : generate variable fonts

-gen : interpolate and then generate the family. If the writing system is not a latin one, it add a "secure set" of glyphs from the NotoSans, NotoSerif, NotoSans-Italic or NotoSerif-Italic (depending if the style of the font).

--static : extract one or more instances from a variable font.

-r : rename the fonts
