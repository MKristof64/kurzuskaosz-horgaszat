import bpy,pathlib
OUT=pathlib.Path(bpy.data.filepath).parent;s=bpy.context.scene
labels=bpy.data.collections['03 LABELS | Magyar feliratok'];labels.hide_render=True
s.camera=bpy.data.objects['CAMERA | fish three quarter'];s.render.resolution_percentage=100;s.render.resolution_x=3840;s.render.resolution_y=2400;s.cycles.samples=48;s.cycles.adaptive_threshold=.035;s.render.filepath=str(OUT/'Hal_3D_atlatszo.png')
bpy.ops.render.render(write_still=True)
labels.hide_render=False;s.camera=bpy.data.objects['CAMERA | complete Hungarian diagram'];s.render.resolution_x=3840;s.render.resolution_y=2720;s.render.filepath=str(OUT/'Hal_feliratokkal.png')
bpy.ops.render.render(write_still=True)
print('RENDERS_COMPLETE',flush=True)
