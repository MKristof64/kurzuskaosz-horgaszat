# -*- coding: utf-8 -*-
"""Derived bare-label story GLB. Run with final Hal_3D.blend already loaded.

Based on export_story.py. The loaded source scene is never saved, and only
copied/generated objects are selected for the new Hal_story_bare.glb export.
"""
import bpy
import hashlib
import json
import math
import pathlib
import struct
import time
from collections import defaultdict

import numpy as np

STARTED = time.time()
SOURCE = pathlib.Path(bpy.data.filepath).resolve()
assert SOURCE.name == 'Hal_3D.blend', 'Load the final Hal_3D.blend as input.'
OUT = SOURCE.parent
TARGET = OUT / 'Hal_story_bare.glb'
REPORT = OUT / 'Hal_story_bare_audit.json'
CATS = ['Ember', 'Folyamatok', 'Eszközök', 'Külső környezet', 'Szervezet']
COLS = [bpy.data.collections[n] for n in [
    '01 FISH | Csapósügér', '02 FINS | Úszók', '03 LABELS | Magyar feliratok']]
SOURCE_COL = bpy.data.collections['04 EDIT | Szövegforrások']
EXCLUDED_PREFIXES = ('LABEL_PANEL', 'LABEL_ACCENT', 'LABEL_LEADER')
MM_PER_BU = 100.0
STROKE_OFFSET = .0012
PALETTE = {
    'ink': '#223629',
    'LABEL_0': '#536246',
    'LABEL_1': '#68785A',
    'LABEL_2': '#3E5D45',
    'LABEL_3': '#877148',
    'LABEL_4': '#74653F',
    'LABEL_5': '#384E36',
    'LABEL_6': '#223629',
}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


protected = [p for p in [SOURCE, OUT / 'Hal_3D.obj', OUT / 'Hal_3D_atlatszo.png',
                       OUT / 'Hal_feliratokkal.png'] if p.exists()]
hashes_before = {p.name: sha(p) for p in protected}


def group_for(ob):
    label = ob.get('source_label', ob.name)
    if 'Vállalatnév' in label:
        return 'LABEL_6'
    if 'Eredmény' in label:
        return 'LABEL_5'
    matches = [i for i, cat in enumerate(CATS) if cat in label]
    assert len(matches) == 1, (ob.name, label, matches)
    return 'LABEL_' + str(matches[0])


def triangles(ob):
    counts = np.empty(len(ob.data.polygons), dtype=np.int32)
    ob.data.polygons.foreach_get('loop_total', counts)
    return int(np.maximum(counts - 2, 0).sum(dtype=np.int64))


def world_bounds(obs):
    lower = np.full(3, np.inf)
    upper = np.full(3, -np.inf)
    for ob in obs:
        co = np.empty(len(ob.data.vertices) * 3, dtype=np.float32)
        ob.data.vertices.foreach_get('co', co)
        matrix = np.asarray(ob.matrix_world, dtype=np.float64)
        world = co.reshape((-1, 3)) @ matrix[:3, :3].T + matrix[:3, 3]
        assert np.isfinite(world).all(), ob.name
        lower = np.minimum(lower, world.min(axis=0))
        upper = np.maximum(upper, world.max(axis=0))
    gltf_min = np.array([lower[0], lower[2], -upper[1]])
    gltf_max = np.array([upper[0], upper[2], -lower[1]])
    return {
        'blender': {'min': lower.tolist(), 'max': upper.tolist(),
                    'center': ((lower + upper) / 2).tolist(), 'size': (upper - lower).tolist()},
        'gltf': {'min': gltf_min.tolist(), 'max': gltf_max.tolist(),
                 'center': ((gltf_min + gltf_max) / 2).tolist(), 'size': (gltf_max - gltf_min).tolist()},
    }


def make_ink(name, hex_color):
    srgb = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in srgb]
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*linear, 1)
    material.use_nodes = True
    p = material.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*linear, 1)
    p.inputs['Roughness'].default_value = .72
    p.inputs['Metallic'].default_value = 0
    p.inputs['Coat Weight'].default_value = 0
    return material


original_texts = sorted([o for o in COLS[2].objects if o.type == 'MESH' and
                         o.name.startswith('LABEL_TEXT | ')], key=lambda o: o.name)
fonts = [o for o in SOURCE_COL.objects if o.type == 'FONT']
assert len(original_texts) == 32 and len(fonts) == 32
font_matches = {}
for original in original_texts:
    source_label = original['source_label']
    matches = [f for f in fonts if f.name == 'EDIT | ' + source_label]
    assert len(matches) == 1, (source_label, len(matches))
    assert matches[0].data.body == original['text_hu'], source_label
    font_matches[original.name] = matches[0]
