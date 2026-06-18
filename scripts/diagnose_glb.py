#!/usr/bin/env python3
"""诊断 GLB 文件内部结构"""
import struct, json, sys, os

filepath = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "models", "exhibit_1.glb"
)

with open(filepath, "rb") as f:
    data = f.read()

print(f"文件: {filepath}")
print(f"总大小: {len(data):,} bytes ({len(data)/1024/1024:.2f} MB)")

magic = data[0:4]
version = struct.unpack("<I", data[4:8])[0]
total_len = struct.unpack("<I", data[8:12])[0]
print(f"GLB Version: {version}, Header says length: {total_len}")

offset = 12
json_data = None
bin_len = 0

while offset < len(data):
    chunk_len = struct.unpack("<I", data[offset:offset+4])[0]
    chunk_type = struct.unpack("<I", data[offset+4:offset+8])[0]
    chunk_data = data[offset+8:offset+8+chunk_len]

    if chunk_type == 0x4E4F534A:  # JSON
        json_data = json.loads(chunk_data)
        print(f"\nJSON chunk: {chunk_len:,} bytes")
    elif chunk_type == 0x004E4942:  # BIN
        bin_len = chunk_len
        print(f"BIN  chunk: {chunk_len:,} bytes")

    offset += 8 + chunk_len
    if chunk_len % 4:
        offset += 4 - (chunk_len % 4)

if not json_data:
    print("未找到 JSON chunk!")
    sys.exit(1)

# Nodes
nodes = json_data.get("nodes", [])
print(f"\nNodes ({len(nodes)}):")
for i, n in enumerate(nodes):
    name = n.get("name", "unnamed")
    mesh = n.get("mesh", "none")
    trans = n.get("translation", [0,0,0])
    scale = n.get("scale", [1,1,1])
    print(f"  {i}: {name} mesh={mesh} translation={trans} scale={scale}")

# Meshes
meshes = json_data.get("meshes", [])
print(f"\nMeshes ({len(meshes)}):")
for i, m in enumerate(meshes):
    prims = m.get("primitives", [])
    print(f"  {i}: {len(prims)} primitive(s)")
    for j, p in enumerate(prims):
        attrs = list(p.get("attributes", {}).keys())
        mode = p.get("mode", 4)
        idx = p.get("indices", "none")
        mat = p.get("material", "none")
        print(f"    prim {j}: mode={mode} indices={idx} material={mat} attrs={attrs}")

# Accessors (顶点/索引数据描述)
accessors = json_data.get("accessors", [])
print(f"\nAccessors ({len(accessors)}):")
for i, a in enumerate(accessors):
    t = a.get("type")
    count = a.get("count")
    ctype = a.get("componentType")
    minv = a.get("min", "")
    maxv = a.get("max", "")
    bufv = a.get("bufferView", "")
    # 只打印关键 accessor（POSITION）
    if a.get("_name_hint") or "POSITION" in str(a):
        pass
    print(f"  {i}: type={t} count={count:,} componentType={ctype} bufferView={bufv}")
    if minv and maxv:
        print(f"       min={minv} max={maxv}")

# Materials
mats = json_data.get("materials", [])
print(f"\nMaterials ({len(mats)}):")
for i, m in enumerate(mats):
    name = m.get("name", "unnamed")
    pbr = m.get("pbrMetallicRoughness", {})
    color = pbr.get("baseColorFactor", "")
    rough = pbr.get("roughnessFactor", "")
    print(f"  {i}: {name} baseColor={color} roughness={rough}")

# Scenes / Scene
scenes = json_data.get("scenes", [])
scene = json_data.get("scene", 0)
print(f"\nScenes: {len(scenes)}, active scene index: {scene}")
if scenes:
    print(f"  Scene 0 nodes: {scenes[0].get('nodes', [])}")
