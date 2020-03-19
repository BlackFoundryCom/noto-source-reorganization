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
        if "MarkFilterType" not in j and "MarkAttachmentType" not in j:
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
    print(name)
    single_txt = ""
    single_txt += "lookup " + name[2:-2] + " {\n"
    gpos_single_dico = dict()
    if len(parseLookupflag(lookup[0:6])) != 0:
        single_txt += parseLookupflag(lookup[0:6])
    for j in lookup[4:]:
        if "MarkFilterType" not in j and "MarkAttachmentType" not in j:
            j_list = j.split("\t")
            if j_list[1] in gpos_single_dico:
                gpos_single_dico[j_list[1]] = gpos_single_dico[j_list[1]].append({j_list[0]:j_list[2]})
            else:
                gpos_single_dico[j_list[1]] = [{j_list[0]:j_list[2]}]
            if "x advance" in j_list[0]:
                single_txt += "\tposition " + j_list[1] + " < 0 0 " +  j_list[2] + " 0 >;\n"
            elif "y advance" in j_list[0]:
                single_txt += "\tposition " + j_list[1] + " < 0 0 0 " +  j_list[2] + " >;\n"
            elif "x placement" in j_list[0]:
                single_txt += "\tposition " + j_list[1] + " < " + j_list[2] + " 0 0 0 >;\n"
            elif "y placement" in j_list[0]:
                single_txt += "\tposition " + j_list[1] + " < 0 " + j_list[2] + " 0 0 >;\n"
    single_txt += "    } " + name[2:-2] + " ;\n\n"
    # print(gpos_single_dico)
    # print(name)
    # print(gpos_single_dico)
    for i in gpos_single_dico:
        # print(i)
        xadv, xplace, yadv, yplace = "0", "0", "0", "0"
        # print(gpos_single_dico[i])
        for d in gpos_single_dico[i]:
            # print(d)
            if "x advance" in d:
                xadv = d["x advance"]
        print("    pos " + i + " < " + xplace + " " + yplace + " " + xadv + " " + yplace + " >;\n")
    print("\n\n")
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
    if "firstclass definition begin" in contenu:
        for i in contenu:
            if "firstclass definition begin" in i:
                classList = []
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
                classList = []
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
            rules += "\tmarkClass " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + "> @_MARKCLASS_" + \
            str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
        elif "base" in ligne:
            rules += "\tposition mark " + ligneSplit[1] + " <anchor " + ligneSplit[3].replace(",", " ") + \
            "> mark @_MARKCLASS_" + str(ligneSplit[2]) + "_lookup_" + name.split('_')[1] + ";\n"
    m2m_txt = m2m_txt + rules + "    } " + name[2:-2] + " ;\n\n"
    return m2m_txt


