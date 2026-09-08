"""Modeled European-perch fins. Safe to import: no scene changes until build_fins.

Coordinates: head +X, dorsum +Z, flanks +/-Y; units are scene fish units.
Every membrane is a closed thin mesh and every ray is tapered, modeled geometry.
"""
import math
import bpy
import numpy as np


PROFILE_X = np.array([-1.62, -1.35, -1., -.5, 0., .5, .85, 1.1, 1.3, 1.53, 1.85])
PROFILE_Z = np.array([.10, .19, .32, .47, .51, .46, .38, .32, .255, .18, .095])


def _smooth_interp(values, positions):
    """Clamped Catmull-Rom interpolation through the individual ray positions."""
    values = np.asarray(values, dtype=np.float64)
    pos = np.asarray(positions, dtype=np.float64)
    k = np.floor(pos).astype(int)
    u = (pos-k)[..., None]
    a = values[np.clip(k-1, 0, len(values)-1)]
    b = values[np.clip(k, 0, len(values)-1)]
    c = values[np.clip(k+1, 0, len(values)-1)]
    d = values[np.clip(k+2, 0, len(values)-1)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)


def _mesh(name, verts, faces, collection, material):
    verts = np.asarray(verts, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set("co", verts.reshape(-1))
    mesh.loops.add(faces.size)
    mesh.loops.foreach_set("vertex_index", faces.reshape(-1))
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set("loop_start", np.arange(len(faces), dtype=np.int32)*faces.shape[1])
    mesh.polygons.foreach_set("loop_total", np.full(len(faces), faces.shape[1], dtype=np.int32))
    mesh.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _add_tube(verts, faces, points, radius, sides=8):
    """Closed tube with transported local frames and a fine rounded distal tip."""
    points = np.asarray(points, dtype=np.float64)
    tangent = np.gradient(points, axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-12)
    reference = np.repeat([[0., 1., 0.]], len(points), axis=0)
    parallel = abs(tangent[:, 1]) > .88
    reference[parallel] = [0., 0., 1.]
    normal = np.cross(tangent, reference)
    normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-12)
    binormal = np.cross(tangent, normal)
    a = np.linspace(0., 2*math.pi, sides, endpoint=False)
    t = np.linspace(0., 1., len(points))
    # A fine, finite end ring avoids zero-area tip polygons.
    radii = radius * (.105 + .895*(1.-t)**.78)
    rings = points[:, None, :] + radii[:, None, None]*(
        np.cos(a)[None, :, None]*normal[:, None, :] +
        np.sin(a)[None, :, None]*binormal[:, None, :])
    offset = len(verts)
    verts.extend(rings.reshape(-1, 3).tolist())
    for j in range(len(points)-1):
        for k in range(sides):
            p = offset+j*sides+k
            q = offset+j*sides+(k+1)%sides
            # s runs around each ring, t runs along the ray.
            faces.append((p, q, q+sides))
            faces.append((p, q+sides, p+sides))
    first_center = len(verts)
    verts.append(points[0].tolist())
    last_center = len(verts)
    verts.append(points[-1].tolist())
    end = offset+(len(points)-1)*sides
    for k in range(sides):
        nk = (k+1)%sides
        faces.append((first_center, offset+nk, offset+k))
        faces.append((last_center, end+k, end+nk))


def _ray_path(root, tip, bend, samples=33):
    t = np.linspace(0., 1., samples)[:, None]
    return root[None, :]*(1.-t) + tip[None, :]*t + np.sin(math.pi*t)*bend[None, :]


