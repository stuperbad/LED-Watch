import json,re,sys
d=json.load(open(sys.argv[1])); s=set()
for u in d["unconnected_items"]:
    for i in u["items"]:
        m=re.search(r"\[([^\]]*)\]",i["description"])
        if m and m.group(1): s.add(m.group(1))
pri=["GND","SBU","CC1","CC2","VBUS","/BATT","ISET","TS","+3V3","/UPDI"]
out=[n for n in pri if n in s]+sorted(n for n in s if n not in pri)
print(" ".join(out))
