import bpy,pathlib,json
from collections import defaultdict
OUT=pathlib.Path(bpy.data.filepath).parent
CATS=['Ember','Folyamatok','Eszközök','Külső környezet','Szervezet']
cols=[bpy.data.collections[n] for n in ['01 FISH | Csapósügér','02 FINS | Úszók','03 LABELS | Magyar feliratok']]
for image in bpy.data.images:
 if image.name.startswith('Hal_skin_4K'):image.filepath=str(OUT/'Hal_skin_4K.png')
temp=bpy.data.collections.new('STORY_EXPORT');bpy.context.scene.collection.children.link(temp)
groups=defaultdict(list)
for c in cols:
 for o in c.objects:
  if o.type!='MESH':continue
  family='FISH'
  if c==cols[2]:family='LABEL_'+str(next((i for i,cat in enumerate(CATS) if cat in o.name),5))
  key=(family,tuple(m.name for m in o.data.materials))
  ob=o.copy();ob.data=o.data.copy();temp.objects.link(ob);groups[key].append(ob)
exports=[]
for i,(key,obs) in enumerate(groups.items()):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 ob=bpy.context.object;ob.name=key[0]+'__'+str(i);ob['story_group']=key[0];exports.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for o in exports:o.select_set(True)
target=OUT/'Hal_story.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=10,export_draco_texcoord_quantization=14,export_materials='EXPORT',export_extras=True)
print('STORY_EXPORT_PASS',len(exports),target.stat().st_size,flush=True)
