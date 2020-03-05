import os
from fontTools.misc.plistlib import load as readPlist
import defcon


def contentOfClass(l):
    s = str()
    for i in l:
        s = s + " " + i
    return s + " "


### IF list is set to False, gives you the groups put in a dict
def getGroups(lookupGroupsRaw, MarkAttachmentType=False):
    groupsListRaw = list()
    classDefinition = dict()
    groupsList = []
    ClassTxt = ""
    groupsListRawbis = []
    grpDict = dict()
    groupsTag = []

    for i in lookupGroupsRaw:
        if "class definition begin" in i:
            j = lookupGroupsRaw.index(i) + 1
            while "class definition end" not in lookupGroupsRaw[j]:
                groupsListRaw.append(lookupGroupsRaw[j])
                j += 1
    groupsListRaw.append("void")

    ### PUT COMMON GLYPHS IN EACH CLASS BY COMPARING THEIR TAGGED NUMBER ###
    grpNum = 1
    for i in groupsListRaw[:-1]:
        j = groupsListRaw.index(i) + 1
        if i[-1:] == groupsListRaw[j][-1:]:
            groupsList.append(i.split()[0])
        elif len(groupsList) != 0:
            classDefinition[str(grpNum) + "_" + groupsList[0]] = groupsList
            groupsList = []
            grpNum +=1
    for i in classDefinition:
        if MarkAttachmentType is True:
            ClassTxt += ("@" + i[0:1] + " = [" + contentOfClass(classDefinition[i]) +  "];\n")
        else:
            ClassTxt += ("@" + i + " = [" + contentOfClass(classDefinition[i]) +  "];\n")
    return ClassTxt

def getGroupsAsDict(lookupGroupsRaw, start = "class definition begin"):
    groupsListRaw = list()
    classDefinition = dict()
    groupsList = []
    ClassTxt = ""
    grpDict = dict()
    groupsTag = []
    for i in lookupGroupsRaw:
        if start in i:
            j = lookupGroupsRaw.index(i) + 1
            while "class definition end" not in lookupGroupsRaw[j]:
                groupsListRaw.append(lookupGroupsRaw[j])
                j += 1

    for i in groupsListRaw:
        if len(i) > 0:
            isplit = i.split("\t")
            if isplit[1] not in groupsTag:
                groupsTag.append(isplit[1])
        for i in groupsTag:
            grpDict[i] = [j.split("\t")[0] for j in groupsListRaw if j.split("\t")[1] == i]

    return grpDict

def parseLookupflag(chapeau):
    lookupflag = ""
    for j in chapeau:
        if "yes" in j:
            lookupflag += j[:-4] + " "
        if "MarkAttachmentType" in j:
            lookupflag += " @_MarkAttachmentType_".join(j.split("\t")) + " "
        if "MarkFilterType" in j:
            lookupflag += " @_FilterSet_".join(j.split("\t")).replace("MarkFilterType","UseMarkFilteringSet")
    if len(lookupflag) != 0:
        lookupflag = "    lookupflag " + lookupflag + " ;\n"
    return lookupflag


def parseSingleGSUB(name, lookup):
    single_txt = ""
    single_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        single_txt += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        j_list = j.split("\t")
        single_txt += "\tsub " + j_list[0] + " by " +  j_list[1] + " ;\n"
    single_txt += "    } " + name[2:-2] + " ;\n\n"
    return str(single_txt)

def parseMultipleGSUB(name, lookup):
    issues = []
    presenceOfSingleInMultiple = 0
    multiple_txt = ""
    single_to_separate = "lookup " + name[2:-2] + "_alt_single {\n"
    multiple_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        multiple_txt += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        j_list = j.split("\t")
        if len(j_list) >= 3:
            multiple_txt += "\tsub " + j_list[0] + " by"
            for g in j_list[1:]:
                multiple_txt += " " + g
            multiple_txt += " ;\n"
        elif len(j_list)<3:
            if name[2:-2] not in issues:
                issues.append(name[2:-2])
            presenceOfSingleInMultiple = 1
            single_to_separate += "\tsub " + j_list[0] + " by " + j_list[0] +" ;\n"
    multiple_txt += "    } " + name[2:-2] + " ;\n\n"
    single_to_separate += "    } " + name[2:-2] + "_alt_single ;\n\n"
    if presenceOfSingleInMultiple == 1:
        multiple_txt += single_to_separate
    return str(multiple_txt), issues

def parseLigatureGSUB(name, lookup):
    ligaGsub = ""
    ligaGsub += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        ligaGsub += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        if "MarkFilterType" not in j:
            j_list = j.split("\t")
            ligaGsub += "    sub "
            for g in j_list[1:]:
                ligaGsub += g + " "
            ligaGsub += "by " + j_list[0] + " ;\n"
    ligaGsub += "    } " + name[2:-2] + " ;\n\n"
    return str(ligaGsub)

##########################
#### GPOS LookupType 1 ###
##########################
"""
stored => position type tab Glyph tab value
output => position Glyphname <value record with a valur in y advance or x advance>
"""
def parseSingleGPOS(name, lookup):
    single_txt = ""
    single_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        single_txt += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        j_list = j.split("\t")
        if "x advance" in j_list[0]:
            single_txt += "\tposition " + j_list[1] + " < 0 0 " +  j_list[2] + " 0 >;\n"
        elif "y advance" in j_list[0]:
            single_txt += "\tposition " + j_list[1] + " < 0 0 0 " +  j_list[2] + " >;\n"
        elif "x placement" in j_list[0]:
            single_txt += "\tposition " + j_list[1] + " < " + j_list[2] + " 0 0 0 >;\n"
        elif "y placement" in j_list[0]:
            single_txt += "\tposition " + j_list[1] + " < 0 " + j_list[2] + " 0 0 >;\n"
    single_txt += "    } " + name[2:-2] + " ;\n\n"
    return str(single_txt)

