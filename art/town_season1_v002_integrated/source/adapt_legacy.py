"""Copy only builder function definitions, then apply explicit dimensional edits.

No previous driver, file write, or export is executed. Generated modules are
owned editable source snapshots, and the original inputs stay hash-protected.
"""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
SOURCES={'cafe':ART/'town_cafe_v003/source/build_cafes.py','homes':ART/'town_house_florist_v001/source/build_set.py',
         'shops':ART/'town_sol_bakery_bookshop_v001/source/build_set.py','civic':ART/'town_sol_civic_market_workshop_v001/source/build_set.py'}
PATCHES={
'build':[
 ('global COL,PARENT,LOW','global COL,PARENT,LOW\n    G.LOW=low'),
 ("COL=collection('%s • cafe level %d'%(tag,level))","COL=collection('%s • cafe level %d'%(tag,level));G.COL=COL"),
 ("PARENT['level']=level;PARENT['pivot']='ground centre';PARENT['front']='-Y'","G.PARENT=PARENT\n    PARENT['level']=level;PARENT['pivot']='ground centre';PARENT['front']='-Y'"),
 ('(2.50,2.10,2.38),(3.0,2.40,2.63),(3.20,2.50,3.77)','(2.50,2.10,2.25),(3.0,2.40,2.25),(3.20,2.50,4.25)'),
 ('2.32),(2.55,.14,.40)','2.17),(2.55,.14,.40)'),('2.33','2.18'),('awning(0,y-.04,2.08','awning(0,y-.04,2.45'),
 ('(0,0,2.64)','(0,0,2.25)'),('2.83,.83,.78','2.70,.83,.94'),('2.91,.65,.61','2.78,.65,.78'),
 ('(x,y-.14,3.19)','(x,y-.14,3.17)'),('(.045,.055,.54)','(.045,.055,.70)'),('y-.23,2.80','y-.23,2.68'),
 ('3.22,.92,.58','3.38,.92,.85'),('(3.52,1.46,.11)','(4.10,1.46,.11)'),
 ('succulent(1.49,y-.64','succulent(1.85,y-.64'),('(1.03,y-1.19,.49)','(.05,y-1.19,.49)'),('for x in (.73,1.32)','for x in (-.25,.34)')],
'house':[
 ('(2.25,2.10,2.30),(2.60,2.25,2.45),(2.94,2.40,3.43)','(2.25,2.10,2.25),(2.60,2.25,2.25),(2.94,2.40,4.25)'),
 ('chimney(.91,.52,3.92)','chimney(.91,.52,4.74)'),('(0,0,2.44)','(0,0,2.25)'),
 ('y-.01,2.98,.62,.56','y-.01,3.35,.76,.85'),('2.49,.70,.91','2.14,1.0,1.79'),('2.55,.53,.78','2.16,.8,1.6'),
 ('(.035,.035,.68)','(.035,.035,1.42)'),('(.65,y-.165,2.94)','(.65,y-.165,2.96)'),
 ('w/2+.025,2.98,.95,.56','w/2+.025,3.42,.95,.85'),('y-.02,3.78','y-.02,4.60'),
 ('(0,y-.30,2.42)','(0,y-.30,2.08)'),('(x,y-.55,1.27)','(x,y-.55,1.08)'),('(.13,.13,2.28)','(.13,.13,1.94)'),
 ('y-.62,2.49','y-.62,2.16'),('y-.40,2.57','y-.40,2.28')],
'florist':[
 ('(2.20,2.00,2.28),(2.58,2.23,2.60),(2.68,2.30,2.75)','(2.20,2.00,2.25),(2.58,2.23,2.25),(2.68,2.30,2.25)')],
'bakery':[
 ('(0,2.30,1.96,2.34),(0,2.96,2.18,2.53),(-.39,2.46,2.34,3.65)','(0,2.30,1.96,2.25),(0,2.96,2.18,2.25),(-.39,2.46,2.34,4.25)'),
 ("ww+.26,'Clay light'","ww+.26,'Roof olive light'"),('succulent(-1.59','succulent(-1.75'),
 ('(x,0,2.49)','(x,0,2.25)'),('2.65,1.08,.83','2.70,1.08,.94'),('2.72,.86,.65','2.78,.86,.78'),
 ('(x,front-.17,3.04)','(x,front-.17,3.15)'),('(.05,.045,.59)','(.05,.045,.72)'),('(x,front-.19,2.62)','(x,front-.19,2.68)'),
 ('.03,3.03,.84,.68','.03,3.25,.84,.85'),('d/2+.025,3.03,.84,.68','d/2+.025,3.35,.84,.85')],
'bookshop':[
 ('(2.13,2.00,2.29,.86),(2.57,2.20,2.42,1.00),(2.89,2.34,3.10,1.30)','(2.13,2.00,2.25,.86),(2.57,2.20,2.25,1.00),(2.89,2.34,4.25,.95)'),
 ('book_cart(-.72,front-.95','book_cart(-.72,front-.72'),('bench(.76,front-1.28','bench(-.75,front-1.48'),
 ('(0,front-.14,3.08)','(0,front-.14,3.20)'),('1.99,.77,3.64,.48','1.99,.77,3.76,.48'),
 ('front-.40,3.12','front-.40,3.18'),('(0,front-.51,2.64)','(0,front-.51,2.68)'),
 ('.05,2.66,.84,.59','.05,3.38,.84,.85'),('d/2+.025,2.68,.84,.59','d/2+.025,3.38,.84,.85'),
 ('(.83,front-1.29,.645)','(-.68,front-1.49,.645)'),('(.83,front-1.29,.669)','(-.68,front-1.49,.669)')],
'town_hall':[
 ('(2.70,2.02,2.30),(3.10,2.18,2.57),(3.25,2.26,3.53)','(2.70,2.02,2.25),(3.10,2.18,2.25),(3.25,2.26,4.25)'),
 ('(0,0,2.46)','(0,0,2.25)'),('2.65,.69,.70','2.85,.69,.85'),('2.71,.53,.56','2.92,.53,.71'),
 ('(x,front-.165,2.97)','(x,front-.165,3.28)'),('(.04,.035,.47)','(.04,.035,.64)'),('front-.12,2.97','front-.12,3.28'),
 ('.02,2.99,.92,.62','.02,3.35,.92,.85'),('d/2+.025,2.99,1.12,.63','d/2+.025,3.35,1.12,.85')],
'cupola':[('o.location.z+=.08','o.location.z+=.80')],
'grocer':[
 ('(2.85,1.97,2.21),(3.20,2.14,2.31),(3.28,2.24,2.34)','(2.85,1.97,2.25),(3.20,2.14,2.25),(3.28,2.24,2.25)'),
 ('(-.94,.06,2.99),(1.34,2.04,1.31)','(-.94,.06,3.225),(1.34,2.04,2.05)'),
 ('1.63,2.34,3.70','1.63,2.34,4.30'),('window(-.94,-1.005,2.99,.87,.72','window(-.94,-1.005,3.19,.87,.85'),
 ("grocer_icon(-.94,-1.13,3.45)","grocer_icon(-.94,-1.13,4.05)"),('back_window(.94,1.105,2.99,.82,.70)','back_window(.94,1.105,3.31,.82,.85)')],
'workshop':[
 ('(0,2.32,2.02,2.20),(0,2.63,2.14,2.34),(-.43,2.38,2.26,3.19)','(0,2.32,2.02,2.25),(0,2.63,2.14,2.25),(-.43,2.38,2.26,4.25)'),
 ('(x,0,2.44)','(x,0,2.25)'),('front,2.81,.81,.54','front,3.19,.81,.85'),
 ('.05,2.82,.86,.54','.05,3.30,.86,.85'),('d/2+.025,2.82,.91,.54','d/2+.025,3.32,.91,.85')]
}
CAFÉ_FEATURES={'cup_icon','hip_roof','table','flowerbox','umbrella','build'}
EXCLUDE={'hashes','protected_hashes','check_components','stats','export','glb_stats','consolidate','configure','camera','row'}
HEADER='''"""Owned adaptation of existing miniature builder functions. Drivers excluded."""
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
'''
for module,path in SOURCES.items():
    source=path.read_text(encoding='utf-8');tree=ast.parse(source);functions=[]
    for node in tree.body:
        if not isinstance(node,ast.FunctionDef) or node.name in EXCLUDE:continue
        if module=='cafe' and node.name not in CAFÉ_FEATURES:continue
        text=ast.get_source_segment(source,node)
        for old,new in PATCHES.get(node.name,[]):
            assert old in text,(module,node.name,old)
            text=text.replace(old,new)
        functions.append(text)
    (ROOT/'source'/f'legacy_{module}.py').write_text(HEADER+'\n\n'.join(functions)+'\n',encoding='utf-8')
print('Adapted four owned builder modules; original drivers never executed')
