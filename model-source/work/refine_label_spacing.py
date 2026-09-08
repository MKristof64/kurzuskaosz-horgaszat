import bpy,pathlib
out=pathlib.Path(bpy.data.filepath).parent
for ob in bpy.data.collections['03 LABELS | Magyar feliratok'].objects:
 if ob.name in ['LABEL_PANEL | Ember','LABEL_PANEL | Folyamatok','LABEL_PANEL | Eszközök']:
  for v in ob.data.vertices:v.co.z=.57+(v.co.z-.57)*(1.26/1.14)
 if ob.name=='LABEL_TEXT | Vállalatnév • KurzusKáosz Kft.':
  for v in ob.data.vertices:v.co.z+=.40
src=bpy.data.objects.get('EDIT | Vállalatnév • KurzusKáosz Kft.')
if src:src.location.z+=.40
bpy.context.scene.camera=bpy.data.objects['CAMERA | complete Hungarian diagram']
bpy.data.collections['03 LABELS | Magyar feliratok'].hide_render=False
bpy.context.scene.render.filepath='//Hal_feliratokkal.png'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Hal_3D.blend'),compress=True)
print('FINAL_LABEL_SPACING_SAVED',flush=True)
