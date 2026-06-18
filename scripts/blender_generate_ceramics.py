#!/usr/bin/env python3
"""
Blender 批量陶瓷建模脚本
============================
在项目根目录执行:
    blender --background --python scripts/blender_generate_ceramics.py

Windows 示例 (根据实际安装路径调整):
    "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python scripts\blender_generate_ceramics.py
"""

import bpy
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "static", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================================
# 器型轮廓 (x=半径, y=高度, 单位: 米)
# =====================================================================
PROFILES = {
    "meiping": [
        (0.000, 0.000), (0.030, 0.000), (0.032, 0.005),
        (0.070, 0.030), (0.075, 0.060), (0.070, 0.100),
        (0.055, 0.140), (0.040, 0.170), (0.030, 0.190),
        (0.025, 0.205), (0.022, 0.215), (0.018, 0.225),
        (0.015, 0.235), (0.012, 0.245), (0.000, 0.245),
    ],
    "yuhuchun": [
        (0.000, 0.000), (0.030, 0.000), (0.032, 0.005),
        (0.035, 0.020), (0.033, 0.055), (0.032, 0.090),
        (0.055, 0.120), (0.068, 0.140), (0.062, 0.160),
        (0.045, 0.180), (0.035, 0.195), (0.030, 0.210),
        (0.028, 0.220), (0.030, 0.225), (0.032, 0.230), (0.000, 0.230),
    ],
    "guanyin": [
        (0.000, 0.000), (0.028, 0.000), (0.030, 0.005),
        (0.055, 0.025), (0.065, 0.050), (0.060, 0.085),
        (0.045, 0.125), (0.032, 0.155), (0.025, 0.175),
        (0.022, 0.190), (0.025, 0.200), (0.028, 0.208), (0.000, 0.208),
    ],
    "bowl": [
        (0.000, 0.000), (0.020, 0.000), (0.022, 0.005),
        (0.055, 0.030), (0.072, 0.060), (0.078, 0.090),
        (0.072, 0.110), (0.058, 0.125), (0.042, 0.135),
        (0.028, 0.140), (0.015, 0.142), (0.000, 0.142),
    ],
    "plate": [
        (0.000, 0.000), (0.022, 0.000), (0.025, 0.004),
        (0.070, 0.015), (0.095, 0.035), (0.105, 0.055),
        (0.102, 0.068), (0.092, 0.078), (0.078, 0.084),
        (0.060, 0.088), (0.040, 0.090), (0.000, 0.090),
    ],
    "jar": [
        (0.000, 0.000), (0.035, 0.000), (0.038, 0.004),
        (0.065, 0.022), (0.078, 0.050), (0.080, 0.080),
        (0.072, 0.110), (0.055, 0.135), (0.040, 0.152),
        (0.032, 0.165), (0.030, 0.173), (0.032, 0.180), (0.000, 0.180),
    ],
    "washer": [
        (0.000, 0.000), (0.025, 0.000), (0.028, 0.004),
        (0.065, 0.014), (0.088, 0.032), (0.095, 0.048),
        (0.090, 0.058), (0.078, 0.067), (0.060, 0.073),
        (0.040, 0.077), (0.000, 0.077),
    ],
    "cup": [
        (0.000, 0.000), (0.018, 0.000), (0.020, 0.004),
        (0.035, 0.018), (0.042, 0.042), (0.044, 0.068),
        (0.042, 0.088), (0.038, 0.103), (0.032, 0.113),
        (0.025, 0.121), (0.018, 0.125), (0.000, 0.125),
    ],
    "vase": [
        (0.000, 0.000), (0.028, 0.000), (0.030, 0.004),
        (0.048, 0.022), (0.055, 0.048), (0.052, 0.080),
        (0.042, 0.118), (0.032, 0.150), (0.025, 0.175),
        (0.020, 0.195), (0.018, 0.210), (0.020, 0.222),
        (0.022, 0.230), (0.000, 0.230),
    ],
}