def _build_fin(name, roots, tips, bends, collection, membrane_material,
               ray_material, spines, normal_hint, scallop=.026,
               thickness=.0022, radius=.0085, cross_steps=22,
               radial_steps=34, branch=True):
    roots = np.asarray(roots, dtype=np.float64)
    tips = np.asarray(tips, dtype=np.float64)
    bends = np.asarray(bends, dtype=np.float64)
    ray_count = len(roots)
    ns = (ray_count-1)*cross_steps+1
    nt = radial_steps+1
    s = np.linspace(0., ray_count-1., ns)
    t = np.linspace(0., 1., nt)
    rs = _smooth_interp(roots, s)
    ts = _smooth_interp(tips, s)
    bs = _smooth_interp(bends, s)
    q = s-np.floor(s)
    scallops = np.sin(math.pi*q)**1.65
    # Membrane sits below the terminal ends of rays, forming soft natural bays.
    ts -= (ts-rs)*scallop*scallops[:, None]
    center = rs[:, None, :]*(1.-t[None, :, None])+ts[:, None, :]*t[None, :, None]
    center += np.sin(math.pi*t)[None, :, None]*bs[:, None, :]
    nh = np.asarray(normal_hint, dtype=np.float64)
    nh /= np.linalg.norm(nh)
    # Subtle radial corrugation and an organic ripple, never a rigid flat sail.
    ripple = (.006*np.sin(math.pi*q)[:, None] * np.sin(math.pi*t)[None, :]
              + .0017*np.sin(2.1*s)[:, None]*np.sin(2.*math.pi*t)[None, :])
    center += ripple[:, :, None]*nh[None, None, :]
    ds = np.gradient(center, axis=0)
    dt = np.gradient(center, axis=1)
    normals = np.cross(ds, dt)
    normals /= np.maximum(np.linalg.norm(normals, axis=2)[:, :, None], 1e-12)
    # Fine thickness, reducing near the margin while retaining a closed surface.
    half_thickness = thickness*.5*(.40+.60*(1.-t)**.55)
    upper = center+normals*half_thickness[None, :, None]
    lower = center-normals*half_thickness[None, :, None]
    verts = np.concatenate([upper.reshape(-1, 3), lower.reshape(-1, 3)])
    ids = np.arange(ns*nt).reshape(ns, nt)
    a = ids[:-1, :-1].reshape(-1)
    b = ids[1:, :-1].reshape(-1)
    c = ids[1:, 1:].reshape(-1)
    d = ids[:-1, 1:].reshape(-1)
    upper_faces = np.stack([a, b, c, d], axis=1)
    lower_faces = upper_faces[:, ::-1]+ns*nt
    # Clockwise boundary walk viewed from the lower face.
    boundary = np.concatenate([ids[:, 0], ids[-1, 1:], ids[-2::-1, -1], ids[0, -2:0:-1]])
    following = np.roll(boundary, -1)
    side_faces = np.stack([following, boundary, boundary+ns*nt, following+ns*nt], axis=1)
    faces = np.concatenate([upper_faces, lower_faces, side_faces])
    membrane = _mesh(name+"_membrane", verts, faces, collection, membrane_material)
    membrane["fin_name"] = name
    membrane["ray_count"] = ray_count
    membrane["spine_count"] = spines
    membrane["soft_ray_count"] = ray_count-spines
    membrane["geometry"] = "Closed thin membrane, curved radial corrugations, scalloped distal edge"
    membrane["anatomical_side"] = ("left" if name.endswith("left") else "right" if name.endswith("right") else "median")
    ray_verts, ray_faces = [], []
    for k in range(ray_count):
        path = _ray_path(roots[k], tips[k], bends[k])
        r = radius*(1.12 if k < spines else .78)
        _add_tube(ray_verts, ray_faces, path, r)
        # Soft rays bifurcate distally; principal hard spines remain unbranched.
        if branch and k >= spines and 0 < k < ray_count-1:
            split_t = .55 + .025*math.sin(k*1.7)
            branch_root = (roots[k]*(1.-split_t)+tips[k]*split_t+
                           math.sin(math.pi*split_t)*bends[k])
            for sign in (-1, 1):
                neighbor = tips[k+sign]
                branch_tip = tips[k]*.82+neighbor*.18
                branch_path = _ray_path(branch_root, branch_tip, bends[k]*.15, samples=17)
                _add_tube(ray_verts, ray_faces, branch_path, r*.46, sides=6)
    rays = _mesh(name+"_rays", ray_verts, ray_faces, collection, ray_material)
    for obj in (rays,):
        obj["fin_name"] = name
        obj["ray_count"] = ray_count
        obj["spine_count"] = spines
        obj["soft_ray_count"] = ray_count-spines
        obj["geometry"] = "Tapered modeled rays; branched soft rays; unbranched hard spines"
    return [membrane, rays]


