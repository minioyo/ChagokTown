"""Connect the whole village through actual all-stage ground-level geometry."""
import math,heapq,json
from collections import defaultdict
from mathutils import Vector
import town as T
import geometry as G

def inside(p,poly):
    value=False;x,y=p
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:value=not value
    return value

def dist(p,poly):
    if inside(p,poly):return 0
    result=1e10
    for a,b in zip(poly,poly[1:]+poly[:1]):
        dx=b[0]-a[0];dy=b[1]-a[1];ll=dx*dx+dy*dy
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll)) if ll else 0
        result=min(result,math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy))
    return result

def body_polys(col):
    # Weld positional seam duplicates only for finding connected closed components.
    # Keep a conservative XY projection of every component intersecting walking height.
    result=[]
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        me=obj.data;positions={};parent={};points=[];indices=[]
        def find(a):
            while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
            return a
        for v in me.vertices:
            p=obj.matrix_world@v.co;key=tuple(round(c,5) for c in p)
            if key not in positions:positions[key]=len(points);parent[len(points)]=len(points);points.append(tuple(p))
            indices.append(positions[key])
        for face in me.polygons:
            ids=[indices[i] for i in face.vertices];a=find(ids[0])
            for b in ids[1:]:parent[find(b)]=a
        groups=defaultdict(list)
        for i,p in enumerate(points):groups[find(i)].append(p)
        for pp in groups.values():
            if min(p[2] for p in pp)>=1.85 or max(p[2] for p in pp)<=.205:continue
            poly=T.hull([(p[0],p[1]) for p in pp])
            if len(poly)>=3:result.append(poly)
    return result

def make(layout,asset,height,paving):
    kinds={b['kind'] for b in layout};local={(k,n):body_polys(asset(k,n)) for k in kinds for n in (1,2,3)}
    obstacles=[{'plot':b['id'],'level':n,'poly':[T.world_xy(b,p) for p in poly]} for b in layout for n in (1,2,3) for poly in local[b['kind'],n]]
    step=.16;radius=.38;blocked=set();by_plot=defaultdict(set);by_stage=defaultdict(set);bounds=(-22,20,-16,16)
    def cell(p):return (round(p[0]/step),round(p[1]/step))
    def xy(c):return (c[0]*step,c[1]*step)
    # Rasterize inflated convex components. No point-in-wall loophole from horizontal rays.
    for row in obstacles:
        poly=row['poly'];lo=[min(p[i] for p in poly)-radius for i in (0,1)];hi=[max(p[i] for p in poly)+radius for i in (0,1)]
        for ix in range(math.floor(lo[0]/step),math.ceil(hi[0]/step)+1):
            for iy in range(math.floor(lo[1]/step),math.ceil(hi[1]/step)+1):
                c=(ix,iy)
                if c not in by_stage[row['plot'],row['level']] and dist(xy(c),poly)<radius:
                    by_plot[row['plot']].add(c);by_stage[row['plot'],row['level']].add(c)
    blocked=set().union(*by_plot.values());all_blocked=set(blocked)
    def valid(c):return c not in blocked and bounds[0]<=c[0]*step<=bounds[1] and bounds[2]<=c[1]*step<=bounds[3]
    def line(a,b):
        n=max(1,math.ceil(math.dist(a,b)/.06))
        return all(valid(cell((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n))) for i in range(n+1))
    def search(start,goals):
        assert valid(start),('Blocked start',xy(start))
        target=list(goals);queue=[(0,0,start)];cost={start:0};previous={};seen=set();serial=0
        def heuristic(c):return min(math.hypot(c[0]-q[0],c[1]-q[1]) for q in target)
        while queue:
            _,_,c=heapq.heappop(queue)
            if c in seen:continue
            seen.add(c)
            if c in goals:
                path=[c]
                while path[-1] in previous:path.append(previous[path[-1]])
                return list(reversed(path))
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                q=(c[0]+dx,c[1]+dy)
                if not valid(q) or not valid((c[0]+dx,c[1])) or not valid((c[0],c[1]+dy)):continue
                value=cost[c]+math.hypot(dx,dy)
                if value>=cost.get(q,1e10):continue
                cost[q]=value;previous[q]=c;serial+=1;heapq.heappush(queue,(value+heuristic(q),serial,q))
        raise AssertionError(('No connected lane',xy(start)))
    def simplify(path):
        pp=[xy(c) for c in path];out=[pp[0]];i=0
        while i<len(pp)-1:
            j=next(j for j in range(len(pp)-1,i,-1) if line(pp[i],pp[j]));out.append(pp[j]);i=j
        return out
    market=cell((-.2,-5.6));north=cell((.3,5.1));network=set();routes=[]
    for name,start,end in [('Market to cathedral lane',market,north),('Village arrival',cell((-.2,-15)),market)]:
        raw=search(start,{end});network.update(raw);routes.append({'name':name,'points':simplify(raw),'width':.74})
    stats=json.loads((T.ROOT/'reports/model_stats.json').read_text())['models'];connections=[]
    new_doors={'cathedral':(0,-3.545),'inn':(.8,-.54),'watermill':(-.65,-1.545),'farmstead':(-2.1,-.895)}
    # Connect nearby doors first; more remote workshops share the resulting alleys.
    ordered=sorted(layout,key=lambda b:math.dist(b['xy'],(0,0)))
    environment=G.COL;stage_collections={n:G.collection(f'ACCESS • level {n} thresholds') for n in (1,2,3)}
    for n in (3,2,1):
        for b in ordered:
            blocked=set().union(*(cells for key,cells in by_plot.items() if key!=b['id']),by_stage[b['id'],n])
            d=new_doors[b['kind']] if b['kind'] in new_doors else stats[f"{b['kind']}_level_{n}"]['doors'][0]['xy']
            start=T.world_xy(b,(d[0],d[1]-.70));c=cell(start)
            assert valid(c),('Door obstructed',b['id'],n,start,[r['plot'] for r in obstacles if (r['plot']!=b['id'] or r['level']==n) and dist(start,r['poly'])<radius])
            raw=search(c,network);points=[T.world_xy(b,(d[0],d[1]-.28)),start]+simplify(raw)
            if n==3:network.update(raw)
            length=sum(math.dist(a,z) for a,z in zip(points,points[1:]))
            if len(points)>1 and length>.08:routes.append({'name':f"{b['id']} L{n} door",'points':points,'width':.66,'level':n})
            connections.append({'plot':b['id'],'level':n,'door_xy':list(d),'start':start,'points':points,'distance_to_shared_network_m':length,'clearance_radius_m':radius})
    blocked=all_blocked
    for r in routes:
        G.COL=stage_collections[r['level']] if 'level' in r else environment
        if len(r['points'])>1:paving('Shared alley • '+r['name'],r['points'],r['width'])
    G.COL=environment
    # Each complete route and terminal lead is explicit reviewable data, not a nearest-point claim.
    report={'method':'All-stage connected-component hulls at 0.205–1.85m; inflated 0.38m; connected 0.16m graph',
            'primary_doors':connections,'routes':routes,'obstacles':obstacles,'all_stage_primary_connections':len(connections),'blocked_grid_cells':len(blocked)}
    (T.ROOT/'reports/access.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
