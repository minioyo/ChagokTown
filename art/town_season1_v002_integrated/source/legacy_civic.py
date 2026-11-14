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
def begin(key, level):
    # Editable components use exactly the delivered geometry, without a redundant dense variant.
    G.LOW = True
    G.COL = G.collection('EDIT • ' + key)
    G.PARENT = bpy.data.objects.new(key + '_root', None); G.COL.objects.link(G.PARENT)
    G.PARENT['level'] = level; G.PARENT['front'] = '-Y'; G.PARENT['units'] = 'metres'
    return G.COL, G.PARENT

def shell(x, y, w, d, h, color):
    box('Foundation • stone plinth', (x,y,.085), (w+.18,d+.18,.17), 'Stone', .065)
    box('Wall • plaster shell', (x,y,(h+.12)/2), (w,d,h-.12), color, .075)
    box('Wall • ivory skirting', (x,y,.25), (w+.04,d+.04,.17), 'Cream', .035)

def gable(x,y,w,d,z,rise,color,tile_color,wall_color,across=False,tiles=True):
    """Closed plaster gable with broad tiles. across rotates ridge to X for bakery."""
    old = set(G.COL.objects)
    a = math.atan2(rise,w/2); length = math.hypot(w/2,rise)
    hw = w/2-.15; hd = d/2-.15
    # The five-point profile overlaps the thick roof along the whole slope,
    # while its bottom still overlaps the upright wall. No triangular eave slit.
    profile=[(-hw,z-.12),(hw,z-.12),(hw,z+.04),(0,z+rise-.03),(-hw,z+.04)]
    vs=[(xx,yy,zz) for yy in (-hd,hd) for xx,zz in profile]
    k=len(profile)
    faces=[tuple(range(k)),tuple(range(2*k-1,k-1,-1))]+[(i,i+k,(i+1)%k+k,(i+1)%k) for i in range(k)]
    mesh('Gable • closed plaster infill',vs,faces,wall_color,.018)
    for side in (-1,1):
        box('Roof • thick slope',(side*w/4,0,z+rise/2),(length+.10,d,.15),color,.04,rot=(0,side*a,0))
        for yy in (-d/2,d/2):
            box('Roof • ivory bargeboard',(side*w/4,yy,z+rise/2-.055),(length+.17,.13,.17),'Cream',.026,rot=(0,side*a,0))
        box('Roof • ivory eave',(side*w/2,0,z-.04),(.13,d+.12,.18),'Cream',.026)
        if tiles:
            for row in range(3):
                t = (row+.5)/3
                for col in range(4):
                    box('Roof • broad tile',(side*w/2*t,-d/2+(col+.5)*d/4,z+rise*(1-t)+.086),
                        (length/3+.01,d/4-.016,.032),tile_color if (row+col)%5==0 else color,0,rot=(0,side*a,0))
    cyl('Roof • rounded ridge',(0,0,z+rise+.10),.105,d+.12,color,rot=(math.pi/2,0,0))
    for o in set(G.COL.objects)-old:
        if across:
            o.location = Vector((-o.location.y,o.location.x,o.location.z)); o.rotation_euler[2] += math.pi/2
        o.location.x += x; o.location.y += y

def side_window(x,y,z,w,h,cross=True):
    old = set(G.COL.objects); window(0,-x,z,w,h,cross=cross)
    for o in set(G.COL.objects)-old:
        o.location = Vector((-o.location.y,o.location.x+y,o.location.z)); o.rotation_euler[2] += math.pi/2

def back_window(x,y,z,w,h):
    old = set(G.COL.objects); window(x,-y,z,w,h)
    for o in set(G.COL.objects)-old:
        o.location.x = -o.location.x; o.location.y = -o.location.y; o.rotation_euler[2] += math.pi

