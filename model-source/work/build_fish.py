# -*- coding: utf-8 -*-
"""True 3D European-perch-inspired reconstruction with Hungarian diagram labels."""
import bpy, sys, math, json, pathlib, argparse, importlib.util
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs'/'Hal_3D'; OUT.mkdir(parents=True,exist_ok=True)
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ap=argparse.ArgumentParser(); ap.add_argument('--preview',action='store_true'); ap.add_argument('--no-export',action='store_true'); opt=ap.parse_args(argv)
bpy.ops.wm.read_factory_settings(use_empty=True); scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.10
def coll(name):
 c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
fishcol=coll('01 FISH | Csapósügér'); fincol=coll('02 FINS | Úszók'); labelcol=coll('03 LABELS | Magyar feliratok'); sourcecol=coll('04 EDIT | Szövegforrások'); studiocol=coll('05 STUDIO')
def srgb(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h):
 h=h.lstrip('#'); return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def mat(name,h,rough=.4,metal=.0):
 m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=color(h)
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=color(h); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 p.inputs['Coat Weight'].default_value=.25; p.inputs['Coat Roughness'].default_value=.22
 return m
M={
 'skin':mat('Skin | olive silver ctenoid scales','#8F9B64',.43,.055),
 'gill':mat('Gill covers | olive bronze','#8D985F',.36,.19),
 'lip':mat('Lips | natural warm olive','#8D9063',.39),
 'mouth':mat('Mouth cavity | dark tissue','#29231D',.60),
 'gill_dark':mat('Gill crease','#3D4934',.52),
 'fin_olive':mat('Fin membrane | olive translucent','#738159',.42),
 'fin_orange':mat('Fin membrane | burnt orange','#BD4D24',.43),
 'ray_dark':mat('Fin rays | olive bone','#485B3D',.34),
 'ray_orange':mat('Fin rays | amber','#BE6B30',.34),
 'pupil':mat('Eye | black pupil','#050806',.08),
 'socket':mat('Eye socket','#384938',.31),
 'gold':mat('Iris | gold green','#A7A050',.28,.35),
 'tooth':mat('Fine tooth bands','#D4D4B1',.45),
 'label':mat('Labels | porcelain lettering','#EDF6F3',.58),
 'panel':mat('Labels | midnight slate','#14292C',.55),
 'purple':mat('Ember | violet','#AA90ED',.45),
 'blue':mat('Folyamatok | blue','#64BCF2',.45),
 'green':mat('Eszközök | green','#72D7AC',.45),
 'orange':mat('Külső környezet | amber','#F3B65D',.45),
 'red':mat('Szervezet | coral','#F18084',.45),
}
for key in ('skin','gill','lip'):
 n=M[key].node_tree.nodes; l=M[key].node_tree.links; p=n.get('Principled BSDF')
 tc=n.new('ShaderNodeTexCoord'); noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=145; noise.inputs['Detail'].default_value=3
 l.new(tc.outputs['Generated'],noise.inputs['Vector']); b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.17; b.inputs['Distance'].default_value=.001
 l.new(noise.outputs['Fac'],b.inputs['Height']); l.new(b.outputs['Normal'],p.inputs['Normal'])
for key in ('fin_olive','fin_orange'):
 p=M[key].node_tree.nodes.get('Principled BSDF'); p.inputs['Transmission Weight'].default_value=.15; p.inputs['Subsurface Weight'].default_value=.09
cornea=mat('Eye | clear cornea','#FFFFFF',.055)
p=cornea.node_tree.nodes.get('Principled BSDF'); p.inputs['Transmission Weight'].default_value=.8; p.inputs['Alpha'].default_value=.14; p.inputs['IOR'].default_value=1.376; p.inputs['Coat Weight'].default_value=0
cornea.diffuse_color=(1,1,1,.14); cornea.surface_render_method='DITHERED'
M['cornea']=cornea

def make_mesh(name,coords,faces,material,collection=fishcol,smooth=True):
 me=bpy.data.meshes.new(name+' mesh')
 if isinstance(coords,np.ndarray) and isinstance(faces,np.ndarray):
  coords=np.asarray(coords,dtype=np.float32); faces=np.asarray(faces,dtype=np.int32)
  me.vertices.add(len(coords)); me.vertices.foreach_set('co',coords.ravel()); me.loops.add(faces.size); me.loops.foreach_set('vertex_index',faces.ravel()); me.polygons.add(len(faces)); me.polygons.foreach_set('loop_start',np.arange(0,faces.size,3,dtype=np.int32)); me.polygons.foreach_set('loop_total',np.full(len(faces),3,dtype=np.int32))
 else: me.from_pydata(coords,[],faces)
 me.update(); o=bpy.data.objects.new(name,me); collection.objects.link(o); me.materials.append(material)
 if smooth: me.polygons.foreach_set('use_smooth',np.ones(len(me.polygons),dtype=np.bool_))
 return o
