"""Copied read-only spatial checks; no previous driver is imported."""
import bpy,math
from mathutils import Vector

def hull(points):
    pp=sorted(set(tuple(p) for p in points));lo=[];hi=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for p in pp:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pp):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]

def local_points(col):
    dg=bpy.context.evaluated_depsgraph_get();result=[]
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();result.extend(obj.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    return result

def world_xy(b,p):
    a=math.radians(b['yaw']);return (b['xy'][0]+math.cos(a)*p[0]-math.sin(a)*p[1],b['xy'][1]+math.sin(a)*p[0]+math.cos(a)*p[1])

def footprint(b,local):return [world_xy(b,p) for p in local[b['kind']]]

def separation(a,b):
    gap=-1e10
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx=q[0]-p[0];dy=q[1]-p[1];ll=math.hypot(dx,dy);axis=(-dy/ll,dx/ll)
            aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
            gap=max(gap,min(aa)-max(bb),min(bb)-max(aa))
    return gap
