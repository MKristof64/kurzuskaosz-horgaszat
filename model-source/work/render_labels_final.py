import bpy,pathlib
out=pathlib.Path(bpy.data.filepath).parent;s=bpy.context.scene
bpy.data.collections['03 LABELS | Magyar feliratok'].hide_render=False
s.camera=bpy.data.objects['CAMERA | complete Hungarian diagram'];s.render.threads=10;s.render.resolution_percentage=100;s.render.resolution_x=3840;s.render.resolution_y=2720;s.cycles.samples=24;s.cycles.adaptive_threshold=.05;s.render.filepath=str(out/'Hal_feliratokkal.png')
bpy.ops.render.render(write_still=True)
print('DEEP_LABEL_RENDER_COMPLETE',flush=True)
