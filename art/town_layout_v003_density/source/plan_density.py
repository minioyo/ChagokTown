"""Author-directed, deterministic packing of unchanged v002 A building instances."""
import json,math,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'town_layout_v002_concepts'
for folder in ('reports','renders','blend'):(ROOT/folder).mkdir(exist_ok=True)
old=json.loads((OLD/'source/layouts.json').read_text())['A']['buildings']
report=json.loads((OLD/'reports/composition_checks.json').read_text())
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
    pp=sorted(set(tuple(p) for p in points));lo=[];hi=[]
    for p in pp:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pp):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2
def yaw(b):
    if 'yaw' in b:return math.radians(b['yaw'])
    x,y=b['xy'];tx,ty=b['toward'];return math.atan2(tx-x,-(ty-y))
LOCAL={}
for data in report['concepts'].values():
    for b in data['buildings']:
        if b['kind'] in LOCAL:continue
        a=yaw(b);s=b['scale'];x,y=b['xy'];points=data['maximum_stage_xy_hulls'][b['id']]
        LOCAL[b['kind']]=hull([((px-x)*math.cos(a)/s+(py-y)*math.sin(a)/s,-(px-x)*math.sin(a)/s+(py-y)*math.cos(a)/s) for px,py in points])
def footprint(b):
    a=yaw(b);s=b['scale'];x,y=b['xy']
    return [(x+s*(px*math.cos(a)-py*math.sin(a)),y+s*(px*math.sin(a)+py*math.cos(a))) for px,py in LOCAL[b['kind']]]
def separation(a,b):
    gap=-1e10
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx=q[0]-p[0];dy=q[1]-p[1];ll=math.hypot(dx,dy);axis=(-dy/ll,dx/ll)
            aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
            gap=max(gap,min(aa)-max(bb),min(bb)-max(aa))
    return gap
def legal(b,placed,clearance=.055):
    fp=footprint(b)
    return all(separation(fp,footprint(o))>=clearance for o in placed)
offsets=sorted(((ix*.10,iy*.10) for ix in range(-22,23) for iy in range(-22,23)),key=lambda p:(p[0]**2+p[1]**2,p[1],p[0]))
def place(b,target,placed):
    for dx,dy in offsets:
        b['xy']=[round(target[0]+dx,3),round(target[1]+dy,3)]
        if legal(b,placed):return dict(b)
    raise AssertionError('No collision-free position near authored target: '+b['id'])
BY_ID={b['id']:b for b in old}
# Three shop edges of one small shared court, upper residential lane, lower work alley.
authored=[('bakery',(-.3,2.9),0),('cafe',(-3.9,.45),76),('florist',(3.35,.35),-93),
          ('home',(-3.25,5.8),28),('bookshop',(1.1,6.8),-38),('upper_cottage',(-6.35,5.9),77),
          ('workshop',(-5.7,-2.85),88),('lane_cottage',(.55,-2.5),-165)]
compact=[]
for key,target,angle in authored:
    b=dict(BY_ID[key]);b['yaw']=angle;b.pop('toward',None);b['source_id']=key
    compact.append(place(b,target,compact))
# Modest coordinate descent closes remaining grass gaps, without moving the fixed court anchor.
def objective(bb):
    aa=area(hull([b['xy'] for b in bb]))
    return aa+sum(.08*((b['xy'][0]+.6)**2+(b['xy'][1]-2.0)**2) for b in bb)
for iteration in range(16):
    changed=False
    for i,b in enumerate(compact):
        if b['id']=='bakery':continue
        others=compact[:i]+compact[i+1:];best=b;best_score=objective(compact)
        for dx,dy in ((.10,0),(-.10,0),(0,.10),(0,-.10),(.1,.1),(.1,-.1),(-.1,.1),(-.1,-.1)):
            c=dict(b);c['xy']=[round(b['xy'][0]+dx,3),round(b['xy'][1]+dy,3)]
            # Respect the authored neighborhood role and shared court access.
            anchor=next(t for key,t,a in authored if key==b['id'])
            if math.dist(c['xy'],anchor)>2.5:continue
            if not legal(c,others):continue
            trial=compact[:i]+[c]+compact[i+1:];score=objective(trial)
            if score<best_score-1e-6:best,best_score=c,score
        if best is not b:compact[i]=best;changed=True
    if not changed:break
dense=[dict(b) for b in compact]
# These are infill/background copies, not additions to the game's catalog or economy.
infill=[('infill_west','house',1,.46,(-6.65,2.45),82,0.0),
        ('infill_court','florist',1,.50,(2.25,-2.2),-150,0.0),
        ('infill_upper','house',3,.50,(-.8,7.6),-8,1.65),
        ('infill_back','house',2,.50,(-4.7,7.4),-120,1.65),
        ('infill_east','cafe',1,.48,(2.25,3.65),-92,0.0),
        ('infill_work','house',1,.50,(-6.5,-.6),100,0.0),
        ('infill_lower_west','house',2,.56,(-6.7,-3.9),95,-.45),
        ('infill_lower_east','grocer',1,.58,(4.6,-1.5),-110,0.0)]
for key,kind,level,scale,target,angle,ground in infill:
    b={'id':key,'kind':kind,'level':level,'scale':scale,'ground':ground,'yaw':angle,'source_id':None,'background_only':True}
    dense.append(place(b,target,dense))
scenes={'Baseline':old,'Compact':compact,'Dense':dense}
metrics={}
for name,buildings in scenes.items():
    pairs=[{'a':a['id'],'b':b['id'],'gap_m':round(separation(footprint(a),footprint(b)),5)} for a,b in itertools.combinations(buildings,2)]
    assert all(p['gap_m']>=-.0002 for p in pairs)
    aa=area(hull([b['xy'] for b in buildings]))
    footprints=[footprint(b) for b in buildings]
    envelope_area=area(hull([p for fp in footprints for p in fp]));occupied_area=sum(area(fp) for fp in footprints)
    xs=[b['xy'][0] for b in buildings];ys=[b['xy'][1] for b in buildings]
    metrics[name]={'instances':len(buildings),'center_convex_hull_area_m2':round(aa,3),
                   'instances_per_100_m2':round(100*len(buildings)/aa,3),
                   'center_aabb_area_m2':round((max(xs)-min(xs))*(max(ys)-min(ys)),3),
                   'max_stage_hull_sum_area_m2':round(occupied_area,3),'max_stage_cluster_hull_area_m2':round(envelope_area,3),
                   'max_stage_xy_coverage_percent':round(100*occupied_area/envelope_area,2),
                   'max_stage_pairs':pairs,'minimum_separating_axis_gap_m':min(p['gap_m'] for p in pairs)}
(ROOT/'source/layouts.json').write_text(json.dumps(scenes,indent=2),encoding='utf-8')
(ROOT/'reports/placement_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
(ROOT/'source/max_stage_local_hulls.json').write_text(json.dumps(LOCAL,indent=2),encoding='utf-8')
for name,m in metrics.items():print(name,json.dumps({k:v for k,v in m.items() if k!='max_stage_pairs'}))
for b in compact:print('COMPACT',b['id'],b['xy'],b['yaw'])
for b in dense[len(compact):]:print('INFILL',b['id'],b['xy'],b['yaw'])
