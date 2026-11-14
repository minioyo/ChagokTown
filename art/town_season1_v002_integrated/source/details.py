"""A few reused edge trees and a short upper-court stair; massing was reviewed bare."""
import bpy,math,json
from mathutils import Vector
import town as T
import geometry as G

def add(scene,before,layout,local,height):
    trunks=sorted([o for o in before.objects if o.type=='MESH' and o.name.startswith('Tree • warm trunk')],key=lambda o:o.name)
    trees=[o for o in before.objects if o.type=='MESH' and o.name.startswith('Tree •')]
    groups={t:[o for o in trees if min(trunks,key=lambda t:math.dist(o.location[:2],t.location[:2]))==t] for t in trunks}
    targets=[(-17,8),(-14,11),(-10.8,13),(-4.8,16.8),(3.8,17.1),(12,13.5),(12.8,5.5),(-14,-7.8)]
    placed=[];skipped=[]
    for (trunk,parts),target in zip(groups.items(),targets):
        points=[o.matrix_world@Vector(c) for o in parts for c in o.bound_box];bottom=min(p.z for p in points)
        delta=Vector((target[0]-trunk.location.x,target[1]-trunk.location.y,height(*target)-bottom))
        poly=T.hull([(p.x+delta.x,p.y+delta.y) for p in points])
        if any(T.separation(poly,T.footprint(b,local))<=.35 for b in layout):
            skipped.append(target);continue
        for o in parts:
            new=o.copy();new.name='REUSED • '+o.name;G.COL.objects.link(new);new.location+=delta
        placed.append({'source_trunk':trunk.name,'xy':target,'scale_preserved':True})
    # Three ordinary shallow stone treads where the shared lane climbs to the forecourt.
    for i in range(3):
        y=5.43+i*.27;x=.35;top=height(x,y+.135)+.035;bottom=min(height(x,y-.135),height(x,y+.135))-.025
        G.box('Upper court • shallow stair tread',(x,y,(top+bottom)/2),(.80,.28,top-bottom),'Stone light',.008)
    (T.ROOT/'reports/environment.json').write_text(json.dumps({'previous_tree_groups':len(trunks),'reused_tree_groups':len(placed),'new_tree_groups':0,'edge_trees':placed,'omitted_near_buildings':skipped,'new_houses':0,'upper_court_treads':3},indent=2),encoding='utf-8')