def uv_for_mesh(ob,uv):
 layer=ob.data.uv_layers.new(name='UVMap'); layer.data.foreach_set('uv',np.asarray(uv,dtype=np.float32).ravel())
def tube(name,points,radius,material,collection=fishcol,resolution=10):
 cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=10; cu.bevel_depth=radius; cu.bevel_resolution=3
 sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points): p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,cu); collection.objects.link(ob); cu.materials.append(material)
 bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob; bpy.ops.object.convert(target='MESH'); ob.select_set(False); return ob
def ellipsoid(name,center,scale,material,segments=64,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=center)
 o=bpy.context.object; o.name=name; o.scale=scale
 for c in list(o.users_collection): c.objects.unlink(o)
 fishcol.objects.link(o); o.data.materials.append(material)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 o.select_set(False); return o

# Smooth longitudinal profile, X points toward the head.
XP=np.array([-1.63,-1.45,-1.20,-.85,-.45,0,.40,.72,1.00,1.25,1.48,1.68,1.86])
RZ=np.array([.095,.13,.245,.36,.47,.505,.485,.424,.347,.281,.224,.166,.066])
RY=np.array([.066,.079,.14,.235,.316,.358,.351,.322,.288,.246,.197,.15,.106])
CZ=np.array([.025,.025,.025,.025,.030,.045,.065,.067,.05,.036,.013,-.002,-.010])
def interp(x,p):
 # C1 cubic Hermite interpolation, with monotone-safe derivative magnitudes.
 slopes=np.gradient(p,XP); ids=np.clip(np.searchsorted(XP,x)-1,0,len(XP)-2); dx=XP[ids+1]-XP[ids]; t=(x-XP[ids])/dx
 return (2*t**3-3*t**2+1)*p[ids]+(t**3-2*t**2+t)*slopes[ids]*dx+(-2*t**3+3*t**2)*p[ids+1]+(t**3-t**2)*slopes[ids+1]*dx
def side_y(x,z,side):
 rz=float(interp(x,RZ)); ry=float(interp(x,RY)); cz=float(interp(x,CZ)); return side*ry*math.sqrt(max(.035,1-((z-cz)/rz)**2))

print('FISH: building 3,145,728 body triangles',flush=True)
NX,NT=2048,768
us=np.linspace(0,1,NX+1,dtype=np.float32); ts=np.arange(NT,dtype=np.float32)/NT
U,T=np.meshgrid(us,ts,indexing='ij'); X=-1.63+U*3.49; theta=T*2*np.pi
rz=interp(X,RZ); ry=interp(X,RY); cz=interp(X,CZ)
# Approximately 64 scale columns. Every raised overlapping edge is real geometry.
rows=np.floor(T*46); a=((U*64+.5*(rows%2))%1)-.5; b=((T*46)%1)-.5
d=np.sqrt((a/.61)**2+(b/.59)**2)
ridge=np.exp(-((d-.84)/.095)**2)*(.22+.78*np.clip(-a/.35,0,1))
scale_height=.00145*ridge*(1-.70*np.clip((X-.65)/1.05,0,1))
fine=.00013*np.sin(X*723+np.sin(theta*57))*np.sin(theta*331)
R=scale_height+fine
coords=np.stack([X,(ry+R)*np.cos(theta),cz+(rz+R)*np.sin(theta)],axis=-1).reshape(-1,3).astype(np.float32)
ii=np.arange(NX,dtype=np.int32)[:,None]*NT+np.arange(NT,dtype=np.int32)[None,:]; jj=ii//NT*NT+(ii+1)%NT
faces=np.empty((NX*NT*2,3),np.int32); faces[0::2]=np.stack([ii,jj,ii+NT],axis=-1).reshape(-1,3); faces[1::2]=np.stack([jj,jj+NT,ii+NT],axis=-1).reshape(-1,3)
body=make_mesh('FISH_Body | scaled, laterally compressed body',coords,faces,M['skin'])
uv=np.empty((NX*NT,6,2),np.float32); u0=np.broadcast_to(us[:-1,None],(NX,NT)).ravel(); u1=np.broadcast_to(us[1:,None],(NX,NT)).ravel(); t0=np.broadcast_to(ts[None,:],(NX,NT)).ravel(); t1=t0+1/NT
uv[:,0,:]=np.stack([u0,t0],-1); uv[:,1,:]=np.stack([u0,t1],-1); uv[:,2,:]=np.stack([u1,t0],-1); uv[:,3,:]=np.stack([u0,t1],-1); uv[:,4,:]=np.stack([u1,t1],-1); uv[:,5,:]=np.stack([u1,t0],-1)
uv_for_mesh(body,uv.reshape(-1,2)); body['body_triangles']=3145728; body['scale_columns']=64
del U,T,X,theta,rz,ry,cz,rows,a,b,d,ridge,scale_height,fine,R,coords,ii,jj,faces,uv,u0,u1,t0,t1

