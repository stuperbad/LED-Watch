import json,sys
d=json.load(open(sys.argv[1])); n=0
for v in d["violations"]:
    if v["type"] in("shorting_items","clearance","tracks_crossing","hole_clearance","copper_edge_clearance","via_dangling_x"):
        if v["type"]=="hole_clearance" and any("NPTH" in i["description"] for i in v["items"]): continue
        n+=1
print(n)
