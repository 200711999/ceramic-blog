#!/usr/bin/env python3
"""
Blender 红釉双耳炉建模脚本（兼容 Blender 5.1.x）
=================================================
在项目根目录执行:
    blender --background --python scripts/blender_censer.py

Windows:
    "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python scripts\blender_censer.py
"""

import bpy
import bmesh
import math


def clear_scene():
    # background 模式下不能使用 select_all operator，直接删对象
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # 清理无引用数据块
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def _safe_set_input(node, possible_names, value):
    for name in possible_names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False


# =====================================================================
# 1. 炉身主体（Spin 旋转成型）
# =====================================================================

BODY_PROFILE = [
    (0.000, 0.000),
    (0.095, 0.000),
    (0.100, 0.015),
    (0.105, 0.025),
    (0.180, 0.080),
    (0.175, 0.100),
    (0.155, 0.120),
    (0.150, 0.130),
    (0.130, 0.130),
    (0.130, 0.145),
    (0.000, 0.145),
]


def create_body():
    mesh = bpy.data.meshes.new("BodyProfile")
    bm = bmesh.new()

    verts = []
    for x, z in BODY_PROFILE:
        verts.append(bm.verts.new((x, 0.0, z)))

    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("CenserBody", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Spin 旋转成型
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.spin(
        steps=64,
        dupli=False,
        angle=math.tau,
        center=(0.0, 0.0, 0.0),
        axis=(0.0, 0.0, 1.0)
    )
    # Blender 5.x: remove_doubles 已移除，改用 merge_by_distance
    try:
        bpy.ops.mesh.merge_by_distance(threshold=0.0001)
    except RuntimeError:
        # 旧版回退
        try:
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
        except RuntimeError:
            pass
    bpy.ops.object.mode_set(mode='OBJECT')

    # 平滑着色（Blender 5.x 不再需要 use_auto_smooth）
    bpy.ops.object.shade_smooth()

    # 修改器：Subsurf
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2

    # 修改器：Bevel
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.015
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(30)

    return obj


# =====================================================================
# 2. 双耳把手（Bezier + Circle Bevel）
# =====================================================================

HANDLE_PATH = [
    (0.150, 0.115),
    (0.210, 0.118),
    (0.235, 0.095),
    (0.215, 0.072),
    (0.155, 0.075),
]


def create_handle(name="HandleL"):
    curve = bpy.data.curves.new(name=name + "Path", type='CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(HANDLE_PATH) - 1)

    for i, (x, z) in enumerate(HANDLE_PATH):
        bp = spline.bezier_points[i]
        bp.co = (x, 0.0, z)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    handle_obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(handle_obj)

    # 圆形截面
    circle = bpy.data.curves.new(name=name + "Section", type='CURVE')
    circle.dimensions = '2D'
    circle_spline = circle.splines.new('NURBS')
    circle_spline.points.add(7)
    for i in range(8):
        angle = (i / 8) * math.tau
        cx = math.cos(angle) * 0.025
        cy = math.sin(angle) * 0.025
        circle_spline.points[i].co = (cx, cy, 0, 1)
    circle_spline.use_cyclic_u = True

    circle_obj = bpy.data.objects.new(name + "Section", circle)
    bpy.context.collection.objects.link(circle_obj)

    # Bevel（兼容写法）
    try:
        handle_obj.data.bevel_mode = 'OBJECT'
        handle_obj.data.bevel_object = circle_obj
    except AttributeError:
        # Blender 5.x 可能改变了 API
        print("[!] bevel_mode/bevel_object API 变化，尝试备选方案")

    try:
        handle_obj.data.use_fill_caps = True
    except AttributeError:
        pass

    # 转为 Mesh
    bpy.context.view_layer.objects.active = handle_obj
    handle_obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    handle_obj = bpy.context.active_object

    # Subsurf
    subsurf = handle_obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2

    # 平滑着色
    bpy.ops.object.shade_smooth()
    return handle_obj


def create_mirror_handle(original_handle):
    mirror = original_handle.modifiers.new(name="Mirror", type='MIRROR')
    mirror.use_axis = (True, False, False)
    mirror.use_bisect_axis = (True, False, False)
    bpy.context.view_layer.objects.active = original_handle
    original_handle.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Mirror")
    return original_handle


# =====================================================================
# 3. 红釉陶瓷 PBR 材质
# =====================================================================

def create_red_glaze_material():
    mat = bpy.data.materials.new(name="红釉陶瓷")
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")

    _safe_set_input(bsdf, ["Base Color", "Color"], (0.722, 0.145, 0.145, 1.0))
    _safe_set_input(bsdf, ["Roughness"], 0.10)
    _safe_set_input(bsdf, ["Metallic"], 0.0)
    _safe_set_input(bsdf, ["IOR", "Index of Refraction"], 1.54)
    _safe_set_input(bsdf, ["Subsurface Weight", "Subsurface", "Subsurface Scale"], 0.15)
    _safe_set_input(bsdf, ["Subsurface Color", "Subsurface Tint"], (0.847, 0.333, 0.333, 1.0))
    _safe_set_input(bsdf, ["Subsurface Radius", "Subsurface Radii"], (1.0, 0.4, 0.1))

    output = mat.node_tree.nodes.get("Material Output")
    if output:
        for name in ["Surface", "BSDF"]:
            if name in output.inputs:
                mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs[name])
                break

    return mat


# =====================================================================
# 4. 场景灯光
# =====================================================================

def setup_preview_lighting():
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    key = bpy.data.lights.new(name="Key", type='AREA')
    key.energy = 1000
    key.size = 2.0
    key_obj = bpy.data.objects.new("KeyLight", key)
    key_obj.location = (-2.5, -3.0, 4.0)
    bpy.context.collection.objects.link(key_obj)

    fill = bpy.data.lights.new(name="Fill", type='AREA')
    fill.energy = 300
    fill.size = 1.5
    fill_obj = bpy.data.objects.new("FillLight", fill)
    fill_obj.location = (2.5, -2.0, 3.0)
    bpy.context.collection.objects.link(fill_obj)

    rim = bpy.data.lights.new(name="Rim", type='AREA')
    rim.energy = 400
    rim.size = 1.0
    rim_obj = bpy.data.objects.new("RimLight", rim)
    rim_obj.location = (0.0, 3.0, 2.5)
    bpy.context.collection.objects.link(rim_obj)


# =====================================================================
# 主流程
# =====================================================================

def main():
    print("=" * 60)
    print("红釉双耳炉 Blender 建模脚本 (Blender 5.1 兼容)")
    print("=" * 60)

    clear_scene()

    body = create_body()
    print("[+] 炉身主体已生成")

    handle_l = create_handle("HandleL")
    print("[+] 左侧把手已生成")

    create_mirror_handle(handle_l)
    print("[+] 右侧把手已生成")

    mat = create_red_glaze_material()
    body.data.materials.append(mat)
    handle_l.data.materials.append(mat)
    print("[+] 红釉陶瓷材质已应用")

    setup_preview_lighting()
    print("[+] 三点布光已设置")

    cam = bpy.data.cameras.new(name="PreviewCam")
    cam_obj = bpy.data.objects.new("PreviewCamera", cam)
    cam_obj.location = (0.0, -2.5, 1.8)
    cam_obj.rotation_euler = (math.radians(65), 0.0, 0.0)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    print("[+] 预览相机已放置")

    print("\n下一步：")
    print("1. 微调曲线点匹配参考图")
    print("2. Bridge Edge Loops 焊接把手")
    print("3. Ctrl+J 合并，导出 GLB")


if __name__ == "__main__":
    main()