print('FISH: baking procedural skin pigment texture',flush=True)
W,H=4096,2048
UU,TT=np.meshgrid(np.linspace(0,1,W,dtype=np.float32),np.linspace(0,1,H,dtype=np.float32)); X=-1.63+UU*3.49; s=np.sin(TT*2*np.pi)
belly=np.array([.78,.80,.66]); flank=np.array([.51,.60,.35]); back=np.array([.16,.24,.15])
rgb=np.empty((H,W,3),np.float32); upper=np.clip(s,0,1)[...,None]; lower=np.clip(-s,0,1)[...,None]
rgb[:]=flank*(1-upper)+back*upper; rgb=rgb*(1-lower*.88)+belly*lower*.88
stripe=np.zeros((H,W),np.float32)
for k,c in enumerate([-1.24,-.89,-.54,-.17,.22,.61]):
 center=c+.075*np.sin(s*3+k*.75); width=.057+.016*np.maximum(s,0)
 stripe=np.maximum(stripe,np.exp(-((X-center)/width)**4))
stripe*=np.clip((s+.80)/.8,0,1)*.65
rgb*=1-stripe[...,None]
grain=(np.sin(X*813+TT*734)*np.cos(X*317-TT*1977)+np.sin(X*89+TT*371))*.012
rgb+=grain[...,None]
rows=np.floor(TT*46); aa=((UU*64+.5*(rows%2))%1)-.5; bb=((TT*46)%1)-.5; dd=np.sqrt((aa/.61)**2+(bb/.59)**2)
edge=np.exp(-((dd-.84)/.08)**2)*(.2+.8*np.clip(-aa/.35,0,1)); rgb*=1-edge[...,None]*.07
rgb=np.clip(rgb,0,1); linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
pixels=np.ones((H,W,4),np.float32); pixels[:,:,:3]=rgb
tex=bpy.data.images.new('Hal_skin_4K.png',width=W,height=H,alpha=True); tex.pixels.foreach_set(pixels.ravel()); tex.filepath_raw=str(OUT/'Hal_skin_4K.png'); tex.file_format='PNG'; tex.save()
bpy.data.images.remove(tex);tex=bpy.data.images.load(str(OUT/'Hal_skin_4K.png'));tex.colorspace_settings.name='sRGB';tex.pack()
n=M['skin'].node_tree.nodes; l=M['skin'].node_tree.links; im=n.new('ShaderNodeTexImage'); im.image=tex; l.new(im.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
del UU,TT,X,s,rgb,upper,lower,stripe,grain,rows,aa,bb,dd,edge,linear,pixels

# A terminal open mouth, inner cavity and fleshy lips.
print('FISH: anatomical features',flush=True)
lip_points=[]
for a in np.linspace(0,2*np.pi,97): lip_points.append((1.859+.004*math.cos(a),.106*math.cos(a),-.01+.066*math.sin(a)))
tube('FISH_Mouth | continuous fleshy lip',lip_points,.007,M['lip'])
mouth=ellipsoid('FISH_Mouth | recessed inner cavity',(1.800,0,-.012),(.071,.103,.064),M['mouth'])
ellipsoid('FISH_Mouth | continuous lower jaw',(1.74,0,-.095),(.135,.133,.053),M['lip'])
for i,a in enumerate(np.linspace(0,2*np.pi,30,endpoint=False)):
 ellipsoid('FISH_Tooth_%02d'%i,(1.827,.090*math.cos(a),-.01+.050*math.sin(a)),(.005,.0035,.0045),M['tooth'],12,8)

for side in (-1,1):
 # Layered gill cover, with a distinct rear edge and broad opercular spine.
 verts=[(.79,side*(abs(side_y(.79,-.01,side))+.008),-.01)]; rings,segments=32,128
 for j in range(1,rings+1):
  rr=j/rings
  for a in np.linspace(0,2*np.pi,segments,endpoint=False):
   x=.79+.30*rr*math.cos(a); z=-.01+.30*rr*math.sin(a); yy=side_y(x,z,side)+side*(.004+.006*(1-rr**2)); verts.append((x,yy,z))
 fs=[]
 for j in range(segments): fs.append((0,1+j,1+(j+1)%segments))
 for r in range(rings-1):
  aa=1+r*segments; bb=aa+segments
  for j in range(segments): k=(j+1)%segments; fs.extend([(aa+j,bb+j,bb+k),(aa+j,bb+k,aa+k)])
 if side>0: fs=[tuple(reversed(f)) for f in fs]
 plate=make_mesh('FISH_GillCover_'+str(side),verts,fs,M['skin'])
 uvs=[]
 for f in fs:
  for vi in f:
   x,yy,z=verts[vi];sn=np.clip((z-float(interp(x,CZ)))/float(interp(x,RZ)),-1,1);th=(math.pi-math.asin(sn)) if side<0 else math.asin(sn)%(2*math.pi);uvs.append(((x+1.63)/3.49,th/(2*math.pi)))
 uv_for_mesh(plate,uvs)
 points=[]
 for x,z in [(1.04,.21),(.89,.29),(.64,.28),(.51,.12),(.50,-.11),(.64,-.28),(.87,-.29)]: points.append((x,side_y(x,z,side)+side*.014,z))
 tube('FISH_OperculumSeam_'+str(side),points,.005,M['gill_dark'])
 jawpoints=[]
 for x,z in [(1.85,-.012),(1.71,-.038),(1.53,-.067),(1.35,-.085)]:jawpoints.append((x,side_y(x,z,side)+side*.006,z))
 tube('FISH_JawSeam_'+str(side),jawpoints,.0035,M['gill_dark'])
 ellipsoid('FISH_OpercularSpine_'+str(side),(.49,side*.316,.008),(.13,.018,.035),M['gill'])
 eye=(1.267,side*.241,.177)
 ellipsoid('FISH_EyeSocket_'+str(side),eye,(.124,.034,.124),M['socket'])
 ellipsoid('FISH_EyeIris_'+str(side),(eye[0],side*.271,eye[2]),(.106,.028,.106),M['gold'])
 for i in range(96):
  a=i*2*np.pi/96; p1=(eye[0]+.059*math.cos(a),side*.299,eye[2]+.059*math.sin(a)); p2=(eye[0]+.097*math.cos(a+.016),side*.289,eye[2]+.097*math.sin(a+.016))
  tube('FISH_IrisStriation_%d_%d'%(side,i),[p1,p2],.0009,M['gill_dark'] if i%3 else M['tooth'])
 ellipsoid('FISH_EyePupil_'+str(side),(eye[0],side*.304,eye[2]),(.051,.016,.055),M['pupil'])
 ellipsoid('FISH_Cornea_'+str(side),(eye[0],side*.284,eye[2]),(.107,.047,.107),M['cornea'])
 for i,(x,z) in enumerate([(1.563,.102),(1.639,.068)]): ellipsoid('FISH_Nostril_%d_%d'%(side,i),(x,side_y(x,z,side)+side*.002,z),(.015,.007,.009),M['gill_dark'],32,16)
 lateral=[]
 for i,x in enumerate(np.linspace(-1.44,.57,64)):
  z=float(interp(x,CZ)+interp(x,RZ)*.29); y=side_y(float(x),z,side)+side*.0035; lateral.append((x,y,z)); ellipsoid('FISH_LateralPore_%d_%02d'%(side,i),(x,y,z),(.0055,.0035,.004),M['gill_dark'],12,8)
 tube('FISH_LateralLine_'+str(side),lateral,.0013,M['gill_dark'])

spec=importlib.util.spec_from_file_location('fish_fins',ROOT/'work'/'fish_fins.py'); fins=importlib.util.module_from_spec(spec); spec.loader.exec_module(fins)
fins.build_fins(fincol,M)

# Dark rear blotch of the spiny first dorsal, attached to the membrane.
for ob in fincol.objects:
 if ob.name=='Dorsal_1_spiny_membrane':
  ob.data.materials.append(M['gill_dark'])
  for p in ob.data.polygons:
   x,y,z=p.center
   if ((x+.50)/.12)**2+((z-.60)/.105)**2 < 1+.13*math.sin(x*93+z*27):p.material_index=1

print('FISH: original Hungarian labels',flush=True)
font=bpy.data.fonts.load(str(ROOT/'outputs'/'assets'/'PatrickHand-Regular.ttf')); font.pack()
original=json.loads((ROOT/'outputs'/'ellenorzes.json').read_text(encoding='utf8'))['texts']
texts={x['name']:x['text'] for x in original}; text_manifest=[]
def text3d(name,body,x,z,size,maxwidth,material):
 cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.font=font; cu.size=size; cu.space_line=1.07; cu.resolution_u=5; cu.extrude=.0017; cu.bevel_depth=.0003; cu.bevel_resolution=1
 o=bpy.data.objects.new('LABEL_TEXT | '+name,cu); labelcol.objects.link(o); cu.materials.append(material)
 bpy.context.view_layer.update(); bounds=[Vector(p) for p in o.bound_box]; xmin=min(p.x for p in bounds); xmax=max(p.x for p in bounds); ymax=max(p.y for p in bounds)
 sx=min(1,maxwidth/max(xmax-xmin,1e-6)); o.scale=(sx,1,1); o.location=(x-xmin*sx,-.18,z-ymax); o.rotation_euler=(math.pi/2,0,0)
 o['text_hu']=body; o['source_label']=name
 src=o.copy();src.data=cu.copy();sourcecol.objects.link(src);src.name='EDIT | '+name
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
 text_manifest.append({'name':name,'text':body,'mesh':o.name})
 return o
def panel(name,cx,cz,w,h,key):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,-.13,cz));o=bpy.context.object;o.name='LABEL_PANEL | '+name;o.dimensions=(w,.035,h)
 for c in list(o.users_collection):c.objects.unlink(o)
 labelcol.objects.link(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M['panel'])
 bevel=o.modifiers.new('Soft panel edges','BEVEL');bevel.width=.022;bevel.segments=5;bpy.ops.object.modifier_apply(modifier=bevel.name);o.select_set(False)
 tube('LABEL_ACCENT | '+name,[(cx-w/2+.10,-.157,cz+h/2-.035),(cx+w/2-.10,-.157,cz+h/2-.035)],.012,M[key],labelcol)
