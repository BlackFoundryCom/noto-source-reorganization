from vanilla.dialogs import getFile

# help(getFile)
paths = getFile(allowsMultipleSelection=True)
# print(paths)

for path in paths:
    f = OpenFont(path, showUI = False)
# f = CurrentFont()

    for k, v in f.groups.items():
        for i, n in enumerate(v):
            if n not in f.keys():
                print(len(v), k, i, n)
                vlist = list(v)
                vlist.pop(i)
                v = tuple(vlist)

    kernings = f.kerning.keys()
    for i, k in enumerate(kernings):
        n1, n2 = k
        for n in [n1, n2]:
            if n.startswith("@"): continue
            if n not in f.keys():
                try:
                    f.kerning.remove(k)
                    print(k)
                except Exception as e:
                    print(e)
                    
    f.save()
    f.close()
    
print("done")