"""IV02 S3: build the editable ivy source (curves + Geometry Nodes + leaf sources),
realize a triangulated export copy, bake the R cavity mask and export FBXs.

  blender --factory-startup --disable-autoexec -b --python build_ivy.py -- <ivy_IV02 root>

Deterministic (seed 24024). Saves only IV02_Ivy_Prototype.blend (no hotel data).
Patch frame: +X away from the wall, +Z up, width along Y; origin = lower central
attachment point on plane X = 0. Units: 1 BU = 1 m.
"""
import bpy, bmesh, sys, json, math, random, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(sys.argv[sys.argv.index('--') + 1])
sys.path.insert(0, str(ROOT / 'scripts'))
import ivy_shapes as S

SEED = 24024
RNG = random.Random(SEED)
TEX = ROOT / 'textures'; EXP = ROOT / 'exports'; QA = ROOT / 'qa'
BLEND = ROOT / 'IV02_Ivy_Prototype.blend'
NOMINAL = dict(y=(-0.5, 0.5), z=(0.0, 2.0), x=(0.0, 0.25))
STEM_REGION = dict(y=(-0.38, 0.38), z=(0.0, 1.86))

# ---------------------------------------------------------------- scene reset
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images):
    for d in list(block):
        block.remove(d)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1.0

COLL = {}
for name in ('IV02_SourceCurves', 'IV02_LeafSources', 'IV02_GrowthGN', 'IV02_Export'):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); COLL[name] = c

# ---------------------------------------------------------------- material
def load(fn, data):
    img = bpy.data.images.load(str(TEX / fn), check_existing=True)
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    img.pack()
    return img

mat = bpy.data.materials.new('IvyAtlas')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
t_bc = nt.nodes.new('ShaderNodeTexImage'); t_bc.image = load('T_Ivy_Atlas_BaseColor.png', False)
t_n = nt.nodes.new('ShaderNodeTexImage'); t_n.image = load('T_Ivy_Atlas_Normal.png', True)
t_r = nt.nodes.new('ShaderNodeTexImage'); t_r.image = load('T_Ivy_Atlas_Roughness.png', True)
for t in (t_bc, t_n, t_r):
    t.interpolation = 'Linear'
    nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