##########################
#### GPOS LookupType 7 ###
##########################
"""
 stored => first create groups by listing glyphs and tagged them with a number. Same number = same group
            then define context (ligns with "class definition begin" at the beginning)
            the context is written betwen firsst and second tabulation. It is written by the number of the group
            After second tab the couple of 2 number are indicating 1) wich group of the context is impacted,
            and 2) which lookup of the GPOS table is called to impact it.
            The Coverage context is another story not made yet => TODO
 output => first make the groups, then write "position" and th succesion of group creating the context
            then check which element of the contect is impacted, add a ' (quotesingle) after the group and the name of the lookup
            each element of the contect can receive a lookuup.
"""
def parseContextGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos"):
    keyword = "\n\t"+keyword
    clazz = ""
    class_cntxt = ""
    grp_ = dict()
    contextGsubGpos_txt = ""
    if len(parseLookupflag(lookup[0:6])) != 0:
        contextGsubGpos_txt += parseLookupflag(lookup[0:6])
    # GET THE CONTENT OF THE LOOKUP, IF GROUPS ARE DEFINED, GET THEM #
    contenu = [x for x in lookup if x != '']
    for e in contenu[4:]:
        if "MarkFilterType" not in e and "MarkAttachmentType" not in e:
            rule = e.split("\t")
            #if len(rule) == 3:
            if rule[0] == "class":
                class_cntxt = ""
                for i in rule[1].split(","):
                    class_cntxt += "@_group_" + i.strip() + "_" + name[2:-2] + "' "
                class_cntxt_list = class_cntxt.split(" ")
                for r in rule[2:]:
                    element_impacted = int(r.split(",")[0])-1
                    numeroLookup = r.split(",")[1].strip(" ")
                    lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
                    class_cntxt_list[element_impacted] = class_cntxt_list[element_impacted] + " lookup " + lookup_name
                # print(" ".join(class_cntxt_list))
                contextGsubGpos_txt += keyword + " " + " ".join(class_cntxt_list) + ";"
            elif rule[0] == "glyph":
                glif_sequence = list()
                for i in rule[1].split(","):
                    glif_sequence.append(i.strip())
                # print(name, rule[2:])
                numeroLookup = rule[2].split(",")[1].strip(" ")
                lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
                sequence_list = rule[1].split(",")
                sequence_list_quote = []
                for i in sequence_list:
                    sequence_list_quote.append(i + "'")
                for r in rule[2:]:
                    element_impacted = int(r.split(",")[0])-1
                    numeroLookup = r.split(",")[1].strip(" ")
                    lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
                    sequence_list_quote[element_impacted] = sequence_list_quote[element_impacted] + " lookup " + lookup_name
                sequence = "".join(sequence_list_quote)
                # print(sequence)
                contextGsubGpos_txt += keyword + " " + sequence + ";"
            else:
                if "class definition begin" in e:
                    grp_ = getGroupsAsDict(contenu)
                    for g in grp_:
                        cont = " ".join(grp_[g])
                        clazz += "\t@_group_" + g + "_" + name[2:-2] + " = [ " + cont + " ];\n"
    # contextGsubGpos_txt +=  "\n    } " + name[2:-2] + " ;\n\n"
    contextGsubGpos_txt = "lookup " + name[2:-2] + " {\n" + clazz \
        + contextGsubGpos_txt + "\n    } " + name[2:-2] + " ;\n\n"
    # print(contextGsubGpos_txt)
    return str(contextGsubGpos_txt)