groups=[('Ember','purple',-2.10,1.93,(-.90,-.40,.10)),('Folyamatok','blue',0,1.93,(.10,-.40,.10)),('Eszközök','green',2.10,1.93,(1.08,-.28,.08)),('Külső környezet','orange',-1.26,-1.47,(-.78,-.41,-.10)),('Szervezet','red',1.18,-1.47,(.70,-.34,-.09))]
for cat,key,cx,cz,anchor in groups:
 w=2.02 if cz>0 else 2.33;h=1.14
 panel(cat,cx,cz,w,h,key);left=cx-w/2+.11;top=cz+h/2-.095
 title=next(x for x in original if x['name']==cat+' • cím');sub=next(x for x in original if x['name']==cat+' • alcím')
 text3d(title['name'],title['text'],left,top,.20,w-.22,M[key]);text3d(sub['name'],sub['text'],left,top-.21,.094,w-.22,M['label'])
 z=top-.40
 for item in [x for x in original if x['category']==cat and ' • ok ' in x['name']]:
  body=item['text'];text3d(item['name'],body,left+.06,z,.093,w-.26,M['label']);
  # small cause dot, front-facing and physically part of the label group
  p=ellipsoid('LABEL_DOT | '+item['name'],(left+.015,-.17,z-.025),(.013,.008,.013),M[key],16,8)
  fishcol.objects.unlink(p);labelcol.objects.link(p)
  z-=.135 if '\n' not in body else .215
 attach=(cx,-.12,cz-h/2) if cz>0 else (cx,-.12,cz+h/2)
 tube('LABEL_LEADER | '+cat,[attach,(cx,-.18,attach[2]*.68),anchor],.008,M[key],labelcol)