# Artistic AO from vertex colour R (preview only; never a substitute for cast shadows).
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(vc.outputs['Color'], sep.inputs['Color'])
ao = nt.nodes.new('ShaderNodeMapRange'); ao.inputs['To Min'].default_value = 0.55
nt.links.new(sep.outputs['Red'], ao.inputs['Value'])
mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
mul.inputs['Factor'].default_value = 1.0
nt.links.new(t_bc.outputs['Color'], mul.inputs['A']); nt.links.new(ao.outputs['Result'], mul.inputs['B'])
nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = 'UVMap'
nt.links.new(t_n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
nt.links.new(t_r.outputs['Color'], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.0
mat['IV02_maps'] = 'BaseColor sRGB; Normal linear tangent OpenGL +Y (Unreal: Flip Green); Roughness linear. Opaque, no alpha.'
mat['IV02_vertex_color'] = 'Color CORNER RGBA: R cavity/AO (0 occluded,1 open), G growth (0 root,1 mature), B tip (0 base,1 tip), A=1'

# ---------------------------------------------------------------- leaf sources
LEAF_SIZE = {'L0': (0.078, 0.046), 'L1': (0.083, 0.052), 'L2': (0.074, 0.042), 'L3': (0.052, 0.030)}  # blade length, petiole length
LEAN = 0.17  # blade tips lean outward (rad) so leaves catch light and stay off the wall

def bezier(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + p2 * t * t

def leaf_source(name):
    L, pl = LEAF_SIZE[name]
    outline = S.VARIANTS[name]
    uvf = S.leaf_uv_map(name)
    hb = S.HUB
    bmax = max(p[1] for p in outline)
    J = Vector((pl * 0.58, 0.0, pl * 0.80))           # petiole end = blade hub
    ctrl = Vector((pl * 0.50, 0.0, pl * 0.12))        # petiole leaves the stem outward, then arches upward
    verts, faces, uvs, tips = [], [], [], []           # uvs/tips per vertex (no seams inside a part)

    def blade_pt(a, b):
        u_ = a * L; w_ = (b - hb[1]) * L
        cup = L * (0.065 * (1 - min(1, (a / 0.62) ** 2)) - 0.040 * ((b - 0.55) / 0.45) ** 2
                   + 0.010 * math.exp(-(a / 0.05) ** 2))
        x = J.x + cup + max(w_, 0) * math.tan(LEAN)
        return Vector((x, u_, J.z + w_))

    def tipv(b):
        return 0.15 + 0.85 * max(0.0, min(1.0, (b - 0.09) / (bmax - 0.09)))
    # blade: hub, mid ring, outline
    n = len(outline)
    hub_i = len(verts); verts.append(blade_pt(*hb)); uvs.append(uvf(*hb)); tips.append(tipv(hb[1]))
    ring_i = len(verts)
    for a, b in outline:
        ma, mb = hb[0] + 0.5 * (a - hb[0]), hb[1] + 0.5 * (b - hb[1])
        verts.append(blade_pt(ma, mb)); uvs.append(uvf(ma, mb)); tips.append(tipv(mb))
    out_i = len(verts)
    for a, b in outline:
        verts.append(blade_pt(a, b)); uvs.append(uvf(a, b)); tips.append(tipv(b))
    for i in range(n):
        j = (i + 1) % n
        faces.append((hub_i, ring_i + i, ring_i + j))
        faces.append((ring_i + i, out_i + i, out_i + j, ring_i + j))
    blade_faces = len(faces)
    # petiole: 4-sided tube, 4 rings along a quadratic arc, no caps
    sides, rings = 4, 4
    p_i = len(verts)
    for r in range(rings):
        t = r / (rings - 1)
        c = bezier(Vector((0, 0, 0)), ctrl, J, t)
        tan = (bezier(Vector((0, 0, 0)), ctrl, J, min(1, t + 0.01)) - bezier(Vector((0, 0, 0)), ctrl, J, max(0, t - 0.01))).normalized()
        side = Vector((0, 1, 0)); other = tan.cross(side).normalized()
        rad = 0.0013 * (1 - 0.35 * t)
        for k in range(sides):
            ang = 2 * math.pi * k / sides
            verts.append(c + rad * (math.cos(ang) * side + math.sin(ang) * other))
            uvs.append(S.strip_uv('Petiole', k / sides, t)); tips.append(0.15 * t)
    for r in range(rings - 1):
        for k in range(sides):
            a0 = p_i + r * sides + k; a1 = p_i + r * sides + (k + 1) % sides
            faces.append((a0, a1, a1 + sides, a0 + sides))
    me = bpy.data.meshes.new(f'IV02_Leaf_{name}')
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    # blade must face +X (away from the wall)
    nx = sum(me.polygons[i].normal.x * me.polygons[i].area for i in range(blade_faces))
    if nx < 0:
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in range(blade_faces)])
        bm.to_mesh(me); bm.free()
    # petiole tube must face outward from its axis
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    at = me.attributes.new('ivy_tip', 'FLOAT', 'POINT')
    at.data.foreach_set('value', tips)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(f'IV02_Leaf_{name}', me)
    COLL['IV02_LeafSources'].objects.link(ob)
    return ob, len(me.polygons), sum(len(p.vertices) - 2 for p in me.polygons)

leaf_rows = {}
for k in ('L0', 'L1', 'L2', 'L3'):
    ob, nf, nt_ = leaf_source(k)
    ob.location = (0, -1.0 - 0.3 * int(k[1]), 0)   # displayed beside the patch; GN resets children
    leaf_rows[k] = {'object': ob.name, 'faces': nf, 'triangles': nt_, 'blade_length_m': LEAF_SIZE[k][0],
                    'petiole_length_m': LEAF_SIZE[k][1]}

# ---------------------------------------------------------------- growth curves
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

curves_data = []   # list of dict(points=[Vector], radius=[...], offset=float, woody=0/1, leafy=[...])

def grow(start, direction, length, r0, r1, step=0.035, wander=0.35, target=None, steer=0.25, offset=0.0, woody=0, leafy_from=0.02, x_lift=0.0):
    """Grow one stem in the wall plane: smooth noisy heading, optionally steered toward a target."""
    pts = [start.copy()]
    d = Vector(direction).normalized()
    p = start.copy()
    n = max(2, int(length / step))
    for i in range(n):
        if woody and offset == 0.0 and i < 2:
            p = p + Vector((0, 0, step)); pts.append(p.copy()); continue
        ang = RNG.gauss(0, wander) * 0.6
        ca, sa = math.cos(ang), math.sin(ang)
        d = Vector((0, d.y * ca - d.z * sa, d.y * sa + d.z * ca))
        if target is not None:
            to = Vector((0, target[0], target[1])) - Vector((0, p.y, p.z))
            if to.length < step * 2:
                break
            d = (d + to.normalized() * steer).normalized()
        q = p + d * step
        if not (STEM_REGION['y'][0] <= q.y <= STEM_REGION['y'][1] and STEM_REGION['z'][0] <= q.z <= STEM_REGION['z'][1]):
            break
        p = q; pts.append(p.copy())
    m = len(pts)
    radius = [r0 + (r1 - r0) * (i / (m - 1)) for i in range(m)]
    for i, r in enumerate(radius):
        pts[i].x = r + 0.0015 + x_lift          # centreline sits just off the wall plane X = 0
    arc = [0.0]
    for i in range(1, m):
        arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    leafy = [1.0 if a >= leafy_from else 0.0 for a in arc]
    c = dict(points=pts, radius=radius, offset=offset, woody=woody, leafy=leafy, arc=arc)
    curves_data.append(c)
    return c

def point_at(c, frac):
    i = min(len(c['points']) - 1, int(frac * (len(c['points']) - 1)))
    return i, c['points'][i], c['offset'] + c['arc'][i], c['radius'][i]

# three woody stems from one root, steered to left / centre / right crowns
A = grow(Vector((0, 0.0, 0.0)), (0, 0.0, 1), 2.6, 0.0085, 0.0030, wander=0.26, target=(0.06, 1.86), steer=0.09, woody=1, leafy_from=0.30)
i, p, off, r = point_at(A, 0.05)
B = grow(Vector((0, p.y, p.z)), (0, -0.7, 1), 2.4, 0.0060, 0.0026, wander=0.22, target=(-0.33, 1.70), steer=0.12, offset=off, woody=1, leafy_from=0.12, x_lift=0.0015)
i, p, off, r = point_at(A, 0.12)
C = grow(Vector((0, p.y, p.z)), (0, 0.7, 1), 2.2, 0.0052, 0.0024, wander=0.22, target=(0.33, 1.58), steer=0.12, offset=off, woody=1, leafy_from=0.10, x_lift=0.0030)
side = 1
for stem in (A, B, C):
    frac = 0.12
    while frac < 0.95:
        i, p, off, r = point_at(stem, frac)
        # branches spread sideways and upward, alternating, aimed at a lateral point
        ty = clamp(p.y + side * RNG.uniform(0.18, 0.34), -0.37, 0.37)
        tz = clamp(p.z + RNG.uniform(0.08, 0.30), 0.1, 1.86)
        L = RNG.uniform(0.20, 0.42) * (1.0 - 0.25 * frac)
        dirv = Vector((0, ty - p.y, tz - p.z)).normalized()
        br = grow(Vector((0, p.y, p.z)), dirv, L, min(r * 0.75, 0.0034), 0.0014,
                  wander=0.30, target=(ty, tz), steer=0.10, offset=off, x_lift=r + RNG.uniform(0.0005, 0.0025))
        if RNG.random() < 0.55 and len(br['points']) > 5:
            j, q, off2, r2 = point_at(br, RNG.uniform(0.35, 0.6))
            ty2 = clamp(q.y + side * RNG.uniform(-0.05, 0.15), -0.37, 0.37); tz2 = clamp(q.z + RNG.uniform(0.10, 0.22), 0.1, 1.86)
            grow(Vector((0, q.y, q.z)), Vector((0, ty2 - q.y, tz2 - q.z)).normalized(), L * 0.55, min(r2 * 0.85, 0.0022), 0.0011,
                 wander=0.35, target=(ty2, tz2), steer=0.10, offset=off2, x_lift=br['points'][j].x + RNG.uniform(0.0005, 0.002))
        side *= -1
        frac += RNG.uniform(0.06, 0.10)

hc = bpy.data.hair_curves.new('IV02_Stems')
hc.add_curves([len(c['points']) for c in curves_data])
flat_pts = [p for c in curves_data for p in c['points']]
for k, pnt in enumerate(hc.points):
    pnt.position = flat_pts[k]
def attr(name, typ, dom, vals):
    a = hc.attributes.get(name) or hc.attributes.new(name, typ, dom)
    a.data.foreach_set('value', vals)
attr('radius', 'FLOAT', 'POINT', [r for c in curves_data for r in c['radius']])
attr('ivy_leafy', 'FLOAT', 'POINT', [v for c in curves_data for v in c['leafy']])
attr('ivy_root_offset', 'FLOAT', 'CURVE', [c['offset'] for c in curves_data])
attr('ivy_woody', 'FLOAT', 'CURVE', [float(c['woody']) for c in curves_data])
# poly curves: the authored points are the control points (no hidden Catmull-Rom overshoot)
hc.set_types(type='CATMULL_ROM')   # smooth interpolating curves; set through the API so cached type counts stay valid
max_path = max(c['offset'] + c['arc'][-1] for c in curves_data)
stems_ob = bpy.data.objects.new('IV02_Stems', hc)
COLL['IV02_SourceCurves'].objects.link(stems_ob)

# ---------------------------------------------------------------- Geometry Nodes
ng = bpy.data.node_groups.new('IV02_IvyGrowth', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
IN = {}
for nm_, st, dv in (('Seed', 'NodeSocketInt', SEED),
                    ('Stem Segment', 'NodeSocketFloat', 0.025), ('Leaf Spacing', 'NodeSocketFloat', 0.022),
                    ('Leaf Density', 'NodeSocketFloat', 0.95), ('Leaf Merge Distance', 'NodeSocketFloat', 0.027),
                    ('Max Path', 'NodeSocketFloat', max_path), ('Young Tip Threshold', 'NodeSocketFloat', 0.85)):
    s = ng.interface.new_socket(nm_, in_out='INPUT', socket_type=st)
    if dv is not None:
        s.default_value = dv
    IN[nm_] = s
N_ = ng.nodes; Lk = ng.links
gi = N_.new('NodeGroupInput'); go = N_.new('NodeGroupOutput')

def node(t, **props):
    n = N_.new(t)
    for k, v in props.items():
        setattr(n, k, v)
    return n

def setin(n, name, value):
    sock = n.inputs[name]
    try:
        sock.default_value = value
    except TypeError:
        sock.default_value = value.upper()

def math_(op, a, b=None, c=None):
    m = node('ShaderNodeMath', operation=op)
    for idx, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[idx].default_value = v
        else:
            Lk.new(v, m.inputs[idx])
    return m.outputs[0]

def named(name):
    n = node('GeometryNodeInputNamedAttribute', data_type='FLOAT'); n.inputs['Name'].default_value = name
    return n.outputs['Attribute']

def store(geo, name, dtype, domain, value):
    n = node('GeometryNodeStoreNamedAttribute', data_type=dtype, domain=domain)
    n.inputs['Name'].default_value = name
    Lk.new(geo, n.inputs['Geometry']); Lk.new(value, n.inputs['Value'])
    return n.outputs['Geometry']

def rand(lo, hi, seed_off):
    n = node('FunctionNodeRandomValue', data_type='FLOAT')
    n.inputs['Min'].default_value = lo; n.inputs['Max'].default_value = hi
    s = math_('ADD', gi.outputs['Seed'], seed_off)
    Lk.new(s, n.inputs['Seed'])
    return n.outputs['Value']

oi = node('GeometryNodeObjectInfo', transform_space='RELATIVE'); oi.inputs['Object'].default_value = stems_ob  # source curves
rs = node('GeometryNodeResampleCurve'); Lk.new(oi.outputs['Geometry'], rs.inputs['Curve'])
setin(rs, 'Mode', 'Length'); Lk.new(gi.outputs['Stem Segment'], rs.inputs['Length'])
sp = node('GeometryNodeSplineParameter')
growth = math_('DIVIDE', math_('ADD', named('ivy_root_offset'), sp.outputs['Length']), gi.outputs['Max Path'])
g1 = store(rs.outputs['Curve'], 'ivy_growth', 'FLOAT', 'POINT', growth)
sp2 = node('GeometryNodeSplineParameter')
curve = store(g1, 'ivy_tip', 'FLOAT', 'POINT', sp2.outputs['Factor'])

# stems: tube sweep with a seamless mirrored UV around the circumference
circ = node('GeometryNodeCurvePrimitiveCircle', mode='RADIUS'); circ.inputs['Resolution'].default_value = 6
circ.inputs['Radius'].default_value = 1.0
sp3 = node('GeometryNodeSplineParameter')
prof = store(circ.outputs['Curve'], 'ivy_u', 'FLOAT', 'POINT', sp3.outputs['Factor'])
c2m = node('GeometryNodeCurveToMesh'); Lk.new(curve, c2m.inputs['Curve']); Lk.new(prof, c2m.inputs['Profile Curve'])
rad = node('GeometryNodeInputRadius'); Lk.new(rad.outputs[0], c2m.inputs['Scale'])
c2m.inputs['Fill Caps'].default_value = False
mirror = math_('SUBTRACT', 0.5, math_('MULTIPLY', 0.5, math_('COSINE', math_('MULTIPLY', named('ivy_u'), 2 * math.pi))))
wu0, wv0, wu1, wv1 = S.inset(S.CELLS['Woody']); bu0, bv0, bu1, bv1 = S.inset(S.CELLS['Branch'])
woody = named('ivy_woody')
u0 = math_('ADD', bu0, math_('MULTIPLY', woody, wu0 - bu0))
v0 = math_('ADD', bv0, math_('MULTIPLY', woody, wv0 - bv0))
uu = math_('ADD', u0, math_('MULTIPLY', mirror, wu1 - wu0))
vv = math_('ADD', v0, math_('MULTIPLY', named('ivy_tip'), wv1 - wv0))
cxyz = node('ShaderNodeCombineXYZ'); Lk.new(uu, cxyz.inputs['X']); Lk.new(vv, cxyz.inputs['Y'])
stems_uv = store(c2m.outputs['Mesh'], 'UVMap', 'FLOAT2', 'CORNER', cxyz.outputs['Vector'])
smat = node('GeometryNodeSetMaterial'); Lk.new(stems_uv, smat.inputs['Geometry']); smat.inputs['Material'].default_value = mat

# leaves: points along every stem, thinned, merged, instanced from the leaf sources
c2p = node('GeometryNodeCurveToPoints', mode='LENGTH'); Lk.new(curve, c2p.inputs['Curve'])
Lk.new(gi.outputs['Leaf Spacing'], c2p.inputs['Length'])
keep = math_('LESS_THAN', rand(0.0, 1.0, 11), math_('MULTIPLY', gi.outputs['Leaf Density'], named('ivy_leafy')))
dele = node('GeometryNodeDeleteGeometry', domain='POINT'); Lk.new(c2p.outputs['Points'], dele.inputs['Geometry'])
Lk.new(math_('SUBTRACT', 1.0, keep), dele.inputs['Selection'])
eps = node('GeometryNodeCurveEndpointSelection'); eps.inputs['Start Size'].default_value = 0; eps.inputs['End Size'].default_value = 1
sep_end = node('GeometryNodeSeparateGeometry', domain='POINT'); Lk.new(curve, sep_end.inputs['Geometry']); Lk.new(eps.outputs[0], sep_end.inputs['Selection'])
endpts = node('GeometryNodeCurveToPoints', mode='EVALUATED'); Lk.new(sep_end.outputs['Selection'], endpts.inputs['Curve'])
jpts = node('GeometryNodeJoinGeometry'); Lk.new(endpts.outputs['Points'], jpts.inputs['Geometry']); Lk.new(dele.outputs['Geometry'], jpts.inputs['Geometry'])
mbd = node('GeometryNodeMergeByDistance'); Lk.new(jpts.outputs['Geometry'], mbd.inputs['Geometry'])
Lk.new(gi.outputs['Leaf Merge Distance'], mbd.inputs['Distance'])
ptip_geo = store(mbd.outputs['Geometry'], 'ivy_ptip', 'FLOAT', 'POINT', named('ivy_tip'))  # stem tip value carried by each leaf point
tip = named('ivy_ptip')
young = math_('GREATER_THAN', tip, gi.outputs['Young Tip Threshold'])
idx = math_('ADD', math_('MULTIPLY', young, 3.0), math_('MULTIPLY', math_('SUBTRACT', 1.0, young), math_('FLOOR', rand(0.0, 2.999, 12))))
eul = node('ShaderNodeCombineXYZ')
Lk.new(rand(-2.3, 2.3, 13), eul.inputs['X']); Lk.new(rand(-0.18, 0.06, 14), eul.inputs['Y']); Lk.new(rand(-0.28, 0.28, 15), eul.inputs['Z'])
e2r = node('FunctionNodeEulerToRotation'); Lk.new(eul.outputs['Vector'], e2r.inputs['Euler'])
scl = math_('MULTIPLY', rand(0.82, 1.12, 16), math_('SUBTRACT', 1.0, math_('MULTIPLY', 0.30, tip)))
rm1 = node('GeometryNodeRemoveAttribute'); Lk.new(ptip_geo, rm1.inputs['Geometry']); rm1.inputs['Name'].default_value = 'ivy_tip'
rm2 = node('GeometryNodeRemoveAttribute'); Lk.new(rm1.outputs['Geometry'], rm2.inputs['Geometry']); rm2.inputs['Name'].default_value = 'radius'
ci = node('GeometryNodeCollectionInfo', transform_space='ORIGINAL'); ci.inputs['Collection'].default_value = COLL['IV02_LeafSources']
ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
iop = node('GeometryNodeInstanceOnPoints'); Lk.new(rm2.outputs['Geometry'], iop.inputs['Points'])
Lk.new(ci.outputs['Instances'], iop.inputs['Instance']); iop.inputs['Pick Instance'].default_value = True
Lk.new(idx, iop.inputs['Instance Index']); Lk.new(e2r.outputs['Rotation'], iop.inputs['Rotation']); Lk.new(scl, iop.inputs['Scale'])
real = node('GeometryNodeRealizeInstances'); Lk.new(iop.outputs['Instances'], real.inputs['Geometry'])

join = node('GeometryNodeJoinGeometry'); Lk.new(real.outputs['Geometry'], join.inputs['Geometry']); Lk.new(smat.outputs['Geometry'], join.inputs['Geometry'])
smooth = node('GeometryNodeSetShadeSmooth'); Lk.new(join.outputs['Geometry'], smooth.inputs['Mesh']); smooth.inputs['Shade Smooth'].default_value = True
col = node('FunctionNodeCombineColor'); col.inputs['Red'].default_value = 1.0; col.inputs['Alpha'].default_value = 1.0
Lk.new(named('ivy_growth'), col.inputs['Green']); Lk.new(named('ivy_tip'), col.inputs['Blue'])
final = store(smooth.outputs['Mesh'], 'Color', 'FLOAT_COLOR', 'CORNER', col.outputs['Color'])
Lk.new(final, go.inputs['Geometry'])

gn_me = bpy.data.meshes.new('IV02_IvyPatch_GN')
gn_ob = bpy.data.objects.new('IV02_IvyPatch_GN', gn_me)
COLL['IV02_GrowthGN'].objects.link(gn_ob)
mod = gn_ob.modifiers.new('IV02_IvyGrowth', 'NODES'); mod.node_group = ng
ids = {it.name: it.identifier for it in ng.interface.items_tree if getattr(it, 'in_out', None) == 'INPUT'}
# leaf sources are kept as editable inputs but hidden from render/view so only the instanced patch shows
vl = bpy.context.view_layer
for lc in vl.layer_collection.children:
    if lc.name == 'IV02_LeafSources':
        lc.exclude = True
stems_ob.hide_render = True
bpy.context.view_layer.update()

# ---------------------------------------------------------------- export copy
dg = bpy.context.evaluated_depsgraph_get()
ev = gn_ob.evaluated_get(dg)
src_me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
gn_faces = len(src_me.polygons); gn_tris = sum(len(p.vertices) - 2 for p in src_me.polygons)
exp_me = src_me; exp_me.name = 'SM_Ivy_WallPatch_Prototype'
bm = bmesh.new(); bm.from_mesh(exp_me)
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(exp_me); bm.free()
exp_ob = bpy.data.objects.new('SM_Ivy_WallPatch_Prototype', exp_me)
COLL['IV02_Export'].objects.link(exp_ob)

# classify parts by UV island
uvl = exp_me.uv_layers['UVMap']
def island(uv):
    for k, (a, b, c, d) in S.CELLS.items():
        if a <= uv[0] <= c and b <= uv[1] <= d:
            return k
    return None
poly_part = []
for p in exp_me.polygons:
    poly_part.append(island(uvl.data[p.loop_indices[0]].uv))

# R cavity bake: cosine hemisphere rays (fixed set, seed 24024) against the patch and the wall plane X = 0
verts = [v.co.copy() for v in exp_me.vertices]
bvh = BVHTree.FromPolygons(verts, [p.vertices for p in exp_me.polygons])
rr = random.Random(SEED)
DIRS = []
for _ in range(32):
    u1, u2 = rr.random(), rr.random()
    r_, th = math.sqrt(u1), 2 * math.pi * u2
    DIRS.append(Vector((r_ * math.cos(th), r_ * math.sin(th), math.sqrt(max(0, 1 - u1)))))
vert_is_blade = [False] * len(verts)
for p, part in zip(exp_me.polygons, poly_part):
    if part and part.startswith('L'):
        for vi in p.vertices:
            vert_is_blade[vi] = True
MAXD = 0.08
cav = []
for vi, v in enumerate(exp_me.vertices):
    n = v.normal.copy()
    if vert_is_blade[vi] and n.x < 0:
        n = -n
    t = n.orthogonal().normalized(); b2 = n.cross(t)
    o = v.co + n * 0.0015
    hit = 0
    for d in DIRS:
        w = (t * d.x + b2 * d.y + n * d.z).normalized()
        if w.x < 0 and o.x / -w.x <= MAXD:
            hit += 1; continue
        if bvh.ray_cast(o, w, MAXD)[0] is not None:
            hit += 1
    cav.append(1.0 - hit / len(DIRS))
colattr = exp_me.color_attributes['Color']
cdata = [0.0] * (len(exp_me.loops) * 4)
colattr.data.foreach_get('color', cdata)
for li, loop in enumerate(exp_me.loops):
    cdata[li * 4] = cav[loop.vertex_index]
colattr.data.foreach_set('color', cdata)
exp_me.color_attributes.active_color = colattr
exp_me.color_attributes.render_color_index = list(exp_me.color_attributes).index(colattr)
for a in [a.name for a in exp_me.attributes]:
    if a.startswith('ivy_') or a in ('radius',):
        exp_me.attributes.remove(exp_me.attributes[a])
exp_me.materials.clear(); exp_me.materials.append(mat)
for p in exp_me.polygons:
    p.material_index = 0
# attribute removal reallocates custom-data layers: re-fetch every layer wrapper
uvl = exp_me.uv_layers['UVMap']
colattr = exp_me.color_attributes['Color']

# ---------------------------------------------------------------- axis markers (diagnostic only)
def marker(name, loc, s=0.01):
    me = bpy.data.meshes.new(name)
    v = [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]
    f = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    me.from_pydata(v, [], f); me.update()
    ob = bpy.data.objects.new(name, me); ob.location = loc
    COLL['IV02_Export'].objects.link(ob)
    return ob
markers = [marker('IV02_Axis_Origin', (0, 0, 0)), marker('IV02_Axis_PlusX_0p25m', (0.25, 0, 0)),
           marker('IV02_Axis_PlusY_0p5m', (0, 0.5, 0)), marker('IV02_Axis_PlusZ_2m', (0, 0, 2.0))]

FBX = dict(object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
           axis_forward='-Y', axis_up='Z', bake_space_transform=False, use_mesh_modifiers=True,
           mesh_smooth_type='FACE', use_tspace=True, use_triangles=True, colors_type='LINEAR',
           prioritize_active_color=True, add_leaf_bones=False, bake_anim=False, use_custom_props=False,
           path_mode='STRIP', embed_textures=False, use_selection=True)

def export(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(path), **FBX)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
print('IV02_SAVED_BEFORE_EXPORT', flush=True)
if '--no-export' in sys.argv: raise SystemExit
fbx_ivy = export([exp_ob], EXP / 'SM_Ivy_WallPatch_Prototype.fbx')
fbx_axes = export(markers, EXP / 'IV02_AxisMarkers.fbx')

# ---------------------------------------------------------------- measurements
co = [v.co for v in exp_me.vertices]
lo = [min(c[i] for c in co) for i in range(3)]; hi = [max(c[i] for c in co) for i in range(3)]
from collections import Counter
part_tris = Counter(poly_part)
uv_ok = {}
for k in S.CELLS:
    iu0, iv0, iu1, iv1 = S.inset(S.CELLS[k], 16)
    sel = [uvl.data[li].uv for p, part in zip(exp_me.polygons, poly_part) if part == k for li in p.loop_indices]
    uv_ok[k] = {'corners': len(sel), 'all_inside_16px_inset': all(iu0 - 1e-6 <= u.x <= iu1 + 1e-6 and iv0 - 1e-6 <= u.y <= iv1 + 1e-6 for u in sel)}
cd = [0.0] * (len(exp_me.loops) * 4); exp_me.color_attributes['Color'].data.foreach_get('color', cd)
chan = {c: cd[i::4] for i, c in enumerate('RGBA')}
def stats(v):
    v = sorted(v); n = len(v)
    return {'min': v[0], 'p05': v[int(n * .05)], 'median': v[n // 2], 'p95': v[int(n * .95)], 'max': v[-1], 'mean': sum(v) / n}
def corr(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else None
hist = {c: [0] * 10 for c in 'RGB'}
for c in 'RGB':
    for x in chan[c]:
        hist[c][min(9, int(x * 10))] += 1
leaf_count = sum(1 for p in exp_me.polygons) and None
# buried leaves: blade triangles whose centroid is covered from +X and both 35-degree obliques
covered = 0; blade_tris = 0
obl = [Vector((1, 0, 0)), Vector((math.cos(0.61), math.sin(0.61), 0)), Vector((math.cos(0.61), -math.sin(0.61), 0)),
       Vector((math.cos(0.61), 0, math.sin(0.61)))]
for p, part in zip(exp_me.polygons, poly_part):
    if not (part and part.startswith('L')):
        continue
    blade_tris += 1
    c = p.center + p.normal * 0.0005 * (1 if p.normal.x >= 0 else -1)
    if all(bvh.ray_cast(c + d * 0.0008, d, 0.5)[0] is not None for d in obl):
        covered += 1
stem_tris = part_tris.get('Woody', 0) + part_tris.get('Branch', 0)
# stem radius check from the actual mesh (woody root ring)
root_ring = [v.co for v, p in zip(exp_me.vertices, range(len(exp_me.vertices))) if v.co.z < 0.0005]
root_r = max(((c.x - 0.0085 - 0.0015) ** 2 + c.y ** 2) ** 0.5 for c in root_ring) if root_ring else None
m = {
    'revision': 'IV02-r1', 'seed': SEED, 'blender': bpy.app.version_string,
    'source_blend': str(BLEND),
    'collections': {k: [o.name for o in c.objects] for k, c in COLL.items()},
    'curves': {'object': stems_ob.name, 'type': stems_ob.type, 'curve_count': len(hc.curves), 'point_count': len(hc.points),
               'woody_curves': sum(c['woody'] for c in curves_data), 'max_path_m': max_path,
               'stem_region_m': STEM_REGION},
    'geometry_nodes': {'group': ng.name, 'modifier_object': gn_ob.name, 'inputs': {k: ng.interface.items_tree[k].default_value for k in ids if hasattr(ng.interface.items_tree[k], 'default_value')}, 'node_inputs': {'Object Info': stems_ob.name, 'Collection Info': 'IV02_LeafSources', 'Set Material': mat.name},
                       'evaluated_faces': gn_faces, 'evaluated_triangles': gn_tris},
    'leaf_sources': leaf_rows,
    'export_mesh': {'object': exp_ob.name, 'vertices': len(exp_me.vertices), 'triangles': len(exp_me.polygons),
                    'loops': len(exp_me.loops), 'triangles_by_island': dict(part_tris),
                    'leaf_instances_estimate': round(sum(v for k, v in part_tris.items() if k and k.startswith('L')) / (leaf_rows['L0']['triangles'] - 24)),
                    'blade_triangles': blade_tris, 'petiole_triangles': part_tris.get('Petiole', 0), 'stem_triangles': stem_tris,
                    'material_slots': [s.name for s in exp_me.materials],
                    'uv_layers': [l.name for l in exp_me.uv_layers],
                    'color_attributes': [(a.name, a.domain, a.data_type) for a in exp_me.color_attributes],
                    'tight_min_m': lo, 'tight_max_m': hi, 'tight_size_cm': [(hi[i] - lo[i]) * 100 for i in range(3)],
                    'nominal_m': NOMINAL,
                    'within_nominal': lo[0] >= -1e-6 and hi[0] <= 0.25 and lo[1] >= -0.5 and hi[1] <= 0.5 and lo[2] >= -1e-4 and hi[2] <= 2.0,
                    'vertices_behind_wall_plane': sum(1 for c in co if c.x < -1e-6),
                    'pivot_object_origin_m': list(exp_ob.location), 'object_matrix_identity': exp_ob.matrix_world == Matrix.Identity(4),
                    'root_ring_radius_m_measured': root_r,
                    'blade_triangles_covered_from_front_and_obliques': covered,
                    'blade_covered_fraction': covered / blade_tris if blade_tris else None,
                    'uv_island_check': uv_ok,
                    'vertex_color': {c: stats(chan[c]) for c in 'RGBA'},
                    'vertex_color_hist10': hist,
                    'channel_correlation': {'RG': corr(chan['R'], chan['G']), 'RB': corr(chan['R'], chan['B']), 'GB': corr(chan['G'], chan['B'])},
                    'collision': 'none (no UCX objects; no collision in export)'},
    'cavity_bake': {'rays': len(DIRS), 'max_distance_m': MAXD, 'occluders': 'patch BVH + wall plane X=0',
                    'blade_hemisphere': 'oriented to +X (front face)', 'domain': 'per vertex, written to every corner'},
    'fbx': {'ivy': fbx_ivy, 'axis_markers': fbx_axes, 'settings': {k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX.items()}},
    'axis_markers_m': {o.name: list(o.location) for o in markers},
}
# reference data for the clean round-trip comparison (per corner)
ref = {'positions': [list(exp_me.vertices[l.vertex_index].co) for l in exp_me.loops],
       'normals': [list(n.vector) for n in exp_me.corner_normals],
       'uv': [list(uvl.data[i].uv) for i in range(len(exp_me.loops))],
       'color': [cd[i * 4:i * 4 + 4] for i in range(len(exp_me.loops))]}
(QA / 'ivy_export_reference.json').write_text(json.dumps(ref), encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
m['blend'] = {'path': str(BLEND), 'bytes': BLEND.stat().st_size, 'sha256': hashlib.sha256(BLEND.read_bytes()).hexdigest()}
(QA / 'ivy_build.json').write_text(json.dumps(m, indent=1, default=str), encoding='utf-8')
print('IV02_IVY_BUILD', m['export_mesh']['triangles'], m['export_mesh']['tight_size_cm'], m['export_mesh']['within_nominal'],
      m['export_mesh']['blade_covered_fraction'], m['channel_correlation'] if 'channel_correlation' in m else m['export_mesh']['channel_correlation'])

# release Python wrappers of mesh data before Blender tears down (avoids a crash at exit)
del co, verts, ref, cd, chan, uvl, colattr, exp_me, src_me, bvh
import gc; gc.collect()
