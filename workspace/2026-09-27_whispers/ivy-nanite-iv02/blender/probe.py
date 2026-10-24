import bpy
print("VER", bpy.app.version_string)
c = bpy.data.hair_curves.new("t")
c.add_curves([3,4])
print("curves", len(c.curves), len(c.points), [a.name for a in c.attributes])
print("pos", [p.position[:] for p in c.points][:2])
a = c.attributes.new("g0", 'FLOAT', 'CURVE'); print("attr ok", a.domain)
ng = bpy.data.node_groups.new("x", 'GeometryNodeTree')
for t in ["GeometryNodeCurveToMesh","GeometryNodeResampleCurve","GeometryNodeCurveToPoints","GeometryNodeInstanceOnPoints","GeometryNodeCollectionInfo","GeometryNodeRealizeInstances","GeometryNodeStoreNamedAttribute","GeometryNodeSetMaterial","GeometryNodeSetShadeSmooth","GeometryNodeInputNamedAttribute","FunctionNodeRandomValue","FunctionNodeCombineColor","GeometryNodeMergeByDistance","GeometryNodeCurvePrimitiveCircle","GeometryNodeJoinGeometry","GeometryNodeSplineParameter","GeometryNodeDeleteGeometry","GeometryNodeInputID","GeometryNodeInputIndex","FunctionNodeCombineXYZ","ShaderNodeCombineXYZ","FunctionNodeRotateEuler","FunctionNodeEulerToRotation","GeometryNodeTransform","GeometryNodeSetPosition","GeometryNodeInputPosition","GeometryNodeTriangulate","GeometryNodeSetCurveRadius","GeometryNodeSplineLength","GeometryNodeInputNormal","GeometryNodeObjectInfo","GeometryNodeSeparateGeometry"]:
    try:
        n = ng.nodes.new(t); print("OK", t, [i.name for i in n.inputs][:9], "->", [o.name for o in n.outputs][:6])
    except Exception as e: print("NO", t, e)
p = bpy.ops.export_scene.fbx.get_rna_type().properties
print("FBX", [k.identifier for k in p])
print("ENG", [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items])