def build_fins(collection, materials):
    """Build fins and return their Blender objects.

    Required materials: fin_olive, fin_orange, ray_dark, ray_orange.
    Dorsal XV + I,14; anal II,9; pectoral 13 each; pelvic I,5 each.
    Caudal 17 principal rays; body length and placement match the host scene.
    """
    out = []
    # The roots follow the actual host body profile rather than a straight bar.
    n = 15
    s = np.linspace(0., 1., n)
    x = .67-1.34*s
    z = .03+np.interp(x, PROFILE_X, PROFILE_Z)-.013
    roots = np.stack([x, .005*np.sin(s*math.pi), z], axis=1)
    height = np.interp(s, [0., .10, .26, .42, .60, .79, 1.], [.12, .32, .455, .49, .46, .34, .14])
    tips = roots+np.stack([-.075-.09*np.sin(math.pi*s), .010*np.sin(4.5*s), height], axis=1)
    bends = np.stack([-.027*np.sin(math.pi*s), .013*np.sin(3.7*s), .017*np.ones(n)], axis=1)
    out += _build_fin("Dorsal_1_spiny", roots, tips, bends, collection,
                      materials["fin_olive"], materials["ray_dark"], 15, [0, 1, 0],
                      scallop=.060, radius=.0090, branch=False)

    n = 15
    s = np.linspace(0., 1., n)
    x = -.73-.61*s
    z = .03+np.interp(x, PROFILE_X, PROFILE_Z)-.009
    roots = np.stack([x, .004*np.sin(3*s), z], axis=1)
    height = np.interp(s, [0., .16, .4, .72, 1.], [.15, .285, .30, .27, .105])
    tips = roots+np.stack([-.06-.13*np.sin(math.pi*s), -.012*np.sin(3*s), height], axis=1)
    bends = np.stack([-.022*np.ones(n), .009*np.sin(5*s), .012*np.ones(n)], axis=1)
    out += _build_fin("Dorsal_2_soft", roots, tips, bends, collection,
                      materials["fin_olive"], materials["ray_dark"], 1, [0, 1, 0],
                      scallop=.018, radius=.007)

    n = 11
    s = np.linspace(0., 1., n)
    x = -.65-.56*s
    z = .03-np.interp(x, PROFILE_X, PROFILE_Z)+.008
    roots = np.stack([x, .003*np.sin(s*3), z], axis=1)
    drop = np.interp(s, [0., .14, .32, .65, 1.], [.17, .29, .365, .31, .16])
    tips = roots+np.stack([-.11-.18*np.sin(math.pi*s), .006*np.sin(5*s), -drop], axis=1)
    bends = np.stack([-.025*np.ones(n), -.007*np.sin(3*s), -.015*np.ones(n)], axis=1)
    out += _build_fin("Anal", roots, tips, bends, collection,
                      materials["fin_orange"], materials["ray_orange"], 2, [0, 1, 0],
                      scallop=.024, radius=.0075)

    for side, side_name in [(-1., "left"), (1., "right")]:
        n = 13
        s = np.linspace(0., 1., n)
        roots = np.stack([.49-.035*s,
                          side*(.298+.025*np.sin(math.pi*s)),
                          -.003-.125*s], axis=1)
        length = .43+.36*np.sin(math.pi*s)
        tips = np.stack([.49-length*(.94+.05*np.sin(math.pi*s)),
                         side*(.47+.215*np.sin(math.pi*s)),
                         -.035-.37*s], axis=1)
        # Both fins have a gentle backward cup, with minute natural asymmetry.
        tips[:, 2] += side*.007*np.sin(math.pi*s)
        bends = np.stack([-.03*np.ones(n), side*.026*np.sin(math.pi*s),
                          -.012*np.ones(n)], axis=1)
        out += _build_fin("Pectoral_"+side_name, roots, tips, bends, collection,
                          materials["fin_olive"], materials["ray_dark"], 0,
                          [0, side*.72, -.70], scallop=.018, radius=.0061,
                          thickness=.0019)

        n = 6
        s = np.linspace(0., 1., n)
        roots = np.stack([.16-.12*s, side*(.145+.024*s), -.428-.01*s], axis=1)
        tips = np.array([[-.31, side*.275, -.805],
                         [-.46, side*.292, -.848],
                         [-.535, side*.303, -.825],
                         [-.51, side*.312, -.77],
                         [-.40, side*.295, -.681],
                         [-.245, side*.250, -.594]], dtype=np.float64)
        tips[:, 2] += side*.006*np.sin(math.pi*s)
        bends = np.stack([-.021*np.ones(n), side*.026*np.sin(math.pi*s),
                          -.021*np.ones(n)], axis=1)
        out += _build_fin("Pelvic_"+side_name, roots, tips, bends, collection,
                          materials["fin_orange"], materials["ray_orange"], 1,
                          [0, side, .15], scallop=.019, radius=.0074,
                          thickness=.0020)

    n = 17
    s = np.linspace(0., 1., n)
    roots = np.stack([-1.626+.049*abs(2*s-1),
                      .003*np.sin(2*math.pi*s), .03+.095*(1-2*s)], axis=1)
    # Rounded upper and lower lobes surround a shallow, unmistakable fork.
    controls = np.array([[-1.85, .003, .256],
                         [-2.13, .008, .475],
                         [-2.38, .006, .524],
                         [-2.422, .003, .449],
                         [-2.33, -.002, .210],
                         [-2.27, -.004, .035],
                         [-2.333, -.002, -.147],
                         [-2.431, .002, -.381],
                         [-2.394, .008, -.473],
                         [-2.15, .01, -.436],
                         [-1.854, .007, -.201]])
    tips = _smooth_interp(controls, s*(len(controls)-1))
    bends = np.stack([-.026*np.sin(math.pi*s), .018*np.sin(math.pi*s),
                      .012*np.sin(2*math.pi*s)], axis=1)
    out += _build_fin("Caudal_forked", roots, tips, bends, collection,
                      materials["fin_orange"], materials["ray_orange"], 0,
                      [0, 1, 0], scallop=.013, thickness=.0026, radius=.0080)
    for obj in out[-2:]:
        obj["principal_ray_count"] = 17
        obj["anatomy_note"] = "17 principal caudal rays; rounded forked tail; small procurrent rays not counted"
    return out
