for k in ("Mor","Che","Cas","NS","Put","Out","Camp","Zast","Yel","V1","V2","V3","V4"):
    print(k, dict(CNT[k]))
print("fills", {k: globals()[k] for k in ("MOR_FILL","CHE_FILL","CAS_FILL","NS_FILL","PUT_KR_FILL","PUT_FILL")})
print("MISSED", MISSED)
print("camp", {k:(len(v) if v else 0) for k,v in CAMP_PLAN.items()})
print("terr", Counter(T).most_common(40))
from collections import Counter as C2
print("heights", sorted(C2(H).items()))

bad=[]
for y in range(S):
    for x in range(S):
        h=H[I(x,y)]
        for dx,dy in NB8:
            xx,yy=x+dx,y+dy
            if 0<=xx<S and 0<=yy<S and abs(H[I(xx,yy)]-h)>1:
                bad.append((x,y,h,H[I(xx,yy)],FIXED[I(x,y)],FIXED[I(xx,yy)])); break
print("BAD", bad[:20])

import os
if os.environ.get("V2_SAVE"):
    sc.write_to_file(str(ROOT/"build"/"_v2_world_test.aoe2scenario"))
print("QSHORT", QSHORT); print("MISSED", MISSED)
bad=[]
for y in range(S):
    for x in range(S):
        h=H[I(x,y)]
        for dx,dy in NB8:
            xx,yy=x+dx,y+dy
            if 0<=xx<S and 0<=yy<S and abs(H[I(xx,yy)]-h)>1: bad.append((x,y,h,H[I(xx,yy)],FIXED[I(x,y)],FIXED[I(xx,yy)])); break
print("BAD2", bad[:10])
ub=[]
for (tx,ty,sz) in REC:
    hs={H[I(tx+a,ty+b)] for a in range(sz) for b in range(sz) if inb(tx+a,ty+b)}
    if len(hs)>1: ub.append((tx,ty,sz,hs))
print("UNFLAT", ub)