def hall_icon(x,y,z,s=1):
    cyl('Hall • ivory community medallion',(x,y,z),.27*s,.07,'Cream',rot=(math.pi/2,0,0))
    for i in (-1,0,1):
        zz=z+(.045 if i==0 else -.005)*s
        ellipsoid('Hall • community head',(x+i*.13*s,y-.065,zz+.075*s),(.045*s,.025*s,.045*s),'Teal')
        box('Hall • community body',(x+i*.13*s,y-.06,zz-.025*s),(.075*s,.035,.09*s),'Teal',.025)

def bench(x,y,z=0,w=.72):
    box('Bench • timber seat',(x,y,z+.43),(w,.32,.10),'Wood light',.025)
    box('Bench • timber back',(x,y+.15,z+.63),(w,.07,.20),'Wood light',.02)
    for dx in (-w*.36,w*.36):
        for dy in (-.10,.10):rod('Bench • leg',(x+dx,y+dy,z),(x+dx,y+dy,z+.39),.025,'Teal dark')
        rod('Bench • back support',(x+dx,y+.14,z+.41),(x+dx,y+.14,z+.71),.022,'Teal dark')

def hall_porch(front,w):
    box('Hall porch • stone deck',(0,front-.56,.065),(w+.20,1.12,.13),'Stone',.045)
    box('Hall porch • golden canopy',(0,front-.37,2.12),(w+.08,.94,.15),'Brass',.035,rot=(.10,0,0))
    box('Hall porch • ivory eave',(0,front-.83,2.07),(w+.12,.10,.16),'Cream',.025)
    for x in (-w*.45,w*.45):
        box('Hall porch • ivory column',(x,front-.73,1.13),(.13,.13,2.0),'Cream',.026)
        rod('Hall porch • brace',(x,front-.72,1.81),(x,front-.42,2.08),.027,'Wood light')
    for x in (-w*.30,w*.30):bench(x,front-.42,.13,.66)

def cupola():
    old=set(G.COL.objects)
    box('Bell tower • ivory pedestal',(0,.03,4.14),(.89,.83,.20),'Cream',.035)
    for x in (-.34,.34):
        for y in (-.26,.32):box('Bell tower • ivory post',(x,y,4.57),(.10,.10,.73),'Cream',.023)
    for y in (-.27,.33):box('Bell tower • cross beam',(0,y,4.89),(.85,.11,.12),'Cream',.022)
    cyl('Bell tower • bell',(0,.03,4.56),.21,.30,'Brass',top=.10)
    cyl('Bell tower • lower bell lip',(0,.03,4.405),.23,.065,'Brass')
    ellipsoid('Bell tower • clapper',(0,.03,4.36),(.045,.045,.07),'Teal dark')
    rod('Bell tower • hanger',(0,.03,4.70),(0,.03,4.85),.025,'Teal dark')
    gable(0,.03,1.05,.95,4.94,.29,'Brass','Butter','Cream',tiles=False)
    ellipsoid('Bell tower • finial',(0,.03,5.39),(.075,.075,.12),'Brass')
    for o in set(G.COL.objects)-old:o.location.z+=.80

def town_hall(level):
    key=f'town_hall_level_{level}';coll,root=begin(key,level)
    w,d,h=[(2.70,2.02,2.25),(3.10,2.18,2.25),(3.25,2.26,4.25)][level-1]
    front=-d/2-.035
    shell(0,0,w,d,h,'Cream')
    gable(0,0,d+.38,w+.40,h+.025,.62 if level<3 else .66,'Brass','Butter','Cream',across=True)
    door(0,front-.02)
    for x in (-w*.32,w*.32):window(x,front,1.28,.56,.74,cross=False)
    side_window(w/2+.025,.03,1.35,.92,.86)
    back_window(0,d/2+.025,1.35,1.12,.83)
    if level==1:
        hall_icon(0,front-.10,2.03,.60)
    else:
        hall_porch(front,w)
        if level==2:hall_icon(0,front-.10,2.35,.60)
        else:
            box('Hall • upper ivory belt',(0,0,2.25),(w+.10,d+.08,.13),'Butter',.03)
            for x in (-.92,.92):
                arch('Hall upper • ivory arch',x,front-.04,2.85,.69,.85,.14,'Butter')
                arch('Hall upper • opaque glass',x,front-.13,2.92,.53,.71,.045,'Glass')
                box('Hall upper • mullion',(x,front-.165,3.28),(.04,.035,.64),'Cream',.008)
            hall_icon(0,front-.12,3.28,.95)
            side_window(w/2+.025,.02,3.35,.92,.85)
            back_window(0,d/2+.025,3.35,1.12,.85)
            cupola()
    bpy.context.view_layer.update();return coll,root

