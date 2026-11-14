"""Owned adaptation of existing miniature builder functions. Drivers excluded."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
import geometry as G
from geometry import box,mesh,cyl,rod,ring,ellipsoid,arch,window,side_window,door,succulent,awning
collection=G.collection
M=G.M
COL=None
PARENT=None
LOW=True
def cup_icon(x,y,z,s=1,disc=True):
    if disc:cyl('Sign • plain medallion',(x,y,z),.28*s,.10*s,'Cream',rot=(math.pi/2,0,0))
    yy=y-.065*s
    box('Sign • cup silhouette',(x-.025*s,yy,z),(.25*s,.045*s,.21*s),'Teal',.043*s)
    ring('Sign • cup handle',(x+.13*s,yy-.006*s,z+.015*s),.065*s,.022*s,'Teal',rot=(math.pi/2,0,0))
    box('Sign • saucer',(x-.018*s,yy,z-.14*s),(.35*s,.045*s,.036*s),'Teal',.012*s)

def hip_roof(w,d,z):
    a=w/2+.16;b=d/2+.16;inset=.38
    vs=[(-a,-b,z),(a,-b,z),(a,b,z),(-a,b,z),(-a+inset,-b+inset,z+.46),(a-inset,-b+inset,z+.46),(a-inset,b-inset,z+.46),(-a+inset,b-inset,z+.46)]
    mesh('Roof • soft hipped shell',vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'Teal',.055)
    box('Roof • rounded crown',(0,0,z+.46),(w-.40,d-.40,.13),'Teal light',.055)
    for i in range(5):
        x=(i-2)*w*.20
        rod('Roof • front seam',(x,-b+.04,z+.04),(x*.78,-b+inset-.01,z+.50),.018,'Teal light')

def table(x,y,z=0):
    cyl('Terrace • round tabletop',(x,y,z+.63),.32,.085,'Wood light')
    rod('Terrace • pedestal',(x,y,z+.06),(x,y,z+.60),.045,'Teal dark')
    cyl('Terrace • table foot',(x,y,z+.04),.21,.08,'Teal dark')
    for dx in (-.48,.48):
        cyl('Terrace • stool seat',(x+dx,y+.03,z+.35),.16,.08,'Wood light')
        for a in (0,math.tau/3,2*math.tau/3):
            ox=.105*math.cos(a);oy=.105*math.sin(a)
            rod('Terrace • stool leg',(x+dx+ox,y+.03+oy,z+.02),(x+dx+ox*.7,y+.03+oy*.7,z+.32),.023,'Teal dark')
    cyl('Terrace • cup',(x-.05,y,z+.725),.06,.11,'Cream',top=.073)
    cyl('Terrace • coffee',(x-.05,y,z+.783),.058,.005,'Dark wood',thin=True)

def flowerbox(x,y,z,w=.78):
    box('Upper • flowerbox',(x,y,z),(w,.26,.19),'Wood light',.035)
    for i in range(3):
        xx=x+(i-1)*w*.25
        ellipsoid('Upper • foliage',(xx,y,z+.15),(.15,.11,.11),'Leaf')
        for k in range(4):
            a=k*math.tau/4
            ellipsoid('Upper • flower petal',(xx+.055*math.cos(a),y+.055*math.sin(a),z+.25),(.058,.058,.035),'Pink' if i%2 else 'Flower')

def umbrella(x,y,z):
    rod('Terrace • umbrella pole',(x,y,.12),(x,y,z+.23),.028,'Wood')
    n=8;vs=[(x,y,z+.25)]+[(x+.77*math.cos(i*math.tau/n),y+.77*math.sin(i*math.tau/n),z-.05) for i in range(n)]
    o=mesh('Terrace • scalloped umbrella',vs,[(0,i+1,(i+1)%n+1) for i in range(n)],'Cream')
    o.data.materials.append(M['Teal light'])
    for p in o.data.polygons:p.material_index=p.index%2;p.use_smooth=True
    m=o.modifiers.new('Canopy thickness','SOLIDIFY');m.thickness=.025
    ellipsoid('Terrace • umbrella finial',(x,y,z+.27),(.05,.05,.06),'Wood')

def build(level,low):
    global COL,PARENT,LOW
    G.LOW=low
    LOW=low;tag='LOW' if low else 'EDIT'
    COL=collection('%s • cafe level %d'%(tag,level));G.COL=COL
    PARENT=bpy.data.objects.new('cafe_level_%d_%s'%(level,tag.lower()),None);COL.objects.link(PARENT)
    G.PARENT=PARENT
    PARENT['level']=level;PARENT['pivot']='ground centre';PARENT['front']='-Y'
    w,d,h=[(2.50,2.10,2.25),(3.0,2.40,2.25),(3.20,2.50,4.25)][level-1]
    y=-d/2-.04
    box('Foundation • stone plinth',(0,0,.095),(w+.22,d+.20,.19),'Stone',.07)
    box('Wall • butter plaster',(0,0,(h+.13)/2),(w,d,h-.13),'Butter',.085)
    box('Wall • cream skirting',(0,0,.28),(w+.05,d+.05,.20),'Cream',.035)
    box('Roof • cream cornice',(0,0,h),(w+.24,d+.24,.20),'Cream',.06)
    hip_roof(w,d,h+.11)
    dx=.72 if level==1 else 1.0
    door(dx,y-.02)
    window(-.51,y-.01,1.17,1.00 if level==1 else 1.34,1.16 if level==1 else 1.37,trim='Teal dark',cross=False)
    side_window(w/2+.025,1.38,1.00 if level==1 else 1.18,1.06)
    # A pictogram takes the place of all lettering; no FONT objects or text textures.
    if level==1:
        cup_icon(-.48,y-.06,2.10,.70)
        awning(-.51,y-.02,1.94,1.35,5,.49)
        succulent(1.46,y-.29,0,.14,.21)
    else:
        box('Fascia • plain cream band',(0,y-.04,2.17),(2.55,.14,.40),'Cream',.065)
        cup_icon(0,y-.155,2.18,.69,False)
        # Small bean silhouettes, never text, on the central pictogram band.
        for x in (-.36,.36):
            bean=ellipsoid('Fascia • coffee bean',(x,y-.167,2.18),(.07,.025,.105),'Wood')
            bean.rotation_euler[1]=.45 if x>0 else -.45
        awning(0,y-.04,2.45,w-.04,10)
        rod('Sign • hanging arm',(w/2-.06,y,2.49),(w/2+.37,y-.40,2.49),.032,'Dark wood')
        cup_icon(w/2+.30,y-.44,2.19,.95)
        if level==2:
            table(-.85,y-.97)
            succulent(.26,y-.43,0,.16,.25)
        else:
            # A real second floor changes silhouette and scale, not just decoration.
            box('Upper • belt cornice',(0,0,2.25),(w+.18,d+.18,.17),'Cream',.04)
            for x in (-.79,.79):
                arch('Upper • arched surround',x,y-.01,2.70,.83,.94,.16,'Cream')
                arch('Upper • arched glazing',x,y-.105,2.78,.65,.78,.04,'Glass')
                box('Upper • central mullion',(x,y-.14,3.17),(.045,.055,.70),'Cream',.01)
                flowerbox(x,y-.23,2.68)
            side_window(w/2+.035,3.38,.92,.85)
            # Paved terrace remains inside the common 4.8 x 4.8 m placement envelope.
            box('Terrace • patio base',(0,y-.72,.055),(4.10,1.46,.11),'Stone',.06)
            table(-.88,y-.91,.11)
            umbrella(-.88,y-1.04,2.40)
            succulent(1.85,y-.64,.11,.22,.32)
            box('Terrace • seat',(.05,y-1.19,.49),(.80,.30,.09),'Wood light',.035)
            for x in (-.25,.34):rod('Terrace • seat leg',(x,y-1.19,.11),(x,y-1.19,.46),.04,'Teal dark')
            # One small roof vent adds the final silhouette accent.
            cyl('Roof • vent',(1.02,.63,h+.68),.11,.36,'Teal dark')
            cyl('Roof • vent cap',(1.02,.63,h+.88),.18,.075,'Cream')
    bpy.context.view_layer.update()
    return COL,PARENT
