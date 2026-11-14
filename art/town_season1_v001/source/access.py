"""Inspected local doorway-ray helpers copied from v003; owned season copy."""
import bpy,math,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scene_common import models_in as model_objects,identity as id_of

def terrain_bvh(s):
    terrain=next(o for o in s.objects if o.type=='MESH' and 'terrain' in o.name.lower())
    terrain.data.calc_loop_triangles()
    return BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],[tuple(t.vertices) for t in terrain.data.loop_triangles],all_triangles=True)

def ground(bvh,x,y):
    p=bvh.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),80)[0]
    return p.z if p else 0.0

def road_candidates(s):
    points=[]
    for o in s.objects:
        if o.type=='MESH' and any(m and (m.name=='Path' or m.name.startswith('Path.')) for m in o.data.materials) and any(n in o.name.lower() for n in ('lane','alley','threshold','court','landing','approach')):
            stride=max(1,len(o.data.vertices)//180)
            points += [tuple((o.matrix_world@o.data.vertices[i].co).xy) for i in range(0,len(o.data.vertices),stride)]
    return list(set((round(x,4),round(y,4)) for x,y in points))

def building_bvhs(s):
    bpy.context.window.scene=s;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();result={}
    for instance in model_objects(s):
        vertices=[];faces=[]
        for obj in instance.instance_collection.all_objects:
            if obj.type!='MESH':continue
            ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();offset=len(vertices)
            transform=instance.matrix_world@obj.matrix_world
            vertices += [transform@v.co for v in me.vertices]
            faces += [tuple(offset+i for i in t.vertices) for t in me.loop_triangles];ev.to_mesh_clear()
        result[id_of(instance)]=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    return result

def clear_walk(points,bvh,obstacles,half_width,height):
    for aa,bb in zip(points,points[1:]):
        a=Vector(aa);b=Vector(bb);delta=b-a
        if delta.length<.03:continue
        normal=Vector((-delta.y,delta.x)).normalized();steps=max(2,math.ceil(delta.length/.25))
        for offset in (-half_width,0,half_width):
            positions=[]
            for i in range(steps+1):
                p=a.lerp(b,i/steps)+normal*offset
                positions.append(Vector((p.x,p.y,ground(bvh,p.x,p.y)+height)))
            for p,q in zip(positions,positions[1:]):
                d=q-p
                if d.length<1e-6:continue
                # A doorstep strip may follow gentle ground, never bridge a
                # retaining-wall drop as an almost vertical paving curtain.
                if abs(d.z)>max(.025,.70*math.hypot(d.x,d.y)):return False
                for collider in obstacles.values():
                    hit=collider.ray_cast(p,d.normalized(),d.length)
                    if hit[0] is not None and hit[3]<d.length-.0001:return False
    return True

def connection(start,candidates,bvh,obstacles,half_width,height,preferred=None,lead=None):
    options=[]
    if preferred is not None:options.append(tuple(preferred))
    options += sorted(candidates,key=lambda p:math.dist(start,p))[:260]
    prefixes=[[start]]+([[start,lead]] if lead else [])
    for prefix in prefixes:
        for end in options:
            points=prefix+[end]
            if clear_walk(points,bvh,obstacles,half_width,height):return points
        origin=prefix[-1]
        for end in options[:100]:
            for middle in ((origin[0],end[1]),(end[0],origin[1])):
                points=prefix+[middle,end]
                if clear_walk(points,bvh,obstacles,half_width,height):return points
    # Infill behind a shop sometimes needs more than one corner. A small local
    # grid traces a walk around the real meshes instead of drawing up a wall.
    for prefix in reversed(prefixes):
        if not clear_walk(prefix,bvh,obstacles,half_width,height):continue
        origin=prefix[-1];step=.38
        def xy(node):return (origin[0]+node[0]*step,origin[1]+node[1]*step)
        def heuristic(p):return min(math.dist(p,q) for q in candidates)
        queue=[(heuristic(origin),0,(0,0))];cost={(0,0):0};previous={};visited=set();serial=0
        while queue and len(visited)<2300:
            _,_,node=heapq.heappop(queue)
            if node in visited:continue
            visited.add(node);p=xy(node)
            nearby=sorted(candidates,key=lambda q:math.dist(p,q))[:8]
            end=next((q for q in nearby if math.dist(p,q)<.72 and clear_walk([p,q],bvh,obstacles,half_width,height)),None)
            if end is not None:
                nodes=[node]
                while nodes[-1] in previous:nodes.append(previous[nodes[-1]])
                path=prefix+[xy(n) for n in reversed(nodes[:-1])]+[end]
                simplified=[path[0]];index=0
                while index<len(path)-1:
                    farthest=next(j for j in range(len(path)-1,index,-1) if clear_walk([path[index],path[j]],bvh,obstacles,half_width,height))
                    simplified.append(path[farthest]);index=farthest
                return simplified
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nxt=(node[0]+dx,node[1]+dy)
                if max(abs(nxt[0]),abs(nxt[1]))>28 or nxt in visited:continue
                q=xy(nxt);value=cost[node]+math.dist(p,q)
                if value>=cost.get(nxt,float('inf')):continue
                if not clear_walk([p,q],bvh,obstacles,half_width,height):continue
                cost[nxt]=value;previous[nxt]=node;serial+=1
                heapq.heappush(queue,(value+heuristic(q),serial,nxt))
    raise AssertionError(('No clear doorstep connection',start))
