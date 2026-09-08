# Blender fish source provenance

This bundle preserves byte-identical copies of the seven Blender generator,
fin helper, revision, export and rendering scripts used for the final fish,
plus the two subsequent story-asset exporters.
`SOURCE_MANIFEST.json` records their hashes and the required small inputs.
No model, export or render was rerun when assembling this bundle.

## Required environment and paths

Use Blender **4.5.13 LTS** with its bundled Python, NumPy and glTF/Draco add-on.
Blender itself is an external runtime and is not included.
Run from this bundle root and preserve this layout:

```text
work/build_fish.py
work/fish_fins.py
work/deepen_labels.py
work/refine_label_spacing.py
work/export_fish.py
work/render_fish_final.py
work/render_labels_final.py
work/export_story.py
work/export_story_bare.py
outputs/ellenorzes.json
outputs/assets/PatrickHand-Regular.ttf
outputs/assets/OFL.txt
outputs/Hal_3D/                 # generated artifacts, not source
```

`build_fish.py` derives its root from its own parent directory. It imports
`work/fish_fins.py`, loads the included font and reads the `texts` array in
`outputs/ellenorzes.json`. That JSON is an unchanged earlier diagram audit:
its other metrics describe the earlier flat diagram, not the final fish.
The generator creates `Hal_skin_4K.png` procedurally; there is no missing external
texture. The Patrick Hand font is distributed with its included SIL OFL license.

## Execution order

The examples use PowerShell. Point `$blenderExe` at the installed Blender binary.
Later scripts expect the generated `.blend` to be loaded on the command line.

```powershell
$blenderExe = 'C:/path/to/blender.exe'
& $blenderExe --background --factory-startup --python work/build_fish.py -- --no-export
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/deepen_labels.py
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/refine_label_spacing.py
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/export_fish.py
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/render_fish_final.py
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/render_labels_final.py
```

The base build creates geometry, materials, 32 Hungarian mesh labels, 32 hidden
editable font sources, scene cameras, lights, texture and metadata. It also
renders initial views; `--no-export` skips only its initial OBJ/GLB export.
`fish_fins.py` is imported by the builder, not run separately.
`deepen_labels.py` gives the letters approximately 3.6 mm physical depth at
1 Blender unit = 100 mm. `refine_label_spacing.py` applies the final spacing.
Run these two relative revision scripts **once after each fresh base build**;
they are not idempotent.

`export_fish.py` exports the full OBJ and a Draco GLB with copies grouped for
efficient browser drawing. It does not save its temporary grouping to the
source `.blend`. `render_fish_final.py` creates both final PNG views with
48 Cycles samples; `render_labels_final.py` supplies the delivered labelled
view's final 24-sample settings and therefore runs last.

The final geometry check recorded 4,727,260 triangles in total, including
3,676,000 fish triangles. Exact binary hashes can vary with export/runtime
versions even when source geometry is equivalent.

Keep generated `.blend`, `.obj`, `.mtl`, `.glb`, texture, PNG and ZIP artifacts
outside Git, or deliver them through the project's artifact storage. No large
generated binary is included here. All required source inputs were found.

## Subsequent bare-label story asset

`export_story.py` preserves the original story-export grouping recipe.
`export_story_bare.py` derives the later background-free story asset from the
final `.blend` without saving changes to it:

```powershell
& $blenderExe --background outputs/Hal_3D/Hal_3D.blend --python work/export_story_bare.py
```

It produces `Hal_story_bare.glb` and `Hal_story_bare_audit.json`. All 32 labels
are regenerated from the matching hidden font sources with a 0.0012 BU curve
offset and the same 3.6 mm extrusion depth. Labels use forest ink and muted
olive/bronze category colors. It omits panels, accents and the original
leaders, retains the 20 cause dots, and groups categories as `LABEL_0` through
`LABEL_4`, the result as `LABEL_5`, and the company as `LABEL_6`. It leaves
their coordinates unchanged; the report includes original/exported group
bounds and centers in Blender and glTF coordinates for later animation.

The derived artifact has 4,717,710 triangles, including the unchanged
3,676,000 fish triangles. This exporter has no external inputs beyond the
generated final `.blend` and its existing packed skin texture.