##########################
#### GPOS LookupType 8 ###
##########################
"""
    This kind of lookup applies one or more lookup on some letters,
    when a specific context is found. The modified sequence can be preceded
    by backtrack glyphs or classes that are not modified, and/or followed
    by lookahaed classes or glyphs that are not modied either.
    The lookups called should be declared before this one, but this one should be right after
    the lookups it calls, because other substitution or positionning
    can be applied on the shaping resulting from this lookup.
    Only one lookup per glyph or class is allowed in OpenType, but more than one
    in mti files. So if this syntax is found, one needs to creates a new lookup that
    does what the 2 or more lookups called are doing in 2 or more steps.
    When applied pn different glyphs por class of the modified sequence,
    there is no issue.
    The mti files use the keyword "glyphs" and "class-chained" to precise
    the nature of the contentn of the modified sequence.
    Classes are defined before the rules with "backtrackclass," "class" and
    "lookaheadclass" keywords.
"""
def parseChainedGPOSGSUB(name, lookup, namesAndContentsLookup, keyword = "pos"):
    number_of_subtable = 0
    chainedPOS_txt = ""
    rule = ""
    txt_added = ""
    # GET THE NAME AND THE LOOKUPFLAGS IF NEEDED
    chainedPOS_txt += "lookup " + name[2:-2] + " {\n"
    if len(parseLookupflag(lookup[0:6])) != 0:
        chainedPOS_txt += parseLookupflag(lookup[0:6])
    # GET THE CONTENT OF THE LOOKUP, IF GROUPS ARE DEFINED, GET THEM
    contenu = [x for x in lookup if x != '']
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
        for i in contenu:
            if i == "class definition begin":
                classList.append("class definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        inputclass = getGroupsAsDict(classList)
        refactoredGroups = unpackGroupsFromDict(inputclass, name[2:-2], namingConvention = "\t@_impacted_group_")
        chainedPOS_txt += refactoredGroups + "\n"
    if "lookaheadclass definition begin" in contenu:
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
        # print(refactoredGroups)
        chainedPOS_txt += refactoredGroups + "\n"
    # COVERAGE
    backtrackcoverage, inputcoverage, lookaheadcoverage, coverage = "", "", "", ""
    if "backtrackcoverage definition begin" in contenu:
        for i in contenu:
            if "backtrackcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    coverage += contenu[j] + " "
                    j += 1
                coverage += "]"
        backtrackcoverage = coverage
        coverage = ""
    if "inputcoverage definition begin" in contenu:
        for i in contenu:
            if "inputcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    # classList.append(contenu[j])
                    coverage += contenu[j] + " "
                    j += 1
                coverage += "]"
        inputcoverage = coverage
        # print(inputcoverage)
        coverage = ""
    if "lookaheadcoverage definition begin" in contenu:
        for i in contenu:
            if "lookaheadcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    coverage += contenu[j] + " "
                    j += 1
                coverage += "]"
        lookaheadcoverage = coverage
        # print("lookahead", name, lookaheadcoveragecoverage)
        coverage = ""
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
            # print(name, _lookup_called)
            rule += "    " + keyword + " "
            input_rule = []
            lookahead_in_rule = ""
            if _backtrack_group[0] != "":
                for x in _backtrack_group:
                    x = x.replace(" ", "")
                    rule += "@_backtrack_group_" + x + "_" + name[2:-2] + " "
            for _inpt_grp in _input_groups:
                _inpt_grp = _inpt_grp.replace(" ", "")
                input_rule.append("@_impacted_group_" + _inpt_grp + "_" + name[2:-2]  + "' ")
            for element2lookup in _lookup_called:
                num_lookup = int(element2lookup[1].replace(" ", ""))
                lookup_name = str(namesAndContentsLookup[num_lookup][0])[2:].strip("['']").replace(" ", "_")
                index = int(element2lookup[0])-1
                input_rule[index] = input_rule[index] + "lookup " + lookup_name
            if _lookahead_groups[0] != "":
                for x in _lookahead_groups:
                    x = x.replace(" ", "")
                    lookahead_in_rule += "@_lookahead_group_" + x + "_" + name[2:-2] + " "
            rule += "".join(input_rule) + lookahead_in_rule + ";\n"
            # print(i, "\n", rule)
        elif "coverage\t" in i:
            x = i.split(",")[1]
            lookup_name = str(namesAndContentsLookup[int(x)][0])[2:].strip("['']")
            chainedPOS_txt += "    " + keyword + backtrackcoverage + inputcoverage \
                + "' lookup " + lookup_name + lookaheadcoverage + " ;"
        elif "glyph\t" in i:
            glyphs_impacted = []
            isplit = i.split("\t")
            elements_impacted_andLookup = isplit[4:]
            for g in isplit[2].split(","):
                glyphs_impacted.append(g + "'")
            for element2lookup in elements_impacted_andLookup:
                index = int(element2lookup.split(",")[0])-1
                numeroLookup = element2lookup.split(",")[1]
                lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
                glyphs_impacted[index] = glyphs_impacted[index] + " lookup " + lookup_name
            chainedPOS_txt += "\t" + keyword + " " + isplit[1] + " " + " ".join(glyphs_impacted) + " " + isplit[3] + ";\n"
        elif "subtable end" in i:
            number_of_subtable += 1
            txt_added = GPOSSGUB_chained_subtable(namesAndContentsLookup, contenu[contenu.index(i)+1:], name, str(number_of_subtable), keyword)
            # print(txt_added)
            break
    chainedPOS_txt =  chainedPOS_txt + rule + txt_added + "\n    } " + name[2:-2] + " ;\n\n"
    return chainedPOS_txt

def GPOSSGUB_chained_subtable(namesAndContentsLookup, content, name, num, keyword):
    prefix = "_subtable_" + num
    txt = "\n\tsubtable;\n"
    rule = ""
    contenu = [x for x in content if x != '']
    # for toto in contenu:
    #     print(toto)
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
        refactoredGroups = unpackGroupsFromDict(backtrackclass, name[2:-2], namingConvention = "\t@_backtrack"+prefix+"_group_")
        txt += refactoredGroups + "\n"
    if "class definition begin" in contenu:
        classList = []
        for i in contenu:
            if i == "class definition begin":
                classList.append("class definition begin")
                j = contenu.index(i) + 1
                while "class definition end" not in contenu[j]:
                    classList.append(contenu[j])
                    j += 1
                classList.append("class definition end")
        inputclass = getGroupsAsDict(classList)
        refactoredGroups = unpackGroupsFromDict(inputclass, name[2:-2], namingConvention = "\t@_impacted"+prefix+"_group_")
        txt += refactoredGroups + "\n"
    if "lookaheadclass definition begin" in contenu:
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
        refactoredGroups = unpackGroupsFromDict(lookaheadclass, name[2:-2], namingConvention = "\t@_lookahead"+prefix+"_group_")
        # print(refactoredGroups)
        txt += refactoredGroups + "\n"
    # COVERAGE
    backtrackcoverage, inputcoverage, lookaheadcoverage, coverage = "", "", "", ""
    if "backtrackcoverage definition begin" in contenu:
        for i in contenu:
            if "backtrackcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    coverage += contenu[j] + " "
                    j += 1
                coverage += " ]"
        backtrackcoverage = coverage
        coverage = ""
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
    if "lookaheadcoverage definition begin" in contenu:
        for i in contenu:
            if "lookaheadcoverage definition begin" in i:
                coverage = " [ "
                j = contenu.index(i) + 1
                while "coverage definition end" not in contenu[j]:
                    coverage += contenu[j] + " "
                    # print(coverage)
                    j += 1
                coverage += " ]"
        lookaheadcoverage = coverage
        # print("lookahead>", lookaheadcoverage)
        coverage = ""
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
            # print(name, _lookup_called)
            rule += "    " + keyword + " "
            input_rule = []
            lookahead_in_rule = ""
            if _backtrack_group[0] != "":
                for x in _backtrack_group:
                    x = x.replace(" ", "")
                    rule += "@_backtrack_group_" + x + "_" + name[2:-2] + " "
            for _inpt_grp in _input_groups:
                _inpt_grp = _inpt_grp.replace(" ", "")
                input_rule.append("@_impacted_group_" + _inpt_grp + "_" + name[2:-2]  + "' ")
            for element2lookup in _lookup_called:
                num_lookup = int(element2lookup[1].replace(" ", ""))
                lookup_name = str(namesAndContentsLookup[num_lookup][0])[2:].strip("['']").replace(" ", "_")
                index = int(element2lookup[0])-1
                input_rule[index] = input_rule[index] + "lookup " + lookup_name
            if _lookahead_groups[0] != "":
                for x in _lookahead_groups:
                    x = x.replace(" ", "")
                    lookahead_in_rule += "@_lookahead_group_" + x + "_" + name[2:-2] + " "
            rule += "".join(input_rule) + lookahead_in_rule + ";\n"
            # print(i, "\n", rule)
        elif "coverage\t" in i:
            x = i.split(",")[1]
            lookup_name = str(namesAndContentsLookup[int(x)][0])[2:].strip("['']")
            txt += "    " + keyword + backtrackcoverage + inputcoverage \
                + "' lookup " + lookup_name + lookaheadcoverage + " ;"
        elif "glyph\t" in i:
            glyphs_impacted = []
            isplit = i.split("\t")
            elements_impacted_andLookup = isplit[4:]
            for g in isplit[2].split(","):
                glyphs_impacted.append(g + "'")
            for element2lookup in elements_impacted_andLookup:
                index = int(element2lookup.split(",")[0])-1
                numeroLookup = element2lookup.split(",")[1]
                lookup_name = str(namesAndContentsLookup[int(numeroLookup)][0])[2:].strip("['']")
                glyphs_impacted[index] = glyphs_impacted[index] + " lookup " + lookup_name
            txt += "\t" + keyword + " " + isplit[1] + " " + " ".join(glyphs_impacted) + " " + isplit[3] + ";\n"
        elif i == "subtable end":
            break
    txt =  txt + rule + "\n"
    return txt


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
                if "musc" not in dflt:
                    scripts.append(dflt[:-1])
                x += 1
            cleaned_scripts = [x for x in scripts if x != '']
            scripts = cleaned_scripts

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

    ### PUT FEATURES TAG IN A DICT,
    ### WITH NUMBER_ID AND INVOLVED LOOKUPS AS key, value,
    ### IN A LIST THAT IS THE VALUE OF THE FEATURE
    ### Ex: {ccmp : [{"1" : "2, 3, 4"}, {"2": "3, 6, 8"}]}
    ### THE SCRIPTS LIST WHICH LOOKUPS ARE INVOLVED IN EACH FEATURE TAG
    ### EX: THE ARABIC URDU NEDDS LOOKUPS 2, 3, 4 IN ITS CCMP
    ### WHERE ARABIC FARSI NEEDS A ccmp WITH LOOKUPS 3, 6, 8.
    ### TO INDICATE THIS, EACH SCRIPT TAG PRECISE THE NUMBER_ID OF THE FEATURE TAG
    ### EX : arab URD 1
    ###      arab FAR 2
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
    for feature in gposFeaDict:
        gposFeatures += "feature " + feature + " {\n"
        for index_ in gposFeaDict[feature]:
            for k in index_.keys():
                temp_lookup_involved = ""
                for lkup in index_[k].split(","):
                    temp_lookup_involved += "\t\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + ";\n"
                for s in listScript:
                    test = [nb.strip() for nb in s[3].split(",")]
                    if k in test:
                        gposFeatures += "\tscript " + s[0] + " ;\n\t\t" + "language " + s[1] + " ;\n"
                        gposFeatures += temp_lookup_involved
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
                # remove the "musc" tag from languagesystem declaration
                # because of a fonttools bug
                dflt = monotypeFeaturesTxt[x].replace("default", "dflt")
                if "musc" not in dflt.split("\t")[0]:
                    scripts.append(dflt[:-1])
                x += 1
            cleaning = [x for x in scripts if x != '']
            # print(cleaning)
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
                # print("Mixed substitution lookup type in " + issues_str)
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
    # WRITE THE LOOKUP IN EACH FEATURES WITh THE CORRECT SCRIPTS TAGS
    for feature in gsubFeaDict:
        gsubFeatures += "feature " + feature + " {\n"
        content = gsubFeaDict[feature]
        for index_ in gsubFeaDict[feature]:
            for k in index_.keys():
                temp_lookup_involved = ""
                for lkup in index_[k].split(","):
                    temp_lookup_involved += "\t\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + ";\n"
                    if "multiple" in str(namesAndContentsLookup[int(lkup)][0]):
                        if len(full_issues)!=0:
                            # print (full_issues, str(namesAndContentsLookup[int(lkup)][0][0]))
                            if str(namesAndContentsLookup[int(lkup)][0][0]) in full_issues:
                                # print("add the alt lookup")
                                temp_lookup_involved += "\t\t\tlookup " + str(namesAndContentsLookup[int(lkup)][0]).strip("['']").replace(" ", "_") + "_alt_single;\n"
                for s in listScript:
                    test = [nb.strip() for nb in s[3].split(",")]
                    if k in test:
                        # print("\t", k, s[3])
                        gsubFeatures += "\tscript " + s[0] + " ;\n\t\t" + "language " + s[1] + " ;\n"
                        gsubFeatures += temp_lookup_involved
        gsubFeatures += "\t\t} " + feature + ";\n\n"
    # print(gsubFeatures)

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
        ufoPath = os.path.join(repo, m + ".ufo")
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

        ### DEAL WITH THE GSUB TABLE. IF THERE IS NO RULES A VOID GSUB ###
        ### WITH A FAKE FEATURE CALLED "DUMM" IS DECLARED. IT SHOULDN'T BE ADDED OBVIOUSLY
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



# if __name__ == "__main__":
#     fea_ = mti2fea("NotoSansCham")