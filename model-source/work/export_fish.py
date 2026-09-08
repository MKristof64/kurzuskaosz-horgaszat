import bpy,pathlib,json
from collections import defaultdict
OUT=pathlib.Path(bpy.data.filepath).parent
for image in bpy.data.images:
 if image.name.startswith('Hal_skin_4K'):image.filepath=str(OUT/'Hal_skin_4K.png')
cols=[bpy.data.collections[n] for n in ['01 FISH | Csapósügér','02 FINS | Úszók','03 LABELS | Magyar feliratok']]
cols[2].hide_render=False
objects=[o for c in cols for o in c.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
print('EXPORT: original full-detail OBJ',flush=True)
bpy.ops.wm.obj_export(filepath=str(OUT/'Hal_3D.obj'),export_selected_objects=True,export_uv=True,export_normals=True,export_materials=True,export_triangulated_mesh=True,forward_axis='NEGATIVE_Z',up_axis='Y',path_mode='COPY')
print('EXPORT: combine only export copies for browser draw-call efficiency',flush=True)
temp=bpy.data.collections.new('EXPORT_TEMP');bpy.context.scene.collection.children.link(temp)
groups=defaultdict(list)
for o in objects:
 key=('LABEL' if o in list(cols[2].objects) else 'FISH',tuple(m.name for m in o.data.materials))
 copy=o.copy();copy.data=o.data.copy();temp.objects.link(copy);groups[key].append(copy)
exports=[]
for i,(key,obs) in enumerate(groups.items()):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 joined=bpy.context.object;joined.name=key[0]+'_'+str(i)+'_'+key[1][0].split('|')[0].strip().replace(' ','_');exports.append(joined)
bpy.ops.object.select_all(action='DESELECT')
for o in exports:o.select_set(True)
print('EXPORT: Draco GLB, parts=',len(exports),flush=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'Hal_3D.glb'),export_format='GLB',use_selection=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=10,export_draco_texcoord_quantization=14,export_materials='EXPORT',export_extras=True)
print('EXPORT_COMPLETE',flush=True)