text3d('Vállalatnév • KurzusKáosz Kft.','KurzusKáosz\nKft.',-3.10,.55,.25,.75,M['label'])
text3d('Eredmény • zavaros kurzusfelvétel','Zavaros,\nnehézkes\nkurzusfelvétel',2.16,.37,.16,.97,M['label'])
sourcecol.hide_render=True;sourcecol.hide_viewport=True

print('FISH: final triangulation',flush=True)
for collection in (fishcol,fincol,labelcol):
 for o in list(collection.objects):
  if o.type!='MESH':continue
  if all(len(p.vertices)==3 for p in o.data.polygons):continue
  bpy.context.view_layer.objects.active=o;o.select_set(True);mod=o.modifiers.new('Applied triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
def camera(name,pos,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.01;d.clip_end=100
 o=bpy.data.objects.new(name,d);studiocol.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
maincam=camera('CAMERA | fish three quarter',(3.7,-10,2.8),(-.2,0,.05),5.45)
labelcam=camera('CAMERA | complete Hungarian diagram',(0,-12,.28),(0,0,.28),7.02)
def area(name,pos,energy,size,colorv):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=colorv;o=bpy.data.objects.new(name,d);studiocol.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('STUDIO | broad softbox',(-1.0,-3.5,5.0),600,4.0,(.88,.95,1))
area('STUDIO | warm contour',(0,2.0,3.0),750,3.0,(1,.85,.58))
area('STUDIO | face fill',(4,-2,1.0),170,2.0,(1,.96,.85))
area('STUDIO | silver belly fill',(-.5,-3,-2.7),220,3.0,(.86,.95,1))
world=bpy.data.worlds.new('Neutral photographic world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.20,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
scene.camera=maincam;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.035;scene.cycles.max_bounces=6;scene.cycles.transmission_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=10;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.resolution_x=3840;scene.render.resolution_y=2400;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
allgeo=[o for c in (fishcol,fincol,labelcol) for o in c.objects if o.type=='MESH'];count=sum(len(o.data.polygons) for o in allgeo);fishcount=sum(len(o.data.polygons) for o in allgeo if o not in list(labelcol.objects))
assert fishcount>=3000000;assert len(text_manifest)==32
scene['triangles_total']=count;scene['triangles_fish']=fishcount;scene['anatomy_reference']='Perca fluviatilis; Museums Victoria / Australian Museum';scene['accuracy_note']='Species-informed artistic reconstruction, not a specimen scan. The original diagram contains no fish anatomy.'
(OUT/'modell_adatok.json').write_text(json.dumps({'triangles_total':count,'triangles_fish':fishcount,'labels':text_manifest,'species':'Perca fluviatilis','scale':'1 Blender unit = 10 cm','transparent_png':True,'anatomy_sources':['https://fishesofaustralia.net.au/home/species/3690','https://australian.museum/learn/animals/fishes/redfin-perca-fluviatilis/'],'original_labels':32,'fish_objects':len(fishcol.objects)+len(fincol.objects)},ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.file.pack_all();labelcol.hide_render=True
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL';a.spaces.active.overlay.show_overlays=False
scene.render.filepath='//Hal_3D_atlatszo.png';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hal_3D.blend'),compress=True)
print('FISH: saved; triangles=',count,' fish=',fishcount,flush=True)
if opt.preview:
 scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.cycles.samples=16;scene.render.filepath=str(ROOT/'work'/'fish_preview.png');bpy.ops.render.render(write_still=True)
else:
 bpy.ops.render.render(write_still=True)
 scene.camera=labelcam;labelcol.hide_render=False;scene.render.resolution_x=3840;scene.render.resolution_y=2720;scene.render.filepath=str(OUT/'Hal_feliratokkal.png');bpy.ops.render.render(write_still=True)
if not opt.no_export:
 labelcol.hide_render=False;bpy.ops.object.select_all(action='DESELECT')
 for o in allgeo:o.select_set(True)
 print('FISH: exporting OBJ',flush=True)
 bpy.ops.wm.obj_export(filepath=str(OUT/'Hal_3D.obj'),export_selected_objects=True,export_uv=True,export_normals=True,export_materials=True,export_triangulated_mesh=True,forward_axis='NEGATIVE_Z',up_axis='Y',path_mode='COPY')
 print('FISH: exporting compressed GLB',flush=True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'Hal_3D.glb'),export_format='GLB',use_selection=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=10,export_draco_texcoord_quantization=14,export_materials='EXPORT',export_extras=True)
print('FISH_COMPLETE',flush=True)
