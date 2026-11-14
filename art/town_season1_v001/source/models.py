"""Four original season-one buildings. All dimensions are metres; front is -Y."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
import geometry as G
from geometry import box,mesh,cyl,rod,ring,ellipsoid,arch
ROOT=Path(__file__).resolve().parents[1]
LOTS={'cathedral':[[-4.0,-4.65],[3.75,4.65]],'inn':[[-3.8,-4.4],[3.8,3.55]],
      'watermill':[[-3.45,-3.0],[4.2,3.0]],'farmstead':[[-4.85,-3.6],[4.85,3.45]]}
DOORS={'cathedral':[0,-3.87],'inn':[.8,-.91],'watermill':[-.65,-1.84],'farmstead':[-2.1,-1.25]}
PROPORTIONS={'standard_door_panel_height_m':1.6,'standard_door_panel_width_m':.8,'standard_floor_pitch_m':2.0,
             'cathedral_main_door_exception':{'level_1':[.9,1.9],'level_2_3':[1.3,2.5]},
             'world_scale_new_buildings':[1,1,1]}

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

def begin(kind,level):
    G.scene=bpy.context.scene;G.LOW=True;G.COL=G.collection(f'EDIT • {kind}_level_{level}')
    G.PARENT=bpy.data.objects.new(f'{kind}_level_{level} • ground root',None);G.COL.objects.link(G.PARENT)
    G.PARENT['asset_id']=kind;G.PARENT['level']=level;G.PARENT['front']='-Y';G.PARENT['units']='metres'
    G.PARENT['standard_door_panel_m']=[.8,1.6];G.PARENT['floor_pitch_m']=2.0
    G.PARENT['placement_xy_min']=LOTS[kind][0];G.PARENT['placement_xy_max']=LOTS[kind][1]
    return G.COL,G.PARENT

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

def lancet(x,y,z,w=.65,h=1.65,angle=0):
    before=set(G.COL.objects)
    def shape(name,ww,hh,yy,color):
        pp=[(-ww/2,z),(ww/2,z),(ww/2,z+hh*.65),(0,z+hh),(-ww/2,z+hh*.65)]
        n=len(pp);vs=[(xx,yy+off,zz) for off in (-.035,.035) for xx,zz in pp]
        return mesh(name,vs,[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)],color)
    shape('Lancet • warm stone frame',w+.17,h+.13,0,'Stone light')
    shape('Lancet • opaque blue glazing',w,h,-.065,'Glass')
    box('Lancet • tall mullion',(0,-.113,z+h*.43),(.055,.035,h*.84),'Stone light',0)
    box('Lancet • sill',(0,-.035,z-.025),(w+.28,.25,.12),'Stone light',0)
    orient_new(before,x,y,angle)

def chimney(x,y,z):
    box('Chimney • broad stone stack',(x,y,z+.35),(.4,.45,.8),'Old stone',.035)
    box('Chimney • cap',(x,y,z+.77),(.55,.58,.13),'Stone light',.02)
    box('Chimney • dark closed mouth',(x,y,z+.842),(.28,.30,.012),'Dark wood',0)

def bench(x,y,w=1.3):
    box('Courtyard • bench seat',(x,y,.43),(w,.38,.10),'Wood light',.025)
    box('Courtyard • bench back',(x,y+.17,.68),(w,.07,.29),'Wood light',.018)
    for dx in (-w*.34,w*.34):box('Courtyard • bench support',(x+dx,y,.22),(.10,.34,.44),'Wood',.012)

def crate(x,y,z=0):
    box('Working yard • closed crate',(x,y,z+.24),(.65,.49,.48),'Wood light',.015)
    for dx in (-.26,.26):box('Working yard • crate strap',(x+dx,y-.251,z+.24),(.055,.025,.45),'Wood',0)

def rose_window(x,y,z,r):
    cyl('Rose window • stone disc',(x,y,z),r+.15,.13,'Stone light',rot=(math.pi/2,0,0))
    cyl('Rose window • opaque glass',(x,y-.083,z),r,.05,'Glass',rot=(math.pi/2,0,0))
    ring('Rose window • outer tracery',(x,y-.124,z),r*.85,.037,'Cream',rot=(math.pi/2,0,0))
    for i in range(6):
        a=i*math.tau/6
        rod('Rose window • radial tracery',(x,y-.15,z),(x+math.cos(a)*r*.87,y-.15,z+math.sin(a)*r*.87),.024,'Stone light')
    cyl('Rose window • warm centre',(x,y-.16,z),r*.22,.03,'Butter',rot=(math.pi/2,0,0),thin=True)

def cathedral(level,detail=True):
    coll,root=begin('cathedral',level)
    width=[3.15,3.65,3.9][level-1];depth=[4.1,5.65,6.6][level-1];front=-3.5;cy=front+depth/2
    eave=[3.45,4.35,5.45][level-1];rise=[1.2,1.5,1.7][level-1]
    shell(0,cy,width,depth,eave,'Old stone');gable(0,cy,width+.36,depth+.36,eave,rise,'Roof slate','Roof slate light','Old stone',detail=detail)
    if level>=2:
        for side in (-1,1):
            sx=side*(width/2+.53);d=depth-1.1
            shell(sx,cy+.4,1.08,d,2.8 if level==2 else 3.25,'Old stone')
            gable(sx,cy+.4,1.35,d+.25,2.8 if level==2 else 3.25,.65,'Roof slate','Roof slate light','Old stone',detail=detail)
        tx=-2.35 if level==2 else -2.5;ty=-2.35;tw=1.48 if level==2 else 1.65;th=5.65 if level==2 else 8.35
        shell(tx,ty,tw,1.82,th,'Old stone')
        box('Bell tower • stone crown',(tx,ty,th-.08),(tw+.25,2.08,.25),'Stone light',.025)
        cyl('Bell tower • four sided spire',(tx,ty,th+1.12),tw*.81,2.0,'Roof slate',top=0)
        box('Bell tower • cross upright',(tx,ty,th+2.38),(.075,.075,.72),'Brass',.008)
        box('Bell tower • cross arm',(tx,ty,th+2.48),(.40,.075,.075),'Brass',.008)
        if detail:
            for face in range(4):
                a=face*math.pi/2;xx=tx+math.sin(a)*(tw/2+.015);yy=ty-math.cos(a)*.925
                lancet(xx,yy,th-1.52,.55,1.17,a)
            for zz in (2.75,5.2) if level==3 else (2.75,):box('Bell tower • horizontal stone belt',(tx,ty,zz),(tw+.12,1.94,.16),'Stone light',.015)
    if level==3:
        shell(0,3.32,2.7,1.65,4.2,'Old stone');gable(0,3.32,3.0,1.9,4.2,1.1,'Roof slate','Roof slate light','Old stone',detail=detail)
    if detail:
        door(0,front-.045,w=.9 if level==1 else 1.3,h=1.9 if level==1 else 2.5)
        rose_window(0,front-.07,eave-.40,.46 if level==1 else .62)
        for side in (-1,1):
            for index in range(2 if level==1 else 3):
                yy=front+.9+index*(depth-1.7)/(1 if level==1 else 2)
                lancet(side*(width/2+.015),yy,1.05 if level==1 else (3.05 if level==2 else 3.55),.63,1.0 if level==2 else 1.60,side*math.pi/2)
                if level>=2:
                    xx=side*(width/2+1.075);lancet(xx,yy,.65,.52,1.45,side*math.pi/2)
                    box('Cathedral • buttress',(xx,yy,1.35),(.30,.39,2.7),'Stone shade',0)
                    box('Cathedral • buttress cap',(xx,yy,2.73),(.39,.49,.16),'Stone light',.02)
        if level>=2:
            before=set(G.COL.objects);door(0,0,w=.8,h=1.6);orient_new(before,width/2+1.11,cy-.8,math.pi/2)
        for dx in (-1.05,1.05):box('Cathedral • portal pier',(dx,front-.12,1.42),(.23,.34,2.84),'Stone light',.025)
    return coll,root

def inn(level,detail=True):
    coll,root=begin('inn',level);w=[3.3,5.0,6.2][level-1];d=[3.0,3.4,3.4][level-1];cy=-.5+d/2;h=2.25 if level==1 else 4.25
    shell(0,cy,w,d,h);gable(0,cy,d+.38,w+.42,h,1.0 if level==1 else 1.30,'Roof russet','Roof russet light','Warm plaster',across=True,detail=detail)
    if level>=2:
        wx=-1.75 if level==2 else -2.05;wd=2.35 if level==2 else 3.65;wy=-.45-wd/2
        shell(wx,wy,2.12,wd,2.25 if level==2 else 4.25)
        gable(wx,wy,2.48,wd+.25,2.25 if level==2 else 4.25,1.15,'Roof russet','Roof russet light','Warm plaster',detail=detail)
    if detail:
        door(.8,-.54)
        for xx in [-.8] if level==1 else [-.55,1.7]:
            facade_window(xx,-.53,1.25,.68,.82)
            if level>=2:facade_window(xx,-.53,3.25,.70,.86)
        for xx in (-w/2+.48,w/2-.48):
            for zz in ([1.25] if level==1 else [1.25,3.25]):facade_window(-xx,cy+d/2+.015,zz,.7,.85,math.pi)
        for zz in ([1.25] if level==1 else [1.25,3.25]):facade_window(w/2+.015,cy,zz,.82,.85,math.pi/2)
        for xx in (-w/2+.10,0,w/2-.10):box('Inn • exposed timber upright',(xx,-.56,h/2),(.09,.08,h-.1),'Wood',.009)
        if level>=2:box('Inn • floor timber belt',(0,-.565,2.23),(w+.04,.09,.14),'Wood',.012)
        box('Inn • shared porch canopy',(1.15,-1.0,2.06),(2.75,.88,.13),'Roof olive',.025,rot=(.12,0,0))
        for xx in (.0,2.3):box('Inn • porch post',(xx,-1.35,1.0),(.10,.10,2.0),'Wood',.01)
        bench(1.85,-1.13,.85);chimney(-w*.28,cy+.4,h+.65)
        if level>=2:
            facade_window(wx,wy-wd/2-.025,1.3,.7,.86)
            if level==3:facade_window(wx,wy-wd/2-.025,3.3,.7,.86)
        if level==3:
            # Open courtyard is part of the L silhouette, with a low shared wall.
            box('Inn • courtyard low wall',(1.0,-3.65,.33),(3.15,.22,.66),'Old stone',.03)
            for xx in (-.52,2.52):box('Inn • courtyard gate pier',(xx,-3.65,.48),(.34,.36,.96),'Stone light',.035)
            bench(.7,-2.9,1.3)
    return coll,root

def wheel(x,y,r=1.35):
    z=r+.08;depth=.62
    for xx in (x-depth/2,x+depth/2):
        ring('Mill wheel • timber rim',(xx,y,z),r-.08,.095,'Dark wood',rot=(0,math.pi/2,0))
        for i in range(8):
            a=i*math.tau/8
            rod('Mill wheel • radial spoke',(xx,y,z),(xx,y+math.sin(a)*(r-.14),z+math.cos(a)*(r-.14)),.048,'Wood')
    for i in range(12):
        a=i*math.tau/12
        box('Mill wheel • broad paddle',(x,y+math.sin(a)*r,z+math.cos(a)*r),(depth+.14,.30,.095),'Wood light',0,rot=(-a,0,0))
    cyl('Mill wheel • iron axle',(x,y,z),.15,depth+.46,'Teal dark',rot=(0,math.pi/2,0))

def watermill(level,detail=True):
    coll,root=begin('watermill',level);w=[3.05,3.6,3.8][level-1];d=[3.0,3.5,3.7][level-1];cy=-1.5+d/2;h=4.25 if level==3 else 2.25
    shell(0,cy,w,d,h,'Sage');gable(0,cy,w+.35,d+.38,h,1.15,'Roof olive','Roof olive light','Sage',detail=detail)
    wx=w/2+.68;wy=.15;radius=1.10 if level==1 else 1.35
    if detail:wheel(wx,wy,radius)
    else:cyl('BLOCK • wheel',(wx,wy,radius+.08),radius,.68,'Wood',rot=(0,math.pi/2,0))
    if level>=2:
        sx=-2.32;sd=2.1 if level==2 else 3.0;sy=.15
        shell(sx,sy,1.65,sd,2.05,'Warm plaster');gable(sx,sy,1.94,sd+.28,2.05,.65,'Roof olive','Roof olive light','Warm plaster',detail=detail)
    if detail:
        door(-.65,-1.545)
        facade_window(.72,-1.53,1.26,.70,.82)
        for zz in ([1.3,3.25] if level==3 else [1.3]):
            facade_window(-w/2-.015,cy+.25,zz,.76,.85,-math.pi/2)
            facade_window(.65,cy+d/2+.025,zz,.76,.85,math.pi)
        if level>=2:
            door(sx,sy-sd/2-.025);crate(-2.40,-1.8)
        if level==3:
            facade_window(-.65,-1.53,3.25,.70,.90);facade_window(.76,-1.53,3.25,.70,.90)
            box('Mill • loading canopy',(-2.20,-1.70,2.02),(2.10,.88,.13),'Roof olive',.025,rot=(.1,0,0))
            for xx in (-3.10,-1.30):box('Mill • canopy support',(xx,-2.07,.96),(.10,.10,1.92),'Wood',.012)
            crate(-2.65,1.9);crate(-1.98,1.9);chimney(-.8,cy+.7,h+.52)
        box('Mill • axle stone bearing',(w/2+.04,wy,.87),(.27,.53,1.74),'Old stone',.025)
    return coll,root

def crop_patch(x,y,w,d,rows=3):
    box('Farm • earth bed',(x,y,.035),(w,d,.07),'Earth',.01)
    for row in range(rows):
        yy=y-d/2+(row+.5)*d/rows
        box('Farm • raised soil row',(x,yy,.08),(w-.16,.20,.09),'Bank',.018)
        for i in range(4):
            o=ellipsoid('Farm • crop foliage',(x-w*.33+i*w*.22,yy,.20),(.14,.12,.17),'Crop')
            o.rotation_euler[1]=.22*(i%2*2-1)

def farmstead(level,detail=True):
    coll,root=begin('farmstead',level);hx=-2.1;hy=.65;h=2.25 if level<3 else 4.25
    shell(hx,hy,2.65,3.0,h,'Apricot');gable(hx,hy,3.02,3.38,h,1.05,'Roof russet','Roof russet light','Apricot',detail=detail)
    if level>=2:
        bx=1.35;by=.85;bw=2.65;bd=3.55
        shell(bx,by,bw,bd,2.65,'Barn blue');gable(bx,by,bw+.34,bd+.35,2.65,1.25,'Roof olive','Roof olive light','Barn blue',detail=detail)
        if level==3:
            shell(3.48,1.12,1.50,2.65,1.85,'Old stone');gable(3.48,1.12,1.76,2.92,1.85,.50,'Roof olive','Roof olive light','Old stone',detail=detail)
    if detail:
        door(hx,hy-1.545)
        facade_window(hx-.80,hy-1.53,1.28,.55,.75)
        facade_window(hx-1.34,hy+.2,1.28,.70,.82,-math.pi/2)
        facade_window(hx,hy+1.53,1.28,.78,.85,math.pi)
        chimney(hx-.70,hy+.5,h+.48)
        crop_patch(.70,-2.23,2.3,1.5,2 if level==1 else 3)
        if level>=2:
            box('Barn • broad double door',(bx,by-bd/2-.055,1.04),(1.62,.10,1.88),'Wood',.022)
            for dx in (-.83,.0,.83):box('Barn • door pale upright',(bx+dx,by-bd/2-.12,1.05),(.08,.08,1.98),'Stone light',.012)
            box('Barn • door top lintel',(bx,by-bd/2-.12,2.04),(1.83,.10,.13),'Stone light',.018)
            rod('Barn • door brace',(bx-.75,by-bd/2-.18,.18),(bx+.75,by-bd/2-.18,1.91),.032,'Wood light')
            facade_window(bx,by-bd/2-.04,2.62,.56,.47)
            box('Farm • low work canopy',(-.3,-1.18,2.02),(1.2,.92,.13),'Roof olive',.02,rot=(.10,0,0))
            crate(-.12,-1.64)
        if level==3:
            for xx in (hx-.65,hx+.65):facade_window(xx,hy-1.53,3.25,.68,.85)
            facade_window(hx-1.34,hy+.1,3.25,.8,.85,-math.pi/2)
            door(3.48,-.245);crop_patch(3.58,-2.04,1.45,1.8)
        # Only selected fence edges: the entrance and shared yard stay open.
        for x in (-.55,.70,1.95):
            box('Farm • short garden post',(x,-3.17,.36),(.095,.095,.72),'Wood',.012)
        for z in (.29,.53):box('Farm • garden rail',(.70,-3.17,z),(2.6,.075,.075),'Wood light',.012)
    return coll,root

BUILDERS={'cathedral':cathedral,'inn':inn,'watermill':watermill,'farmstead':farmstead}