assert len({f.name for f in font_matches.values()}) == 32

omitted = sorted(o.name for o in COLS[2].objects if o.name.startswith(EXCLUDED_PREFIXES))
retained_original = [o for o in COLS[2].objects if o.type == 'MESH' and
                     not o.name.startswith(EXCLUDED_PREFIXES)]
assert len(retained_original) == 52, 'Expected 32 texts plus 20 cause dots.'
original_groups = defaultdict(list)
for ob in retained_original:
    original_groups[group_for(ob)].append(ob)
original_bounds = {key: world_bounds(obs) for key, obs in sorted(original_groups.items())}

temp = bpy.data.collections.new('STORY_BARE_EXPORT')
bpy.context.scene.collection.children.link(temp)
materials = {key: make_ink('Story bare | ' + key, value) for key, value in PALETTE.items()}
copied_fish = []
generated_texts = []
label_copies = []
text_evidence = []

for collection in COLS[:2]:
    for original in collection.objects:
        if original.type != 'MESH':
            continue
        ob = original.copy()
        ob.data = original.data.copy()
        temp.objects.link(ob)
        copied_fish.append(ob)

print('BARE_STORY: regenerating 32 FONT sources with a thicker stroke', flush=True)
for original in original_texts:
    src = font_matches[original.name]
    family = group_for(original)
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = 'STORY_BARE_TEXT | ' + original['source_label']
    ob.hide_viewport = False
    ob.hide_render = False
    temp.objects.link(ob)
    ob.hide_set(False)
    ob.data.offset = STROKE_OFFSET
    ob.data.extrude = .0153
    ob.data.bevel_depth = .0027
    ob.data.bevel_resolution = 1
    ob.data.materials.clear()
    is_category_title = original['source_label'].endswith(' • cím')
    ob.data.materials.append(materials[family if is_category_title else 'ink'])
    ob['source_label'] = original['source_label']
    ob['text_hu'] = original['text_hu']
    ob['story_group'] = family
    ob['stroke_offset_BU'] = STROKE_OFFSET
    ob['letter_depth_mm'] = 3.6
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mod = ob.modifiers.new('Applied story lettering triangles', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)
    bounds = world_bounds([ob])
    depth_mm = bounds['blender']['size'][1] * MM_PER_BU
    assert 3.599 <= depth_mm <= 3.601, (ob.name, depth_mm)
    text_evidence.append({
        'source_mesh': original.name, 'font_source': src.name,
        'source_label': original['source_label'], 'text': original['text_hu'],
        'story_group': family, 'triangles': triangles(ob),
        'depth_mm': depth_mm, 'curve_offset_BU': STROKE_OFFSET,
        'original_bounds': world_bounds([original]), 'generated_bounds': bounds,
    })
    generated_texts.append(ob)
    label_copies.append(ob)

for original in retained_original:
    if original.name.startswith('LABEL_TEXT'):
        continue
    assert original.name.startswith('LABEL_DOT'), original.name
    family = group_for(original)
    ob = original.copy()
    ob.data = original.data.copy()
    temp.objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(materials[family])
    ob['story_group'] = family
    label_copies.append(ob)

fish_triangles = sum(triangles(o) for o in copied_fish)
label_triangles = sum(triangles(o) for o in label_copies)
assert fish_triangles >= 3000000
assert len(generated_texts) == 32 and len(label_copies) == 52
exported_label_groups = defaultdict(list)
for ob in label_copies:
    exported_label_groups[ob['story_group']].append(ob)
generated_bounds = {key: world_bounds(obs) for key, obs in sorted(exported_label_groups.items())}

# Keep one mesh per category (with multiple material slots), so each group can
# be transformed independently by the hanging-fish composition.
grouped = defaultdict(list)
for ob in copied_fish:
    grouped[('FISH', tuple(m.name for m in ob.data.materials))].append(ob)
for key, obs in sorted(exported_label_groups.items()):
    grouped[(key,)].extend(obs)

exports = []
for i, (key, obs) in enumerate(grouped.items()):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.object
    family = key[0]
    ob.name = family if family.startswith('LABEL_') else 'FISH__' + str(i)
    ob['story_group'] = family
    if family.startswith('LABEL_'):
        ob['source_label_count'] = sum(t['story_group'] == family for t in text_evidence)
        ob['background_panels'] = False
        ob['old_leaders'] = False
    exports.append(ob)

