#!/usr/bin/env python3
"""
从正面白底陶瓷照片提取轮廓，用于生成 Lathe 旋转体 3D 模型。

用法:
    python scripts/extract_profile.py static/image/show/xxx.jpg
    输出: static/profiles/xxx_profile.json

轮廓 JSON 格式:
    {
        "image": "原始图片路径",
        "width": 原始宽度,
        "height": 原始高度,
        "profile": [[radius_0, height_0], [radius_1, height_1], ...]
    }
    其中 radius 和 height 均已归一化到 0~1 范围。
"""

import json
import os
import sys
from PIL import Image


def extract_profile(image_path, bg_threshold=245, min_alpha=128):
    """
    从白底照片中提取器物轮廓。
    返回: (profile_points, img_width, img_height)
    profile_points: [(radius_norm, height_norm), ...] 从上到下
    """
    img = Image.open(image_path).convert('RGBA')
    width, height = img.size

    left_edge = []
    right_edge = []

    for y in range(height):
        row_left = None
        row_right = None
        for x in range(width):
            r, g, b, a = img.getpixel((x, y))
            # 判断是否为背景: 接近白色且不太透明
            is_bg = (a < min_alpha) or (r > bg_threshold and g > bg_threshold and b > bg_threshold)
            if not is_bg:
                if row_left is None:
                    row_left = x
                row_right = x

        if row_left is not None and row_right is not None:
            center = (row_left + row_right) / 2.0
            radius = (row_right - row_left) / 2.0
            left_edge.append((center - radius, y))
            right_edge.append((center + radius, y))

    if not left_edge:
        raise ValueError(f"未能从 {image_path} 提取到轮廓，请确认背景为纯色且器物与背景对比明显")

    # 使用左边缘作为轮廓（镜像对称）
    # 归一化: x->radius/width, y->height/height (翻转Y使底部为0)
    profile = []
    for x, y in left_edge:
        nx = x / width
        ny = 1.0 - (y / height)  # 翻转，底部为0
        profile.append([round(nx, 4), round(ny, 4)])

    # 去重：移除过于接近的点
    cleaned = [profile[0]]
    for p in profile[1:]:
        last = cleaned[-1]
        if abs(p[0] - last[0]) > 0.001 or abs(p[1] - last[1]) > 0.001:
            cleaned.append(p)

    return cleaned, width, height


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/extract_profile.py <图片路径>")
        print("示例: python scripts/extract_profile.py static/image/show/08bcc8619da15841e5aa61dfe57ec74f.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 {image_path}")
        sys.exit(1)

    profile, w, h = extract_profile(image_path)

    # 构建输出路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_dir = os.path.join(base_dir, "static", "profiles")
    os.makedirs(profile_dir, exist_ok=True)

    basename = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(profile_dir, f"{basename}_profile.json")

    data = {
        "image": image_path,
        "width": w,
        "height": h,
        "point_count": len(profile),
        "profile": profile,
        "note": "radius 和 height 均已归一化到 0~1。可直接用于 Blender Lathe/Screw 或 Three.js LatheGeometry"
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"轮廓提取完成: {out_path}")
    print(f"  图片尺寸: {w}x{h}")
    print(f"  轮廓点数: {len(profile)}")
    print(f"  前5个点: {profile[:5]}")


if __name__ == '__main__':
    main()