##########################
#### GPOS LookupType 2 ###
##########################
"""

"""
def parseKernsetGPOS(name, lookup):
    # NEDD TO MAKE THE RTL VERSION, and THE Y VERSION
    kernset_txt = ""
    kernset_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        kernset_txt += parseLookupflag(lookup[0:6])
    # GET THE CONTENT OF THE LOOKUP, AND IF GROUPS ARE DEFINED, GET THEM
    contenu = [x for x in lookup if x != '']
    classList = []
    if "firstclass definition begin" in contenu:
        for i in contenu:
            if "firstclass definition begin" in i:
                classList.append("firstclass definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        firstclass = getGroupsAsDict(classList, start = "firstclass definition begin")
        refactoredGroups = unpackGroupsFromDict(firstclass, name[2:-2], namingConvention = "\t@_firstclass_group_")
        kernset_txt += refactoredGroups + "\n"
    if "secondclass definition begin" in contenu:
        for i in contenu:
            if "secondclass definition begin" in i:
                classList.append("secondclass definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        secondclass = getGroupsAsDict(classList, start = "secondclass definition begin")
        refactoredGroups = unpackGroupsFromDict(secondclass, name[2:-2], namingConvention = "\t@_secondclass_group_")
        kernset_txt += refactoredGroups + "\n"
    for j in lookup[4:]:
        j_list = j.split("\t")
        if "left x advance" in j_list[0]:
            try:
                int(j_list[1])
                one = "@_firstclass_group_" + str(j_list[1]) + "_" + name[2:-2]
            except:
                one = j_list[1]
            try:
                int(j_list[2])
                two = "@_secondclass_group_" + str(j_list[2]) + "_" + name[2:-2]
            except:
                two = j_list[2]
            kernset_txt += "\tposition " + " ".join([one, two, j_list[3]]) + " ;\n"
        if "left x placement" in j_list[0]:
            try:
                int(j_list[1])
                one = "@_firstclass_group_" + str(j_list[1]) + "_" + name[2:-2]
            except:
                one = j_list[1]
            try:
                int(j_list[2])
                two = "@_secondclass_group_" + str(j_list[2]) + "_" + name[2:-2]
            except:
                two = j_list[2]
            kernset_txt += "\tposition " + " ".join([one, two]) + " < " + j_list[3] + " 0 0 0 >;\n"
    #     elif "y advance" in j_list[0]:
    #         kernset_txt += "\tposition " + j_list[1] + " < 0 0 0 " +  j_list[2] + " >;\n"
    #     elif "x placement" in j_list[0]:
    #         kernset_txt += "\tposition " + j_list[1] + " < " + j_list[2] + " 0 0 0 >;\n"
    #     elif "y placement" in j_list[0]:
    #         kernset_txt += "\tposition " + j_list[1] + " < 0 " + j_list[2] + " 0 0 >;\n"
    kernset_txt += "    } " + name[2:-2] + " ;\n\n"
    return str(kernset_txt)


##########################
#### GPOS LookupType 3 ###
##########################
"""
stored => entry or exit is precised the Glyph, than value of the anchor
output =>"postion cursive" + glyphname + if "entry" the value of entry anchor then "<anchor NULL>"
            if "exit" forst the NULL anchor, tha, the anchro value stored
"""
def parseCursive(name, lookup):
    curs_txt = ""
    curs_txt += "lookup " + name[2:-2] + " {\n"
    entryDict = dict()
    exitDict = dict()
    rule = ""
    if len(parseLookupflag(lookup[0:6])) != 0:
        curs_txt += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        j_list = j.split("\t")
        if j_list[0] == "entry":
            if len(j_list) == 4:
                entryDict[j_list[1]] = j_list[2] + " contourpoint " + j_list[3]
            else:
                entryDict[j_list[1]] = j_list[2]
        else:
            exitDict[j_list[1]] = j_list[2]
    for k in entryDict:
        entry = entryDict[k].replace(",", " ")
        if k in exitDict:
            exit = exitDict[k].replace(",", " ")
        else:
            exit = "NULL"
        curs_txt +=  "\tposition cursive " + k + " <anchor "+ entry + ">" + " <anchor "+ exit + ">;\n"
    for k in exitDict:
        if k not in entryDict:
            exit = exitDict[k].replace(",", " ")
            curs_txt += "\tposition cursive " + k + " <anchor NULL>" + " <anchor "+ exit + ">;\n"
    curs_txt += "    } " + name[2:-2] + " ;\n\n"
    return str(curs_txt)

##########################
#### GPOS LookupType 4 ###
##########################
"""
 stored => first the mark glyph with "mark" at beginning of ligne, glyphname, anchor value and a tag number for the class of anchor
                then the base glyphs with "base" at beginning of ligne, glyphname, anchor value and a tag number for the class of mark anchor
 output => a ligne for each mark glyph, the anchor value and the name of its class
                a ligne for each base glyph, the anchor value and the name of the mark class than can be called with it
"""
def parseMark2base(name, lookup):
    m2b_txt = ""
    markDict =dict()
    rules = ""
    m2b_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        m2b_txt += parseLookupflag(lookup[0:6])
    for ligne in lookup[4:]:
        ligneSplit =ligne.split("\t")
        # create a ligne for the mark glyph, gives the anchor value and the name of its class
        if "mark" in ligne:
            rules += "    markClass " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + "> @_MARKCLASS_" + \
            str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
        # create a ligne for the base glyph, gives the anchor value and the name of its class
        elif "base" in ligne:
            rules += "    position base " + ligneSplit[1] + " <anchor " + \
                        ligneSplit[3].replace(",", " ") + "> " + "mark @_MARKCLASS_" + str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
    m2b_txt = m2b_txt + rules + "    } " + name[2:-2] + " ;\n\n"
    return m2b_txt


##########################
#### GPOS LookupType 5 ###
##########################
"""
 stored => mark class: same as in parseMark2Base. Then lignes with "ligature" store the glyph, a tab, wich substitued glyph receive an anchor,
            a tab, how many are substitued, a tab, the tag number of the mark class, a tab, the anchor value
 output => mark class: same ase Mark2Base. Ligature: "position ligature" and by element of ligature:
                if it receive the anchor the syntax is the same as  mark2base, for other element write <anchor NULL> and "ligComponent"
"""
def parseMark2Ligature(name, lookup):
    m2lig_txt = ""
    markDict =dict()
    rules = ""
    whichCompo = 0
    previousGlyph = ""
    m2lig_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        m2lig_txt += parseLookupflag(lookup[0:6])
    for ligne in lookup[4:]:
        ligneSplit = ligne.split("\t")
        # create a ligne for the mark glyph, gives the anchor value and the name of its class
        if ligneSplit[0] == "mark":
            rules += "markClass " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + "> @_MARKCLASS_" + \
            str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
        elif "ligature" in ligne:
            indice = lookup[4:].index(ligne) + 1
            # first compare with previous ligne, if it's the same component that receives a mark class
            if whichCompo == ligneSplit[2]:
                rules += " <anchor " + ligneSplit[5].replace(",", " ") + "> " + \
                "mark @_MARKCLASS_" + str(ligneSplit[4]) + "_lookup_" + name.split('_')[1]
                # if whichCompo == ligneSplit[2] and ligneSplit[2] == ligneSplit[3]:
                #   rules += ";"
            elif int(ligneSplit[2]) == 1 and whichCompo != ligneSplit[2]:
                rules += "\nposition ligature " + ligneSplit[1] + "\n\t\t\t<anchor " + ligneSplit[5].replace(",", " ") + "> " + \
                "mark @_MARKCLASS_" + str(ligneSplit[4]) + "_lookup_" + name.split('_')[1]
            elif int(ligneSplit[2]) > 1:
                rules += "\n\t\t\tligComponent <anchor " + ligneSplit[5].replace(",", " ") + "> mark @_MARKCLASS_" + \
                    str(ligneSplit[4]) + "_lookup_" + name.split('_')[1]
            # if ligneSplit[2] == ligneSplit[3] and end is False:
            #   rules += ";"
            if indice < len(lookup[4:]):
                if ligneSplit[1] not in lookup[4:][indice]:
                    rules += ";"
                # if previousGlyph != ligneSplit[1]:
                #   rules += ";\n"
                # if ligneSplit[2] == ligneSplit[3]:
                #   rules += ";\n"
            # if whichCompo == ligneSplit[2] and ligneSplit[2] == ligneSplit[3]:
            # store the index of component
            whichCompo = ligneSplit[2]
            end = False
    m2lig_txt = m2lig_txt + rules + ";\n    } " + name[2:-2] + " ;\n\n"

    return m2lig_txt

##########################
#### GPOS LookupType 6 ###
##########################
"""
 stored => same as mark2base
 output => same as mark2base but with "position mark" written at the beginning
"""
def parseMark2Mark(name, lookup):
    m2m_txt = ""
    markDict =dict()
    rules = ""
    m2m_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        m2m_txt += parseLookupflag(lookup[0:6])
    for ligne in lookup[4:]:
        ligneSplit =ligne.split("\t")
        # create a ligne for the mark glyph, gives the anchor value and the name of its class
        if ligneSplit[0] == "mark":
            rules += "markClass " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + "> @_MARKCLASS_" + \
            str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
        elif "base" in ligne:
            rules += "position mark " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + \
            "> mark @_MARKCLASS_" + str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
    m2m_txt = m2m_txt + rules + "    } " + name[2:-2] + " ;\n\n"
    return m2m_txt


##########################
#### GPOS LookupType 7 ###
##########################
"""
 stored => first create groups by listing glyphs and tagged them with a number. Same number = same group
            then define context (ligns with "class at the beginning")
            the context is written betwen firsst and second tabulation. It is written by the number of the group
            After second tab the couple of 2 number are indicating 1) wich gropu of the context is impacted, and 2) which
            lookup of the GPOS table is called to impact it.
            The Coverage context is another story not made yet => TODO
 output => first make the groups, then write "position" and th succesion of group creating the context
            then check which element of the contect is impacted, add a ' (quotesingle) after the group and the name of the lookup
            each element of the contect can receive a lookuup.
"""
def parseContextGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos"):
    indiceOfModifiedGlyph = dict()
    contextPOS_txt = ""
    rule = ""
    coupure = 0
    # GET THE NAME AND THE LOOKUPFLAGS IF NEEDED
    contextPOS_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        contextPOS_txt += parseLookupflag(lookup[0:6])
    # GET THE CONTENT OF THE LOOKUP, IF GROUPS ARE DEFINED, GET THEM
    contenu = [x for x in lookup if x != '']
    for e in contenu:
        if 'class definition end' in e:
            coupure = contenu.index(e) + 1
    # GET GROUPS WRTITTEN IN THE BEGINNING OF THE LOOKUP
    groupsOfThisLookup = getGroupsAsDict(contenu)
    for i in groupsOfThisLookup:
        grp = "\t@_group_" + i + "_" + name[2:-2] + " = [ "
        c = 0
        if len(groupsOfThisLookup[i]) < 10:
            for j in groupsOfThisLookup[i]:
                grp += j + " "
        else:
            for j in groupsOfThisLookup[i]:
                if c < 6:
                    grp += j + " "
                    c += 1
                else:
                    grp += j + "\n\t"
                    c = 0
        grp += "];"
        contextPOS_txt += grp + "\n"
    ### ADD THE CONTENT OF THE LOOKUP MINUS THE GROUPS IN FEATURE FILE
    for j in contenu[coupure:]:
        j_list = j.split("\t")
        calledLookups = list()
        indexOfModifiedClassList = list()
        #all numbers after the 2nd tab are reference to lookup. Get them
        for z in range(2,len(j_list)):
            numeroLookup = j_list[z].split(",")[1].replace(" ", "")
            indexOfModifiedClass = j_list[z].split(",")[0].replace(" ", "")
            lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
            calledLookups.append([indexOfModifiedClass, lookup_name])
            indexOfModifiedClassList.append(indexOfModifiedClass)
        for e in indexOfModifiedClassList:
            w = indexOfModifiedClassList.index(e)
            indexOfModifiedClassList.pop(w)
            # IF A LOOKUP IS APPLIED TO THE SAME CONTEXTUAL GROUP, WRITE THE RULE TWICE? WITH DIFFERENT LOOKUP CALLED
            if e in indexOfModifiedClassList:
                for call in calledLookups:
                    if "class" in j:
                        rule += "\t" + keyword + " "
                        context = j_list[1].split(",")
                        index = 1
                        for i in context:
                            i = i.replace(" ", "")
                            rule += "@_group_" + i + "_" + name[2:-2] + "' "
                            if int(call[0]) == index:
                                rule += "lookup " + call[1] + " "
                            index += 1
                        rule += ";\n"
            else:
                if "class" in j:
                    rule += "\t" + keyword + " "
                    context = j_list[1].split(",")
                    index = 1
                    for i in context:
                        i = i.replace(" ", "")
                        rule += "@_group_" + i + "_" + name[2:-2] + "' "
                        for cL in calledLookups:
                            if int(cL[0]) == index:
                                rule += "lookup " + cL[1] + " "
                        index += 1
                rule += ";\n"
    ####################################################
    ### /!\ TODO /!\ look at parseChainedGPOSGSUB() ###
    ####################################################
        if "coverage" in j:
            contextPOS_txt += j + "\n"
    contextPOS_txt +=  rule + "\n   } " + name[2:-2] + " ;\n\n"
    return str(contextPOS_txt)

##########################
#### GPOS LookupType 8 ###
##########################
def parseChainedGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos"):
    chainedPOS_txt = ""
    rule = ""
    # GET THE NAME AND THE LOOKUPFLAGS IF NEEDED
    chainedPOS_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        chainedPOS_txt += parseLookupflag(lookup[0:6])
    # GET THE CONTENT OF THE LOOKUP, IF GROUPS ARE DEFINED, GET THEM
    contenu = [x for x in lookup if x != '']
    # print(contenu)
    if "backtrackclass definition begin" in contenu:
        classList = []
        for i in contenu:
            if i == "backtrackclass definition begin":
                classList.append("backtrackclass definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        backtrackclass = getGroupsAsDict(classList, start = "backtrackclass definition begin")
        refactoredGroups = unpackGroupsFromDict(backtrackclass, name[2:-2], namingConvention = "\t@_backtrack_group_")
        chainedPOS_txt += refactoredGroups + "\n"
    if "class definition begin" in contenu:
        classList = []
        # print(name)
        for i in contenu:
            if i == "class definition begin":
                # print("input class def begin")
                classList.append("class definition begin")
                j = contenu.index(i) + 1
                # print(i, "start at", j)
                while "class definition end" not in contenu[j]:
                    # print(contenu[j])
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
                # print(classList)
                # print("end\n")
        inputclass = getGroupsAsDict(classList)
        refactoredGroups = unpackGroupsFromDict(inputclass, name[2:-2], namingConvention = "\t@_impacted_group_")
        chainedPOS_txt += refactoredGroups + "\n"
    if "lookaheadclass definition begin" in contenu:
        print("lookaheadclass in", name[2:-2])
        classList = []
        for i in contenu:
            if i == "lookaheadclass definition begin":
                classList.append("lookaheadclass definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        lookaheadclass = getGroupsAsDict(contenu, start = "lookaheadclass definition begin")
        refactoredGroups = unpackGroupsFromDict(lookaheadclass, name[2:-2], namingConvention = "\t@_lookahead_group_")
        print(refactoredGroups)
        chainedPOS_txt += refactoredGroups + "\n"
    # COVERAGE
    backtrackcoverage, inputcoverage, lookaheadcoverage = "", "", ""
    coverage = ""
    if "backtrackcoverage definition begin" in contenu:
        for i in contenu:
            if "backtrackcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    # classList.append(contenu[j])
                    coverage += contenu[j] + " "
                    j += 1
                coverage += " ]"
        backtrackcoverage = coverage
        coverage = ""
        # print(backtrackcoverage)
        # chainedPOS_txt += backtrackcoverage + "\n"
    if "inputcoverage definition begin" in contenu:
        for i in contenu:
            if "inputcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    # classList.append(contenu[j])
                    coverage += contenu[j] + " "
                    j += 1
                coverage += " ]"
        inputcoverage = coverage
        coverage = ""
        # print(inputcoverage)
    if "lookaheadcoverage definition begin" in contenu:
        for i in contenu:
            coverage = " [ "
            if "lookaheadcoverage definition begin" in i:
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    # classList.append(contenu[j])
                    coverage += contenu[j] + " "
                    j += 1
        coverage += " ]"
        lookaheadcoveragecoverage = coverage
        coverage = ""
        # print(lookaheadcoveragecoverage)
    # RULES
    for i in contenu:
        if "class-chain" in i:
            isplit = i.split("\t")
            _backtrack_group = isplit[1].split(",")
            _input_groups = isplit[2].split(",")
            _lookahead_groups = isplit[3].split(",")
            _lookup_called = list()
            for e in isplit[4:]:
                if e.split(",") not in _lookup_called:
                    _lookup_called.append(e.split(","))
            # print(_lookup_called)
            rule += "    " + keyword + " "
            if _backtrack_group[0] != "":
                for x in _backtrack_group:
                    x = x.replace(" ", "")
                    rule += "@_backtrack_group_" + x + "_" + name[2:-2] + " "
            for x in _input_groups:
                x = x.replace(" ", "")
                rule += "@_impacted_group_" + x + "_" + name[2:-2]  + "' "
            for x in _lookup_called:
                x = x[1].replace(" ", "")
                #BUG????
                #x = int(x) + 1
                x = int(x)
                lookup_name = str(namesAndContentsLookup[x][0])[2:].strip("['']")
                rule += "lookup " + lookup_name + " "
            # for x in _lookup_called[1].replace(" ", ""):
            #   x = int(x)
            #   lookup_name = str(namesAndContentsLookup[x][0])[2:].strip("['']")
                # rule += "lookup " + lookup_name + " "
            if _lookahead_groups[0] != "":
                for x in _lookahead_groups:
                    x = x.replace(" ", "")
                    rule += "@_lookahead_group_" + x + "_" + name[2:-2] + " "
            rule += ";\n"
        elif "coverage\t" in i:
            x = i.split(",")[1]
            lookup_name = str(namesAndContentsLookup[int(x)][0])[2:].strip("['']")
            chainedPOS_txt += "    " + keyword + backtrackcoverage + inputcoverage \
                + "' lookup " + lookup_name + lookaheadcoverage + " ;"
    chainedPOS_txt =  chainedPOS_txt + rule + "\n    } " + name[2:-2] + " ;\n\n"
    # print(chainedPOS_txt)
    return chainedPOS_txt


def unpackGroupsFromDict(groupDict, localname, namingConvention = "\t@_group_"):
    grp = ""
    unpackedClass = ""
    if localname != "":
        localname = "_" + localname
    for i in groupDict:
        grp = namingConvention + i + localname + " = [ "
        c = 0
        if len(groupDict[i]) < 10:
            for j in groupDict[i]:
                grp += j + " "
        else:
            for j in groupDict[i]:
                if c < 6:
                    grp += j + " "
                    c += 1
                else:
                    grp += j + "\n\t"
                    c = 0
        grp += "];\n"
        unpackedClass += grp
    return unpackedClass


def readGPOS(monotypeFeaturesTxt, rdir):
    namesAndContentsLookup = list()
    lookupContent = list()
    txt = ""
    languagesystem = ""
    contextContent = ""
    listScript = []
    scripts = []
    featuresTable = []
    gposFeatures = ""
    chainedContent = ""
    # lookups = {}
    ### SPLIT THE CONTENT IN LOOKUPS ###
    for i in monotypeFeaturesTxt:
        if "lookup" in i and "lookup end" not in i:
            j = monotypeFeaturesTxt.index(i) + 1
            while "lookup end" not in monotypeFeaturesTxt[j]:
                lookupContent.append(monotypeFeaturesTxt[j][:-1])
                j += 1
            lookupName = i.replace("\t", "_")
            lookupName = lookupName.replace("lookup", "gpos")
            cleaning = [x for x in lookupContent if x != '']
            lookupContent = []
            ### ADD (NAME OF LOOKUP + CONTENT) AS TUPLE IN A LIST SO THE LOOP WILL FOLLOW THE ORDER, DICT is USELESS HERE
            namesAndContentsLookup.append(([lookupName[:-1]], cleaning))
        elif "feature table begin" in i and "feature table end" not in i:
            x = monotypeFeaturesTxt.index(i) + 1
            while "feature table end" not in monotypeFeaturesTxt[x]:
                featuresTable.append(monotypeFeaturesTxt[x][:-1])
                x += 1
            cleaning = [x for x in featuresTable if x != '']
            featuresTable = cleaning
        elif "script table begin" in i and "script table end" not in i:
            x = monotypeFeaturesTxt.index(i) + 1
            while "script table end" not in monotypeFeaturesTxt[x]:
                dflt = monotypeFeaturesTxt[x].replace("default", "dflt")
                scripts.append(dflt[:-1])
                x += 1
            cleande_scripts = [x for x in scripts if x != '']
            scripts = cleande_scripts

    for i in scripts:
        isplit = i.split("\t")
        listScript.append(isplit)
        languagesystem += "languagesystem " + isplit[0] + " " + isplit[1] + ";\n"
    languagesystem += "\n"

    #### REFORMAT THE CONTENT TO WRITE FEATURE FILE ACCORDING TO THE ADOBE SYNTAX
    for i in namesAndContentsLookup:
        name = str(i[0]).replace(" ", "_")
        lookup = i[1]
        content = []
        debut = "lookup " + name[2:-2] + " {\n"
        content_str = ""
        ############################
        ### CURSIV LOOKUP TYPE 3 ###
        ############################
        if "cursiv" in name:
            txt += parseCursive(name, lookup)
        ############################
        ### SINGLE LOOKUP TYPE 1 ###
        ############################
        if "single" in name:
            txt += parseSingleGPOS(name, lookup)
        ############################
        ### SINGLE LOOKUP TYPE 1 ###
        ############################
        if "pair" in name or "kernset" in name:
            txt += parseKernsetGPOS(name, lookup)
        #############################
        ### CONTEXT LOOKUP TYPE 7 ###
        #############################
        elif "context" in name:
            contextContent += parseContextGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos")
        ###############################
        ### Mark2Base LOOKUP TYPE 4 ###
        ###############################
        elif "mark_to_base" in name:
            txt += parseMark2base(name, lookup)
        ###############################
        ### Mark2Liga LOOKUP TYPE 5 ###
        ###############################
        elif "mark_to_ligature" in name:
            txt += parseMark2Ligature(name, lookup)
        ###############################
        ### Mark2Mark LOOKUP TYPE 6 ###
        ###############################
        elif "mark_to_mark" in name:
            txt += parseMark2Mark(name, lookup)
        ###############################
        ### CHAINED LOOKUP TYPE 8 ###
        ###############################
        elif "chained" in name:
            chainedContent += parseChainedGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos")

        #add context at the end
    txt += contextContent + chainedContent

    # FIX Store All list of features and involved lookup by languagesystem
    # in a dict to avoid duplicate. ut MTI files have duplicate. It should be corrected at some point
    gposFeaDict = dict()
    for i in featuresTable:
        isplit = i.split("\t")
        if isplit[1] not in gposFeaDict:
            gposFeaDict[isplit[1]] = [{isplit[0]: isplit[2]}]
        else:
            itemz = []
            for z in gposFeaDict[isplit[1]]:
                itemz.append(z)
            itemz.append({isplit[0]: isplit[2]})
            gposFeaDict[isplit[1]] = itemz
    # print(gposFeaDict)
    for feature in gposFeaDict:
        gposFeatures += "feature " + feature + " {\n"
        for script in gposFeaDict[feature]:
            for k,v in script.items():
                # print(k, v)
                for s in listScript:
                    if k in s[3]:
                        gposFeatures += "script " + s[0] + " ;\n\t" + "language " + s[1] + " ;\n"
                        for lkup in v.split(","):
                            gposFeatures += "\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + ";\n"
        gposFeatures += "\t\t} " + feature + ";\n\n"

    return txt, languagesystem, gposFeatures

def readGDEF(classGdef, rdir):
    namesAndContentsLookup = list()
    lookupContent = list()
    txt = ""
    #initialize variable
    grpBase, grpLigature, grpMark, grpCompo, caret, attach, groups_txt, MarkAttachmentClass = "", "", "", "", "", "", "", ""
    AGdefClass = []
    allGDEF = {}
    GDEF_base, GDEF_ligature, GDEF_mark, GDEF_compo = [], [], [], []
    filterSets, filter_groups_txt = "", ""


    # detect the beginning and the end of classes and put each in a list, then put lists in dict
    for i in classGdef:
        if "begin" in i:
            j = classGdef.index(i) + 1
            while "end" not in classGdef[j]:
                AGdefClass.append(classGdef[j][:-1])
                j += 1
            GdefClassName = i.replace("\t", "_")
            cleanedList = [x for x in AGdefClass if x != '']
            allGDEF[GdefClassName[:-1]] = cleanedList
            AGdefClass = []
    # print(allGDEF)
    #loop on the first class, the one with no precision, that is the GlyphClassDef one. It may contains up to 4 groups
    for i in allGDEF["class definition begin"]:
        if str(i[-1:]) == "1":
            glyph = i.split("\t")
            GDEF_base.append(glyph[0])

        if str(i[-1:]) == "2":
            glyph = i.split("\t")
            GDEF_ligature.append(glyph[0])

        if str(i[-1:]) == "3":
            glyph = i.split("\t")
            GDEF_mark.append(glyph[0])

        if str(i[-1:]) == "4":
            glyph = i.split("\t")
            GDEF_compo.append(glyph[0])

    for i in GDEF_base:
        grpBase += i + " "

    for i in GDEF_ligature:
        grpLigature += i + " "

    for i in GDEF_mark:
        grpMark += i + " "

    for i in GDEF_compo:
        grpCompo += i + " "

    ### FILL A DICT WITH CONTENT OF EACH GROUPS
    GlyphClassDefDict = {"@GDEF_base = [" : grpBase, "@GDEF_ligature = [" : grpLigature, "@GDEF_mark = [" : grpMark, "@GDEF_compo = [" : grpCompo}

    #loop in the LigatureCaretList
    if "carets begin" in allGDEF:
        for i in allGDEF["carets begin"]:
            e = i.split("\t")
            del e[1]
            caret += "\t\tLigatureCaretByPos " + str(" ".join(e)) + " ;\n"
        # print(caret)

    #loop in the AttachmentList
    if "attachment list begin" in allGDEF:
        for i in allGDEF["attachment list begin"]:
            f = i.split("\t")
            attach += "\t\tAttach " + str(" ".join(f)) + " ;\n"

    ### loop in the MarkAttachmentClass.
    if "mark attachment class definition begin" in allGDEF:
        MarkAttachmentClassList = list()
        MarkAttachmentClassList = allGDEF["mark attachment class definition begin"]
        MarkAttachmentClassList.insert(0, "mark attachment class definition begin")
        MarkAttachmentClassList.append("class definition end")
        MarkAttachmentClass = getGroupsAsDict(MarkAttachmentClassList, start = "mark attachment class definition begin")
        MarkAttachmentClass = unpackGroupsFromDict(MarkAttachmentClass, "", namingConvention = "\t@_MarkAttachmentType_")

    if "markfilter set definition begin" in allGDEF:
        filterList = []
        filterList = allGDEF["markfilter set definition begin"]
        filterList.insert(0, "markfilter set definition begin")
        filterList.append("class definition end")
        filterSets = getGroupsAsDict(filterList, start = "markfilter set definition begin")
        filterSets = unpackGroupsFromDict(filterSets, "", namingConvention = "\t@_FilterSet_")

    ### LOOP IN THE DICT OF GLYPHSCLASSDEF to make sure groups are filled, if not then no add it in feature file
    for i in GlyphClassDefDict:
        if len(GlyphClassDefDict[i]) != 0:
            groups_txt += str(i) + GlyphClassDefDict[i] + "];\n"

    if len(MarkAttachmentClass) > 0:
        # txt += "\nMarkAttachClassDef\n" + MarkAttachmentClass
        groups_txt += MarkAttachmentClass + "\n"

    if len(filterSets) > 0:
        filter_groups_txt += filterSets + "\n"


    ### LOOP IN THE DICT OF GLYPHSCLASSDEF to make sure groups are filled,
    ### if not then no list it in GLYPHSCLASSDEF

    txt += "\ntable GDEF {\n  GlyphClassDef\n\t\t"
    for i in GlyphClassDefDict:
        if len(GlyphClassDefDict[i]) != 0 and i != "@GDEF_compo = [":
            txt += str(i[:-4]) + ",\n\t\t"
        elif len(GlyphClassDefDict[i]) == 0 and i != "@GDEF_compo = [":
            txt += ",\n\t\t"
        elif i == "@GDEF_compo = [":
            if len(GlyphClassDefDict[i]) != 0:
                txt += str(i[:-4]) + ";\n"
            else:
                txt += ";\n"

    ### ADD CARET LIST IF IT EXISTS
    if len(caret) > 0:
        txt += "\n" + caret
    ### ADD MARK ATTACHEMENT LIST IF IT EXISTS
    if len(attach) > 0:
        txt += "\n" + attach

    txt += "\n} GDEF;"
    return txt, groups_txt, filter_groups_txt

def readGSUB(monotypeFeaturesTxt):
    namesAndContentsLookup = list()
    lookupContent = list()
    txt = ""
    languagesystem = ""
    chainedContent = ""
    contextContent = ""
    scripts = []
    featuresTable = []
    gsubFeatures = ""
    full_issues = []
    # lookups = {}
    ### SPLIT THE CONTENT IN LOOKUPS ###
    for i in monotypeFeaturesTxt:
        if "lookup" in i and "lookup end" not in i:
            j = monotypeFeaturesTxt.index(i) + 1
            while "lookup end" not in monotypeFeaturesTxt[j]:
                lookupContent.append(monotypeFeaturesTxt[j][:-1])
                j += 1
            lookupName = i.replace("\t", "_")
            lookupName = lookupName.replace("lookup", "gsub")
            cleaning = [x for x in lookupContent if x != '']
            lookupContent = []
            ### ADD (NAME OF LOOKUP + CONTENT) AS TUPLE IN A LIST SO THE LOOP WILL FOLLOW THE ORDER, DICT is USELESS HERE
            namesAndContentsLookup.append(([lookupName[:-1]], cleaning))
        elif "feature table begin" in i and "feature table end" not in i:
            x = monotypeFeaturesTxt.index(i) + 1
            while "feature table end" not in monotypeFeaturesTxt[x]:
                featuresTable.append(monotypeFeaturesTxt[x][:-1])
                x += 1
            cleaning = [x for x in featuresTable if x != '']
            featuresTable = cleaning
        elif "script table begin" in i and "script table end" not in i:
            x = monotypeFeaturesTxt.index(i) + 1
            while "script table end" not in monotypeFeaturesTxt[x]:
                dflt = monotypeFeaturesTxt[x].replace("default", "dflt")
                scripts.append(dflt[:-1])
                x += 1
            cleaning = [x for x in scripts if x != '']
            scripts = cleaning

    listScript = []
    for i in scripts:
        isplit = i.split("\t")
        listScript.append(isplit)
        languagesystem += "languagesystem " + isplit[0] + " " + isplit[1] + ";\n"
    languagesystem += "\n"

    #### REFORMAT THE CONTENT TO WRITE FEATURE FILE ACCORDING TO THE ADOBE SYNTAX
    for i in namesAndContentsLookup:
        name = str(i[0]).replace(" ", "_")
        lookup = i[1]
        content = []
        debut = "lookup " + name[2:-2] + " {\n"
        content_str = ""

        ############################
        ### SINGLE LOOKUP TYPE 1 ###
        ############################
        if "single" in name:
            txt += parseSingleGSUB(name, lookup)
        ##############################
        ### MULTIPLE LOOKUP TYPE 2 ###
        ##############################
        elif "multiple" in name:
            ### some lookup tagged as "multiple" have single substitution
            ### syntaxt embed in them, even if it's forbidden in FDK syntax.
            ### so they need to be separate in another lookup,
            ### and if the lookup is called in feature or in a lookup,
            ### the lines need to be copy/past with the separate lookup.
            lookup_multiple, issues = parseMultipleGSUB(name, lookup)
            txt += lookup_multiple
            if len(issues) != 0:
                issues_str = ""
                for issue in issues:
                    issues_str += issue + " "
                    if issue not in full_issues:
                        full_issues.append(issue)
                print("Mixed substitution lookup type in " + issues_str)
        ###############################
        ### ALTERNATE LOOKUP TYPE 3 ###
        ###############################
        if "alternate" in name:
            print("alternate gsub to do")
        #   txt += parseAlternateGSUB(name, lookup)
        ##############################
        ### LIGATURE LOOKUP TYPE 4 ###
        ##############################
        elif "ligature" in name:
            txt += parseLigatureGSUB(name, lookup)
        #############################
        ### CONTEXT LOOKUP TYPE 5 ###
        #############################
        elif "context" in name:
            contextContent += parseContextGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "sub")
            # print(contextContent)
        #############################
        ### CHAINED LOOKUP TYPE 6 ###
        #############################
        elif "chained" in name:
            chainedContent += parseChainedGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "sub")
        #############################
        ### CONTEXT LOOKUP TYPE 8 ###
        #############################
        elif "reversechained" in name:
            print("reversechained to do")
            # contextContent += parseReversechainedGPOS(name, lookup, namesAndContentsLookup)
    txt += contextContent + chainedContent

    ### FIXED
    gsubFeaDict = dict()
    for i in featuresTable:
        isplit = i.split("\t")
        if isplit[1] not in gsubFeaDict:
            gsubFeaDict[isplit[1]] = [{isplit[0]: isplit[2]}]
        else:
            itemz = []
            for z in gsubFeaDict[isplit[1]]:
                itemz.append(z)
            itemz.append({isplit[0]: isplit[2]})
            gsubFeaDict[isplit[1]] = itemz
    for feature in gsubFeaDict:
        gsubFeatures += "feature " + feature + " {\n"
        content = gsubFeaDict[feature]
        for script in gsubFeaDict[feature]:
            for k,v in script.items():
                # print(k, v)
                for s in listScript:
                    if k in s[3]:
                        gsubFeatures += "script " + s[0] + " ;\n\t" + "language " + s[1] + " ;\n"
                        for lkup in v.split(","):
                            gsubFeatures += "\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + ";\n"
                            if "multiple" in str(namesAndContentsLookup[int(lkup)][0]):
                                if len(full_issues)!=0:
                                    print (full_issues, str(namesAndContentsLookup[int(lkup)][0][0]))
                                    if str(namesAndContentsLookup[int(lkup)][0][0]) in full_issues:
                                        print("add the alt lookup")
                                        gsubFeatures += "\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + "_alt_single;\n"
        gsubFeatures += "\t\t} " + feature + ";\n\n"

    return txt, languagesystem, gsubFeatures

def getGTXT(Gpath):
    with open(Gpath, "r") as G___:
        G___content = G___.readlines()

    return G___content

def mti2fea(family):
    # VARIABLES
    repo = "../src/" + family + "/"
    rdir = os.path.abspath(repo)

    # get mti_features_txt list for each master
    features_by_masters = dict()
    plist_path = [rdir + "/" + i for i in os.listdir(rdir) if i.endswith(".plist")]
    with open(plist_path[0], "rb") as plist:
        gsub_gpos_gdef_2_masters = readPlist(plist)
        for master in gsub_gpos_gdef_2_masters:
            l =[]
            for j in gsub_gpos_gdef_2_masters[master]:
                l.append(gsub_gpos_gdef_2_masters[master][j])
            features_by_masters[master] = l

    # for each master, create a feature file, with its 3 mti files (GPOS, GDEF, GSUB)
    for m in features_by_masters:
        ufoPath = os.path.join(repo, m+".ufo")
        ft = defcon.Font(ufoPath)
        mtiFeatures = []
        # print(m)
        for G___ in features_by_masters[m]:
            Gpath = os.path.join(rdir, G___)
            mtiFeatures.append(Gpath)

        featureTxt = ""
        languagesystem = ""
        gposTxt = ""
        groups_txt = ""
        gdefTxt = ""
        gsubFeatures = ""
        gposFeatures = ""
        gsubTxt = ""
        filter_grps_txt = ""

        # TODO : compare the "languagesystem" tagged in GSUB and GPOS in cas they are not the same… ?
        for table in mtiFeatures:
            if "GPOS" in table:
                monotypeFeaturesTxt = getGTXT(table)
                gposTxt, languagesystem, gposFeatures = readGPOS(monotypeFeaturesTxt, rdir)

        ### DEAL WITH THE GDEF TABLE ###
            elif "GDEF" in table:
                classGdef = getGTXT(table)
                gdefTxt, groups_txt, filter_grps_txt = readGDEF(classGdef, rdir)
                featureTxt = groups_txt + filter_grps_txt + featureTxt + gdefTxt

        ### DEAL WITH THE GSUB TABLE ###
            elif "GSUB" in table:
                monotypeFeaturesTxt = getGTXT(table)
                gsubTxt, languagesystem, gsubFeatures = readGSUB(monotypeFeaturesTxt)
                if "DUMM" in gsubFeatures:
                    gsubTxt = "#NO GSUB RULES\n"
                    gsubFeatures = ""

        featureTxt = languagesystem + groups_txt + filter_grps_txt + "\n#GSUB\n" + gsubTxt   \
                        + "\n#GPOS\n" + gposTxt + "\n#FEATURES LIST\n" + gsubFeatures + gposFeatures + "\n#GDEF\n" + gdefTxt
        # featureTxt = gsubFeatures

        with open(rdir + "/" + m + "_features.fea", "w+") as fea:
            fea.write(featureTxt)
        # ft.features.text = "include(" + m + "_features.fea);"
        ft.features.text = "# Features for " + m + "\n# generated by translating original MTI data\n" + featureTxt
        ft.save()



if __name__ == "__main__":
    fea_ = mti2fea("NotoSansPahawhHmong")