def lean_roof(x,y,w,d,z,color,wall_color,angle=.13):
    # A thick, shallow single-pitch roof, closed under the sloping eaves.
    box('Roof • closed sloping wall infill',(x,y,z-.17),(w-.22,d-.22,.33),wall_color,.018,rot=(angle,0,0))
    box('Roof • thick green slab',(x,y,z),(w,d,.16),color,.038,rot=(angle,0,0))
    for xx in (x-w/2,x+w/2):
        box('Roof • ivory side fascia',(xx,y,z-.045),(.11,d+.10,.17),'Cream',.025,rot=(angle,0,0))
    for dy in (-d/2,d/2):
        box('Roof • broad end fascia',(x,y+dy,z+math.sin(angle)*dy-.045),(w+.11,.10,.17),'Cream',.025)
    # A few broad standing seams keep the roof readable, without a tiled-house silhouette.
    for dx in (-w*.25,0,w*.25):
        box('Roof • broad raised seam',(x+dx,y,z+.09),(.035,d-.06,.035),color,.008,rot=(angle,0,0))

def apple(x,y,z,s=.16,color='Rose',icon=False):
    ellipsoid('Produce • whole apple',(x,y,z),(s,s*.47 if icon else s,s*.93),color)
    rod('Produce • apple stem',(x,y,z+s*.80),(x+.025,y,z+s*1.22),.018,'Wood')
    o=ellipsoid('Produce • single leaf',(x+.08,y,z+s*1.12),(.09,.028,.043),'Leaf dark');o.rotation_euler[1]=-.3

def grocer_icon(x,y,z):
    cyl('Grocer • ivory produce medallion',(x,y,z),.25,.075,'Cream',rot=(math.pi/2,0,0))
    apple(x,y-.07,z-.025,.15,'Rose',True)

def crate(x,y,z,w=.77,produce='Rose'):
    box('Market crate • box',(x,y,z+.15),(w,.44,.30),'Wood light',.025)
    box('Market crate • inset top',(x,y,z+.295),(w-.12,.32,.025),'Earth',.008)
    for xx in (-w/2,w/2):box('Market crate • raised end',(x+xx,y,z+.31),(.065,.45,.19),'Wood light',.016)
    for i in (-1,0,1):
        if produce=='Butter':
            ellipsoid('Produce • squash',(x+i*w*.24,y,z+.43),(.13,.13,.15),'Butter')
        else:apple(x+i*w*.24,y,z+.422,.125,produce)

def market_stand(x,y,z,produce):
    box('Market stand • timber shelf',(x,y,z+.47),(.89,.51,.09),'Wood light',.025)
    for dx in (-.34,.34):
        for dy in (-.16,.16):box('Market stand • leg',(x+dx,y+dy,z+.235),(.07,.07,.47),'Wood',.014)
    crate(x,y,z+.515,.83,produce)

def market_canopy(front,w):
    box('Market • broad green canopy',(0,front-.39,2.08),(w,.98,.12),'Sage',.035,rot=(.10,0,0))
    box('Market • cream valance',(0,front-.87,1.98),(w+.03,.09,.22),'Cream',.035)
    for xx in (-w*.30,0,w*.30):box('Market • green valance block',(xx,front-.927,1.98),(.37,.035,.20),'Leaf dark',.025)
    for x in (-w*.46,w*.46):
        box('Market • ivory awning post',(x,front-.79,1.08),(.09,.09,1.96),'Cream',.022)

