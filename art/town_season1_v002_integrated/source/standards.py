"""Metre-scale shared parts copied into the integrated revision."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
import geometry as G
from geometry import box,mesh,cyl,rod,ring,ellipsoid,arch
ROOT=Path(__file__).resolve().parents[1]

def materials():
    palette=json.loads((ROOT.parent/'town_house_florist_v001/reports/palette.json').read_text())
    palette.update({'Old stone':'D3C2A1','Stone shade':'B4A48A','Stone light':'E2D3B4','Warm plaster':'D9C49C',
                    'Roof slate':'4A716C','Roof slate light':'688B7D','Roof russet':'956A55','Roof russet light':'AE8263',
                    'Roof olive':'7B805B','Roof olive light':'939575','Barn blue':'78928B','Crop':'8EA865',
                    'Grass':'9BAA79','Path':'D9C8A6','Water':'80B6B8','Bank':'A49273'})
    for name,h in palette.items():
        mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=G.linear(h)
        node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=G.linear(h)
        node.inputs['Roughness'].default_value=.68;G.M[name]=mat
    mat=bpy.data.materials.new('Season 1 • opaque vertex palette');mat.use_nodes=True;mat.use_backface_culling=True
    node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Roughness'].default_value=.68;node.inputs['Metallic'].default_value=0
    vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Palette';mat.node_tree.links.new(vc.outputs['Color'],node.inputs['Base Color'])
    G.runtime_mat=mat
    return palette

def shell(x,y,w,d,h,color='Warm plaster',z=0):
    box('Foundation • continuous stone',(x,y,z+.09),(w+.16,d+.16,.18),'Stone shade',.045)
    box('Wall • plaster mass',(x,y,z+(h+.16)/2),(w,d,h-.16),color,.055)
    box('Wall • pale base belt',(x,y,z+.26),(w+.035,d+.035,.15),'Stone light',.025)

def gable(x,y,w,d,z,rise,color='Roof russet',light='Roof russet light',wall='Warm plaster',across=False,detail=True):
    old=set(G.COL.objects);hw=w/2-.12;hd=d/2-.10
    profile=[(-hw,z-.10),(hw,z-.10),(hw,z+.03),(0,z+rise-.025),(-hw,z+.03)]
    vs=[(xx,yy,zz) for yy in (-hd,hd) for xx,zz in profile];n=len(profile)
    mesh('Gable • closed stone infill',vs,[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)],wall)
    angle=math.atan2(rise,w/2);length=math.hypot(w/2,rise)
    for side in (-1,1):
        box('Roof • closed thick slope',(side*w/4,0,z+rise/2),(length+.10,d,.14),color,.028,rot=(0,side*angle,0))
        for yy in (-d/2,d/2):box('Roof • pale bargeboard',(side*w/4,yy,z+rise/2-.045),(length+.16,.12,.15),'Stone light',.018,rot=(0,side*angle,0))
        box('Roof • eave fascia',(side*w/2,0,z-.035),(.12,d+.08,.16),'Stone light',.018)
        if detail:
            for row in range(3):
                for col in range(5):
                    t=(row+.5)/3
                    box('Roof • broad tile colour',(side*w/2*t,-d/2+(col+.5)*d/5,z+rise*(1-t)+.081),
                        (length/3+.006,d/5-.018,.018),light if (col+row*2)%6==0 else color,0,rot=(0,side*angle,0))
    cyl('Roof • continuous ridge',(0,0,z+rise+.055),.075,d+.10,color,rot=(math.pi/2,0,0))
    for obj in set(G.COL.objects)-old:
        if across:obj.location=Vector((-obj.location.y,obj.location.x,obj.location.z));obj.rotation_euler[2]+=math.pi/2
        obj.location.x+=x;obj.location.y+=y

def door(x,y,z=0,w=.8,h=1.6,color='Teal'):
    arch('Door • pale arch frame',x,y,z+.14,w+.20,h+.19,.16,'Stone light')
    arch('Door • panel actual size',x,y-.105,z+.16,w,h,.08,color)
    box('Door • inset upper glazing',(x,y-.158,z+h*.69),(w*.55,.025,h*.31),'Glass',.008)
    box('Door • lower panel',(x,y-.16,z+h*.29),(w*.63,.025,h*.30),'Teal light',.008)
    cyl('Door • brass knob',(x+w*.31,y-.20,z+.84),.035,.045,'Brass',rot=(math.pi/2,0,0),thin=True)
    box('Door • threshold',(x,y-.23,z+.07),(w+.32,.53,.14),'Stone',.025)

def orient_new(before,x,y,angle):
    c=math.cos(angle);s=math.sin(angle)
    for o in set(G.COL.objects)-before:
        ox,oy=o.location.x,o.location.y;o.location.x=x+c*ox-s*oy;o.location.y=y+s*ox+c*oy;o.rotation_euler[2]+=angle

def facade_window(x,y,z,w=.72,h=.85,angle=0):
    before=set(G.COL.objects)
    box('Window • opaque blue glazing',(0,-.045,z),(w,.06,h),'Glass',0)
    for dx in (-w/2,w/2):box('Window • pale jamb',(dx,-.09,z),(.085,.12,h-.085),'Stone light',0)
    for dz in (-h/2,h/2):box('Window • pale lintel',(0,-.09,z+dz),(w+.085,.12,.085),'Stone light',0)
    box('Window • central mullion',(0,-.115,z),(.05,.08,h-.085),'Stone light',0)
    box('Window • deep sill',(0,-.14,z-h/2-.065),(w+.22,.27,.12),'Stone light',.018)
    orient_new(before,x,y,angle)

def bench(x,y,w=1.3):
    box('Courtyard • bench seat',(x,y,.43),(w,.38,.10),'Wood light',.025)
    box('Courtyard • bench back',(x,y+.17,.68),(w,.07,.29),'Wood light',.018)
    for dx in (-w*.34,w*.34):box('Courtyard • bench support',(x+dx,y,.22),(.10,.34,.44),'Wood',.012)

def rose_window(x,y,z,r):
    cyl('Rose window • stone disc',(x,y,z),r+.15,.13,'Stone light',rot=(math.pi/2,0,0))
    cyl('Rose window • opaque glass',(x,y-.083,z),r,.05,'Glass',rot=(math.pi/2,0,0))
    ring('Rose window • outer tracery',(x,y-.124,z),r*.85,.037,'Cream',rot=(math.pi/2,0,0))
    for i in range(6):
        a=i*math.tau/6
        rod('Rose window • radial tracery',(x,y-.15,z),(x+math.cos(a)*r*.87,y-.15,z+math.sin(a)*r*.87),.024,'Stone light')
    cyl('Rose window • warm centre',(x,y-.16,z),r*.22,.03,'Butter',rot=(math.pi/2,0,0),thin=True)