# =====================================================================
# PBR 陶瓷材质定义
# =====================================================================
MATS = {
    "ru":        {"name": "汝窑天青釉",     "color": (0.50,0.72,0.82,1.0), "roughness": 0.12, "sss": 0.10, "ior": 1.45},
    "celadon":   {"name": "龙泉青瓷釉",     "color": (0.48,0.62,0.55,1.0), "roughness": 0.15, "sss": 0.08, "ior": 1.45},
    "jun":       {"name": "钧窑玫瑰紫釉",   "color": (0.55,0.40,0.55,1.0), "roughness": 0.20, "sss": 0.06, "ior": 1.45},
    "white":     {"name": "定窑白釉",       "color": (0.95,0.93,0.88,1.0), "roughness": 0.18, "sss": 0.05, "ior": 1.45},
    "ge":        {"name": "哥窑米黄釉",     "color": (0.78,0.73,0.65,1.0), "roughness": 0.25, "sss": 0.04, "ior": 1.45},
    "black":     {"name": "建窑黑釉",       "color": (0.08,0.08,0.08,1.0), "roughness": 0.08, "sss": 0.02, "ior": 1.50},
    "zisha":     {"name": "宜兴紫砂",       "color": (0.55,0.35,0.28,1.0), "roughness": 0.45, "sss": 0.03, "ior": 1.40},
    "bluewhite": {"name": "景德镇青花",     "color": (0.94,0.92,0.86,1.0), "roughness": 0.15, "sss": 0.04, "ior": 1.45},
    "fencai":    {"name": "粉彩瓷",         "color": (0.96,0.94,0.90,1.0), "roughness": 0.20, "sss": 0.04, "ior": 1.45},
    "famillerose":{"name":"珐琅彩瓷",       "color": (0.97,0.95,0.91,1.0), "roughness": 0.12, "sss": 0.05, "ior": 1.45},
    "doucai":    {"name": "斗彩瓷",         "color": (0.95,0.93,0.88,1.0), "roughness": 0.15, "sss": 0.04, "ior": 1.45},
    "sancai":    {"name": "唐三彩",         "color": (0.78,0.70,0.55,1.0), "roughness": 0.30, "sss": 0.03, "ior": 1.40},
    "red":       {"name": "釉里红",         "color": (0.93,0.90,0.86,1.0), "roughness": 0.15, "sss": 0.04, "ior": 1.45},
    "cizhou":    {"name": "磁州窑白地黑花","color": (0.94,0.92,0.87,1.0), "roughness": 0.25, "sss": 0.03, "ior": 1.40},
}

# =====================================================================
# 展品列表
# =====================================================================
ITEMS = [
    {"id": 1,  "title": "青花瓷瓶",       "shape": "meiping",   "mat": "bluewhite"},
    {"id": 2,  "title": "白瓷观音像",     "shape": "guanyin",   "mat": "white"},
    {"id": 3,  "title": "粉彩花卉碗",     "shape": "bowl",      "mat": "fencai"},
    {"id": 4,  "title": "汝窑天青釉盘",   "shape": "plate",     "mat": "ru"},
    {"id": 5,  "title": "龙泉青瓷梅瓶",   "shape": "meiping",   "mat": "celadon"},
    {"id": 6,  "title": "唐三彩骆驼",     "shape": "jar",       "mat": "sancai"},
    {"id": 7,  "title": "钧窑玫瑰紫釉洗", "shape": "washer",    "mat": "jun"},
    {"id": 8,  "title": "定窑白釉刻花盘", "shape": "plate",     "mat": "white"},
    {"id": 9,  "title": "哥窑金丝铁线瓶", "shape": "vase",      "mat": "ge"},
    {"id": 10, "title": "建窑兔毫盏",     "shape": "cup",       "mat": "black"},
    {"id": 11, "title": "磁州窑白地黑花罐","shape": "jar",      "mat": "cizhou"},
    {"id": 12, "title": "紫砂茶壶",       "shape": "jar",       "mat": "zisha"},
    {"id": 13, "title": "釉里红高足杯",   "shape": "cup",       "mat": "red"},
    {"id": 14, "title": "斗彩鸡缸杯",     "shape": "cup",       "mat": "doucai"},
    {"id": 15, "title": "珐琅彩花卉瓶",   "shape": "yuhuchun",  "mat": "famillerose"},
    {"id": 16, "title": "黑陶蛋壳杯",     "shape": "cup",       "mat": "black"},
]

# =====================================================================
# Blender 函数
# =====================================================================

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            data.remove(block)

def _safe_set_input(node, possible_names, value):
    """尝试多个可能的输入名，找到第一个存在的并设置。"""
    for name in possible_names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False