def grocer(level):
    key=f'grocer_level_{level}';coll,root=begin(key,level)
    w,d,h=[(2.85,1.97,2.25),(3.20,2.14,2.25),(3.28,2.24,2.25)][level-1]
    front=-d/2-.035
    shell(0,0,w,d,h,'Apricot')
    lean_roof(0,0,w+.36,d+.36,h+.12,'Leaf dark','Apricot')
    door(0,front-.015)
    for x in (-w*.325,w*.325):window(x,front,1.19,.68,.84,cross=False)
    side_window(w/2+.02,.04,1.29,.85,.81)
    back_window(0,d/2+.025,1.31,1.12,.85)
    if level==1:
        grocer_icon(.95,front-.12,1.97)
        crate(-1.16,front-.36,0,.67,'Butter')
    else:
        box('Market • broad forecourt',(0,front-.72,.055),(3.78,1.43,.11),'Stone',.045)
        market_canopy(front,3.56)
        market_stand(-1.06,front-.92,.11,'Rose')
        market_stand(1.06,front-.92,.11,'Butter')
        if level==2:
            grocer_icon(0,front-.12,2.32)
        else:
            # One raised storage room and one low shop roof preserve a wide, low market role.
            box('Market loft • raised storeroom',(-.94,.06,3.225),(1.34,2.04,2.05),'Butter',.05)
            lean_roof(-.94,.06,1.63,2.34,4.30,'Leaf','Butter',.10)
            window(-.94,-1.005,3.19,.87,.85,cross=False)
            grocer_icon(-.94,-1.13,4.05)
            back_window(.94,1.105,3.31,.82,.85)
            # A restrained stack beside the store, kept away from the central doorway.
            crate(1.54,.68,0,.67,'Butter')
    bpy.context.view_layer.update();return coll,root

def saltbox(x,y,w,d,z,ridge_x,rise,color):
    left=-w/2;right=w/2;rz=z+rise
    hw=w/2-.15;hd=d/2-.15
    profile=[(-hw,z-.12),(hw,z-.12),(hw,z+.04),(ridge_x,rz-.03),(-hw,z+.04)]
    vs=[(xx,yy,zz) for yy in (-hd,hd) for xx,zz in profile]
    for i in range(len(vs)):vs[i]=(vs[i][0]+x,vs[i][1]+y,vs[i][2])
    k=len(profile)
    faces=[tuple(range(k)),tuple(range(2*k-1,k-1,-1))]+[(i,i+k,(i+1)%k+k,(i+1)%k) for i in range(k)]
    mesh('Workshop • solid asymmetric gable',vs,faces,'Butter',.018)
    for side,end in [(-1,left),(1,right)]:
        span=abs(end-ridge_x);length=math.hypot(span,rise);a=math.atan2(rise,span)*side
        xx=(end+ridge_x)/2
        box('Workshop • asymmetric roof slope',(x+xx,y,z+rise/2),(length+.11,d,.15),color,.035,rot=(0,a,0))
        for yy in (-d/2,d/2):
            box('Workshop • ivory bargeboard',(x+xx,y+yy,z+rise/2-.05),(length+.16,.12,.17),'Cream',.025,rot=(0,a,0))
        box('Workshop • ivory eave',(x+end,y,z-.04),(.12,d+.1,.17),'Cream',.025)
        for row in range(2):
            t=(row+.5)/2
            for col in range(4):
                box('Workshop • broad roof panel',(x+ridge_x+(end-ridge_x)*t,y-d/2+(col+.5)*d/4,rz-rise*t+.083),
                    (length/2+.01,d/4-.02,.032),color,0,rot=(0,a,0))
    cyl('Workshop • rounded offset ridge',(x+ridge_x,y,rz+.10),.10,d+.12,color,rot=(math.pi/2,0,0))

