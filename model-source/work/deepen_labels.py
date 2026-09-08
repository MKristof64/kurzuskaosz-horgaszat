import bpy,pathlib,json
out=pathlib.Path(bpy.data.filepath).parent
for ob in bpy.data.collections['03 LABELS | Magyar feliratok'].objects:
 if ob.type=='MESH' and ob.name.startswith('LABEL_TEXT'):
  for v in ob.data.vertices:v.co.y=-.167+9*(v.co.y+.18)
  ob['letter_depth_mm']=3.6
for ob in bpy.data.collections['04 EDIT | Szövegforrások'].objects:
 ob.data.extrude=.0153;ob.data.bevel_depth=.0027;ob.location.y=-.167
bpy.context.scene['letter_depth_mm']=3.6
info=json.loads((out/'modell_adatok.json').read_text(encoding='utf8'));info['letter_depth_mm']=3.6;info['letters_are_real_extruded_meshes']=True;(out/'modell_adatok.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Hal_3D.blend'),compress=True)
print('DEEP_3D_LETTERS_SAVED',flush=True)