def create_material(info):
    mat = bpy.data.materials.new(name=info["name"])
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")

    # 基础属性 (这些名称通常不变)
    _safe_set_input(bsdf, ["Base Color", "Color"], info["color"])
    _safe_set_input(bsdf, ["Roughness"], info["roughness"])
    _safe_set_input(bsdf, ["IOR", "Index of Refraction"], info["ior"])

    # 次表面散射 — 不同版本名称差异很大，逐个尝试
    _safe_set_input(bsdf, ["Subsurface Weight", "Subsurface", "Subsurface Scale"], info["sss"])
    _safe_set_input(bsdf, ["Subsurface Color", "Subsurface Tint"], info["color"])
    _safe_set_input(bsdf, ["Subsurface Radius", "Subsurface Radii"], (1.0, 0.4, 0.1))

    output = mat.node_tree.nodes.get("Material Output")
    if output:
        surf_names = ["Surface", "BSDF"]
        for name in surf_names:
            if name in output.inputs:
                mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs[name])
                break
    return mat

def create_vase(profile_points, mat_info):
    # 1. 创建贝塞尔曲线（XZ 平面：X=半径, Z=高度）
    curve = bpy.data.curves.new(name="Profile", type="CURVE")
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(count=len(profile_points) - 1)
    for i, (x, y) in enumerate(profile_points):
        bp = spline.bezier_points[i]
        bp.co = (x, 0.0, y)            # Z 轴为高度
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"

    # 强制手柄留在 XZ 平面，防止偏离产生扭曲
    for bp in spline.bezier_points:
        bp.handle_left.y = 0.0
        bp.handle_right.y = 0.0

    obj = bpy.data.objects.new("Ceramic", curve)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # 2. Screw 旋转生成
    screw = obj.modifiers.new(name="Screw", type="SCREW")
    screw.axis = "Z"
    screw.steps = 64
    screw.render_steps = 64
    screw.use_smooth_shade = True

    # 曲线必须先转 Mesh 才能应用修改器
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.active_object  # 获取转换后的网格对象

    # 3. 实体化 (器壁厚度 1.5cm)
    solidify = obj.modifiers.new(name="Solidify", type="SOLIDIFY")
    solidify.thickness = 0.015
    solidify.offset = -1.0

    # 4. 细分表面 (降为 1 级，文件大小可控)
    subsurf = obj.modifiers.new(name="Subsurf", type="SUBSURF")
    subsurf.levels = 1
    subsurf.render_levels = 2

    bpy.ops.object.modifier_apply(modifier="Solidify")
    bpy.ops.object.modifier_apply(modifier="Subsurf")

    # 5. 平滑着色 + 材质
    bpy.ops.object.shade_smooth()
    mat = create_material(mat_info)
    obj.data.materials.append(mat)

    # 6. 清除缩放遗留，保持自然位置（底部在 Z=0）
    # 不移动原点，不 apply location，让前端负责居中
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    return obj

def delete_all_except(obj):
    """导出前删除场景中除目标对象外的所有东西，确保 GLB 干净。"""
    for o in list(bpy.context.scene.objects):
        if o != obj:
            bpy.data.objects.remove(o, do_unlink=True)

def export_glb(obj, filepath):
    delete_all_except(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 最小参数集，兼容 Blender 3.x / 4.x / 5.x
    kwargs = {
        "filepath": filepath,
        "export_format": "GLB",
        "use_selection": True,
        "export_yup": True,
        "export_materials": 'EXPORT',
        "export_image_format": 'AUTO',
        "export_texcoords": True,
        "export_normals": True,
        "export_draco_mesh_compression_enable": False,
    }

    bpy.ops.export_scene.gltf(**kwargs)

def main():
    print("=" * 60)
    print(f"Blender {bpy.app.version_string} | 陶瓷器型批量生成")
    print("=" * 60)

    for item in ITEMS:
        profile = PROFILES.get(item["shape"])
        mat_info = MATS.get(item["mat"])
        if not profile or not mat_info:
            print(f"[!] 跳过: {item['title']}")
            continue

        print(f"\n[+] {item['title']}  ({item['shape']} / {mat_info['name']})")

        # 每个模型独立干净场景
        clear_scene()
        obj = create_vase(profile, mat_info)
        obj.name = f"Exhibit_{item['id']}"

        filepath = os.path.join(OUTPUT_DIR, f"exhibit_{item['id']}.glb")
        export_glb(obj, filepath)

        # 确认文件大小
        size_kb = os.path.getsize(filepath) / 1024
        print(f"    -> {filepath}  ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print(f"完成！共生成 {len(ITEMS)} 个 GLB")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