bpy.ops.object.select_all(action='DESELECT')
for ob in exports:
    ob.select_set(True)
assert sum(triangles(o) for o in exports) == fish_triangles + label_triangles
label_names = sorted(o.name for o in exports if o.name.startswith('LABEL_'))
assert label_names == ['LABEL_' + str(i) for i in range(7)]

print('BARE_STORY: export Draco GLB', flush=True)
bpy.ops.export_scene.gltf(
    filepath=str(TARGET), export_format='GLB', use_selection=True,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
    export_draco_position_quantization=16,
    export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=14,
    export_materials='EXPORT', export_extras=True,
)

raw = TARGET.read_bytes()
json_length, json_type = struct.unpack_from('<II', raw, 12)
gltf = json.loads(raw[20:20 + json_length])
gltf_mesh_nodes = [node for node in gltf.get('nodes', []) if 'mesh' in node]
actual_label_nodes = sorted(node['name'] for node in gltf_mesh_nodes if node.get('name', '').startswith('LABEL_'))
gltf_triangle_count = sum(gltf['accessors'][p['indices']]['count'] // 3
                          for mesh in gltf.get('meshes', []) for p in mesh['primitives'])
hashes_after = {p.name: sha(p) for p in protected}
category_names = CATS + ['Eredmény', 'Vállalatnév']
report = {
    'artifact': TARGET.name,
    'source_blend': SOURCE.name,
    'blender_version': bpy.app.version_string,
    'source_generator': 'work/export_story_bare.py, derived from work/export_story.py',
    'source_files_unchanged': hashes_before == hashes_after,
    'protected_source_hashes': hashes_after,
    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
    'triangles_total': fish_triangles + label_triangles,
    'triangles_fish': fish_triangles, 'triangles_labels': label_triangles,
    'gltf_accessor_triangle_count': gltf_triangle_count,
    'original_text_count': len(original_texts),
    'regenerated_text_count': len(generated_texts),
    'unique_font_sources': len(font_matches),
    'retained_cause_dots': 20,
    'exported_mesh_nodes': len(gltf_mesh_nodes),
    'label_group_count': len(actual_label_nodes), 'label_group_names': actual_label_nodes,
    'omitted_source_objects': omitted,
    'panel_objects_exported': 0, 'accent_objects_exported': 0, 'old_leader_objects_exported': 0,
    'palette_srgb': PALETTE,
    'letter_curve_offset_BU': STROKE_OFFSET,
    'letter_depth_mm_min': min(t['depth_mm'] for t in text_evidence),
    'letter_depth_mm_max': max(t['depth_mm'] for t in text_evidence),
    'coordinate_note': 'glTF coordinates = (Blender X, Blender Z, -Blender Y). Bounds and centers are world-space; no category was repositioned.',
    'categories': [{
        'group': 'LABEL_' + str(i), 'category': category_names[i],
        'text_count': sum(t['story_group'] == 'LABEL_' + str(i) for t in text_evidence),
        'original_bounds': original_bounds['LABEL_' + str(i)],
        'exported_bounds': generated_bounds['LABEL_' + str(i)],
    } for i in range(7)],
    'text_evidence': text_evidence,
    'checks': {
        'all_32_original_labels_regenerated_once': len(text_evidence) == 32 and len({t['source_label'] for t in text_evidence}) == 32,
        'all_32_font_sources_matched': len({t['font_source'] for t in text_evidence}) == 32,
        'all_letters_have_3_6mm_depth': all(3.599 <= t['depth_mm'] <= 3.601 for t in text_evidence),
        'all_letters_have_heavier_curve_offset': all(t['curve_offset_BU'] == STROKE_OFFSET for t in text_evidence),
        'no_panel_accent_or_old_leader_sources_exported': all(not o.name.startswith(EXCLUDED_PREFIXES) for o in retained_original),
        'seven_separate_label_groups': actual_label_nodes == ['LABEL_' + str(i) for i in range(7)],
        'fish_geometry_unchanged_and_over_3m_triangles': fish_triangles == 3676000,
        'gltf_triangle_count_matches_export_geometry': gltf_triangle_count == fish_triangles + label_triangles,
        'original_blend_obj_png_unchanged': hashes_before == hashes_after,
    },
    'duration_seconds': round(time.time() - STARTED, 3),
}
report['passed'] = all(report['checks'].values())
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('BARE_STORY_RESULT ' + json.dumps({k: v for k, v in report.items() if k not in ('text_evidence', 'categories', 'omitted_source_objects')}, ensure_ascii=False), flush=True)
assert report['passed'], report['checks']