def hammer_icon(x,y,z,s=1):
    cyl('Workshop • ivory tool medallion',(x,y,z),.27*s,.075,'Cream',rot=(math.pi/2,0,0))
    box('Workshop icon • hammer handle',(x+.015*s,y-.065,z-.035*s),(.065*s,.045,.36*s),'Wood',.012,rot=(0,-.48,0))
    box('Workshop icon • hammer head',(x-.065*s,y-.075,z+.13*s),(.32*s,.07,.13*s),'Teal dark',.025,rot=(0,-.48,0))

def workbench(x,y,z,w=1.12):
    box('Workbench • thick timber top',(x,y,z+.68),(w,.51,.13),'Wood light',.03)
    box('Workbench • lower shelf',(x,y,z+.24),(w,.42,.09),'Wood light',.025)
    for dx in (-w*.39,w*.39):
        for dy in (-.16,.16):box('Workbench • leg',(x+dx,y+dy,z+.32),(.085,.085,.64),'Wood',.018)
    box('Workbench • small anvil foot',(x+.10,y,z+.785),(.34,.25,.08),'Teal dark',.015)
    box('Workbench • small anvil waist',(x+.10,y,z+.88),(.17,.17,.16),'Teal dark',.02)
    box('Workbench • small anvil head',(x+.10,y,z+.99),(.43,.22,.10),'Teal',.023)
    box('Workbench • wooden offcut',(x-.35,y-.03,z+.79),(.20,.21,.09),'Butter',.016,rot=(0,0,.2))

def workshop(level):
    key=f'workshop_level_{level}';coll,root=begin(key,level)
    x,w,d,h=[(0,2.32,2.02,2.25),(0,2.63,2.14,2.25),(-.43,2.38,2.26,4.25)][level-1]
    front=-d/2-.035
    shell(x,0,w,d,h,'Butter')
    saltbox(x,0,w+.40,d+.38,h+.025,-.36,.67,'Plum')
    door(x-.57,front-.015)
    window(x+.56,front,1.19,.78,.86,cross=False)
    side_window(x+w/2+.025,.08,1.30,.89,.82)
    back_window(-x,d/2+.025,1.32,.92,.83)
    hammer_icon(x-.36,front-.10,h+.31,.78)
    if level>=2:
        box('Workshop • stone work apron',(0,front-.67,.055),(3.35 if level==2 else 3.93,1.34,.11),'Stone',.045)
        cx,cw=(.67,1.76) if level==2 else (1.06,2.26)
        box('Workshop • sage work canopy',(cx,front-.40,2.04),(cw,1.02,.12),'Sage',.035,rot=(.11,0,0))
        box('Workshop • ivory canopy eave',(cx,front-.9,1.98),(cw+.04,.10,.15),'Cream',.025)
        for xx in (cx-cw/2+.05,cx+cw/2-.05):
            # Inner column is on the work-space side of the open entry route.
            box('Workshop • canopy post',(xx,front-.81,1.07),(.10,.10,1.94),'Cream',.022)
        workbench(.91 if level==2 else 1.10,front-.82,.11,1.02 if level==2 else 1.18)
        if level==3:
            box('Workshop upper • ivory belt',(x,0,2.25),(w+.10,d+.08,.13),'Cream',.03)
            window(x-.27,front,3.19,.81,.85,cross=False)
            side_window(x+w/2+.025,.05,3.30,.86,.85)
            back_window(-x,d/2+.025,3.32,.91,.85)
            shell(1.38,.08,1.12,1.96,1.89,'Apricot')
            lean_roof(1.38,.08,1.39,2.19,2.05,'Plum','Apricot',.11)
            side_window(1.965,.08,1.20,.80,.68)
    bpy.context.view_layer.update();return coll,root
