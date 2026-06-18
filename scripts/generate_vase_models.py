#!/usr/bin/env python3
"""
批量生成 16 件陶瓷展品的旋转体 GLB 模型。
纯 Python 实现，仅需 Pillow，不依赖 numpy/trimesh。
用法: venv/bin/python scripts/generate_vase_models.py
"""

import struct
import json
import math
import io
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'static', 'models')

# ---------------------------------------------------------------------------
# 1. 器型轮廓定义 (r, y)，从底部到顶部，r=半径, y=高度
# ---------------------------------------------------------------------------

def interpolate_profile(control_points, steps=32):
    """对控制点做线性插值，得到更密的轮廓。"""
    pts = []
    for i in range(len(control_points) - 1):
        r0, y0 = control_points[i]
        r1, y1 = control_points[i + 1]
        for s in range(steps):
            t = s / steps
            r = r0 + (r1 - r0) * t
            y = y0 + (y1 - y0) * t
            pts.append((r, y))
    pts.append(control_points[-1])
    return pts


def make_meiping():
    """梅瓶: 小口，短颈，丰肩，瘦底。"""
    return interpolate_profile([
        (0.0, 0.0), (0.32, 0.0), (0.35, 0.05),
        (0.38, 0.12), (0.40, 0.20), (0.55, 0.30),
        (0.72, 0.42), (0.78, 0.55), (0.75, 0.70),
        (0.65, 0.90), (0.50, 1.15), (0.38, 1.40),
        (0.28, 1.60), (0.20, 1.75), (0.15, 1.85),
        (0.12, 1.92), (0.10, 1.98), (0.0, 1.98),
    ], steps=10)


def make_yuhuchun():
    """玉壶春瓶: 撇口，细颈，垂腹，圈足。"""
    return interpolate_profile([
        (0.0, 0.0), (0.30, 0.0), (0.32, 0.03),
        (0.35, 0.15), (0.33, 0.50), (0.32, 0.85),
        (0.55, 1.15), (0.68, 1.35), (0.62, 1.55),
        (0.45, 1.75), (0.35, 1.92), (0.30, 2.05),
        (0.28, 2.12), (0.30, 2.18), (0.32, 2.22), (0.0, 2.22),
    ], steps=6)


def make_guanyin():
    """观音瓶: 侈口，短颈，丰肩，下腹收敛。"""
    return interpolate_profile([
        (0.0, 0.0), (0.30, 0.0), (0.33, 0.03),
        (0.60, 0.20), (0.70, 0.45), (0.65, 0.80),
        (0.48, 1.20), (0.35, 1.50), (0.28, 1.70),
        (0.25, 1.85), (0.28, 1.95), (0.32, 2.02), (0.0, 2.02),
    ], steps=6)


def make_bowl():
    """碗型: 敞口，弧形壁，圈足。"""
    return interpolate_profile([
        (0.0, 0.0), (0.20, 0.0), (0.22, 0.04),
        (0.55, 0.25), (0.72, 0.55), (0.78, 0.85),
        (0.72, 1.05), (0.58, 1.20), (0.42, 1.30),
        (0.28, 1.36), (0.15, 1.38), (0.0, 1.38),
    ], steps=6)


def make_plate():
    """盘型: 平弧，浅腹，圈足。"""
    return interpolate_profile([
        (0.0, 0.0), (0.22, 0.0), (0.25, 0.03),
        (0.70, 0.12), (0.95, 0.28), (1.05, 0.45),
        (1.02, 0.58), (0.92, 0.68), (0.78, 0.74),
        (0.60, 0.78), (0.40, 0.80), (0.0, 0.80),
    ], steps=6)


def make_jar():
    """罐型: 直口/敛口，丰肩，鼓腹，平底。"""
    return interpolate_profile([
        (0.0, 0.0), (0.35, 0.0), (0.38, 0.03),
        (0.65, 0.20), (0.78, 0.45), (0.80, 0.75),
        (0.72, 1.05), (0.55, 1.30), (0.40, 1.48),
        (0.32, 1.60), (0.30, 1.68), (0.32, 1.74), (0.0, 1.74),
    ], steps=6)


def make_washer():
    """洗型: 敞口，浅腹，平底。"""
    return interpolate_profile([
        (0.0, 0.0), (0.25, 0.0), (0.28, 0.03),
        (0.65, 0.12), (0.88, 0.28), (0.95, 0.42),
        (0.90, 0.52), (0.78, 0.60), (0.60, 0.66),
        (0.40, 0.70), (0.0, 0.70),
    ], steps=6)


def make_cup():
    """杯型: 口稍敞，深腹，圈足。"""
    return interpolate_profile([
        (0.0, 0.0), (0.18, 0.0), (0.20, 0.03),
        (0.35, 0.15), (0.42, 0.40), (0.44, 0.65),
        (0.42, 0.85), (0.38, 1.00), (0.32, 1.10),
        (0.25, 1.18), (0.18, 1.22), (0.0, 1.22),
    ], steps=6)


def make_vase():
    """通用瓶型: 修长，口微撇。"""
    return interpolate_profile([
        (0.0, 0.0), (0.28, 0.0), (0.30, 0.03),
        (0.48, 0.20), (0.55, 0.45), (0.52, 0.75),
        (0.42, 1.10), (0.32, 1.40), (0.25, 1.65),
        (0.20, 1.85), (0.18, 2.00), (0.20, 2.10),
        (0.22, 2.16), (0.0, 2.16),
    ], steps=6)


SHAPE_BUILDERS = {
    'meiping': make_meiping,
    'yuhuchun': make_yuhuchun,
    'guanyin': make_guanyin,
    'bowl': make_bowl,
    'plate': make_plate,
    'jar': make_jar,
    'washer': make_washer,
    'cup': make_cup,
    'vase': make_vase,
}


# ---------------------------------------------------------------------------
# 2. 旋转体网格生成
# ---------------------------------------------------------------------------

def generate_lathe(profile, segments=64):
    """
    将 2D 轮廓绕 Y 轴旋转生成 3D 网格。
    返回: vertices(list of (x,y,z)), normals(list of (nx,ny,nz)),
          uvs(list of (u,v)), indices(list of int)
    """
    n = len(profile)
    verts = []
    norms = []
    uvs = []

    y_min = profile[0][1]
    y_max = profile[-1][1]
    y_range = y_max - y_min if y_max != y_min else 1.0

    # 计算轮廓法线（2D截面内，朝外）
    prof_norms_2d = []
    for i in range(n):
        if i == 0:
            dr = profile[1][0] - profile[0][0]
            dy = profile[1][1] - profile[0][1]
        elif i == n - 1:
            dr = profile[-1][0] - profile[-2][0]
            dy = profile[-1][1] - profile[-2][1]
        else:
            dr = profile[i + 1][0] - profile[i - 1][0]
            dy = profile[i + 1][1] - profile[i - 1][1]

        # 2D 法线 (朝外): (dy, -dr)
        length = math.sqrt(dr * dr + dy * dy)
        if length < 1e-6:
            nx2d, ny2d = 1.0, 0.0
        else:
            nx2d, ny2d = dy / length, -dr / length

        # 如果点在中心轴附近且朝内，翻转
        if profile[i][0] < 0.01 and ny2d < 0:
            ny2d = -ny2d
        prof_norms_2d.append((nx2d, ny2d))

    # 生成顶点、法线、UV
    for i in range(n):
        r, y = profile[i]
        nx2d, ny2d = prof_norms_2d[i]
        v = (y - y_min) / y_range
        for j in range(segments):
            theta = 2.0 * math.pi * j / segments
            c = math.cos(theta)
            s = math.sin(theta)
            x = r * c
            z = r * s
            verts.append((x, y, z))

            # 3D 法线
            nx = nx2d * c
            ny = ny2d
            nz = nx2d * s
            nl = math.sqrt(nx * nx + ny * ny + nz * nz)
            if nl < 1e-6:
                nx, ny, nz = 0.0, 1.0, 0.0
            else:
                nx, ny, nz = nx / nl, ny / nl, nz / nl
            norms.append((nx, ny, nz))

            u = j / segments
            uvs.append((u, v))

    # 生成索引（侧面 quads 拆成两个三角形）
    indices = []
    for i in range(n - 1):
        for j in range(segments):
            j1 = (j + 1) % segments
            a = i * segments + j
            b = (i + 1) * segments + j
            c = (i + 1) * segments + j1
            d = i * segments + j1
            indices.extend([a, b, d, b, c, d])

    return verts, norms, uvs, indices


# ---------------------------------------------------------------------------
# 3. 纹理生成
# ---------------------------------------------------------------------------

def draw_crackle(draw, w, h, density=80):
    """哥窑冰裂纹效果。"""
    random.seed(42)
    for _ in range(density):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        x2 = x1 + random.randint(-80, 80)
        y2 = y1 + random.randint(-80, 80)
        draw.line([(x1, y1), (x2, y2)], fill=(40, 40, 40), width=1)
    for _ in range(density // 2):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        x2 = x1 + random.randint(-40, 40)
        y2 = y1 + random.randint(-40, 40)
        draw.line([(x1, y1), (x2, y2)], fill=(60, 50, 35), width=1)


def draw_bluewhite_pattern(draw, w, h, seed=1):
    """青花: 白底蓝花，颈部蕉叶纹 + 腹部缠枝莲 + 底部莲瓣。"""
    random.seed(seed)
    # 底色已在 image 创建时设置
    
    # 口沿装饰线
    draw.line([(0, h * 0.01), (w, h * 0.01)], fill=(20, 40, 80), width=3)
    draw.line([(0, h * 0.02), (w, h * 0.02)], fill=(30, 60, 100), width=2)
    
    # 颈部蕉叶纹 (y: 0.03-0.18)
    leaf_count = 16
    for i in range(leaf_count):
        cx = w * (i + 0.5) / leaf_count
        cy = h * 0.10
        # 蕉叶形状
        points = [
            (cx, cy - h * 0.06),
            (cx - w * 0.02, cy + h * 0.04),
            (cx - w * 0.008, cy + h * 0.04),
            (cx, cy + h * 0.02),
            (cx + w * 0.008, cy + h * 0.04),
            (cx + w * 0.02, cy + h * 0.04),
        ]
        draw.polygon(points, fill=(25, 50, 90), outline=(15, 35, 70))
        # 叶脉
        draw.line([(cx, cy - h * 0.05), (cx, cy + h * 0.02)], fill=(15, 35, 70), width=1)
    
    # 肩部装饰带
    draw.line([(0, h * 0.18), (w, h * 0.18)], fill=(20, 40, 80), width=2)
    for i in range(w // 30):
        x = i * 30 + 15
        draw.arc([x - 8, h * 0.18 - 4, x + 8, h * 0.18 + 4], start=0, end=180, fill=(30, 60, 100))
    
    # 腹部缠枝花卉 (主体图案)
    band_count = 3
    petal_colors = [(30, 60, 100), (35, 65, 110), (40, 70, 120)]
    
    for band_idx in range(band_count):
        band_y = h * (0.28 + band_idx * 0.18)
        flower_count = 10
        
        for i in range(flower_count):
            cx = w * (i + random.uniform(0.2, 0.8)) / flower_count
            cy = band_y + random.uniform(-h * 0.05, h * 0.05)
            r = w * (0.035 + random.uniform(-0.01, 0.01))
            
            # 六瓣花朵
            for petal_idx in range(6):
                angle = petal_idx * 60 + random.uniform(-10, 10)
                rad = math.radians(angle)
                px = cx + math.cos(rad) * r * 0.8
                py = cy + math.sin(rad) * r * 0.8
                pr = r * 0.4
                draw.ellipse([px - pr, py - pr * 0.6, px + pr, py + pr * 0.6], 
                            fill=petal_colors[band_idx % 3], outline=(15, 35, 70))
            
            # 花心
            draw.ellipse([cx - r * 0.2, cy - r * 0.15, cx + r * 0.2, cy + r * 0.15], 
                        fill=(25, 50, 90))
        
        # 缠枝藤蔓
        for x in range(0, w, 12):
            y_off = math.sin(x / w * 8 + seed + band_idx) * h * 0.04
            py = band_y + y_off
            draw.ellipse([x - 3, py - 2, x + 3, py + 2], fill=(40, 75, 125))
    
    # 腹部开光装饰
    for i in range(6):
        cx = w * (i + 0.5) / 6
        cy = h * 0.52
        # 先画外轮廓
        draw.ellipse([cx - w * 0.08, cy - h * 0.05, cx + w * 0.08, cy + h * 0.05], 
                     fill=(20, 50, 95), outline=(10, 30, 60))
        # 开光内小图案
        draw.ellipse([cx - w * 0.03, cy - h * 0.02, cx + w * 0.03, cy + h * 0.02], 
                    fill=(35, 70, 115))
    
    # 胫部装饰带
    draw.line([(0, h * 0.78), (w, h * 0.78)], fill=(20, 40, 80), width=2)
    for i in range(w // 25):
        x = i * 25 + 12
        draw.line([(x, h * 0.76), (x, h * 0.80)], fill=(30, 60, 100), width=2)
    
    # 底部莲瓣纹 (y: 0.82-0.95)
    petal_count = 20
    for i in range(petal_count):
        cx = w * (i + 0.5) / petal_count
        cy = h * 0.89
        # 莲瓣
        points = [
            (cx, cy + h * 0.05),
            (cx - w * 0.018, cy + h * 0.01),
            (cx - w * 0.012, cy - h * 0.04),
            (cx, cy - h * 0.05),
            (cx + w * 0.012, cy - h * 0.04),
            (cx + w * 0.018, cy + h * 0.01),
        ]
        draw.polygon(points, fill=(30, 60, 100), outline=(15, 35, 70))
    
    # 圈足
    draw.line([(0, h * 0.97), (w, h * 0.97)], fill=(20, 40, 80), width=3)


def draw_fencai_pattern(draw, w, h, seed=1):
    """粉彩/珐琅彩: 多彩花卉。"""
    random.seed(seed)
    colors = [
        (210, 140, 150), (180, 120, 140),  # 粉红
        (160, 190, 160), (130, 170, 130),  # 绿
        (230, 200, 150), (210, 180, 120),  # 黄
        (180, 160, 210), (150, 130, 190),  # 紫
    ]
    # 底色微黄
    for y in range(h):
        tint = int(240 + 10 * math.sin(y / h * 3))
        draw.line([(0, y), (w, y)], fill=(tint, tint - 5, tint - 15))
    # 大朵花卉
    for _ in range(6):
        cx = random.randint(w // 6, w * 5 // 6)
        cy = random.randint(h // 5, h * 4 // 5)
        color = random.choice(colors)
        for petal in range(5):
            angle = petal * 72 + random.randint(-10, 10)
            rad = math.radians(angle)
            px = cx + math.cos(rad) * w * 0.04
            py = cy + math.sin(rad) * h * 0.04
            draw.ellipse([px - w * 0.03, py - h * 0.025, px + w * 0.03, py + h * 0.025],
                         fill=color, outline=(color[0] - 20, color[1] - 20, color[2] - 20))
        draw.ellipse([cx - w * 0.015, cy - h * 0.012, cx + w * 0.015, cy + h * 0.012], fill=(240, 220, 120))
    # 枝叶
    for _ in range(10):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        x2 = x1 + random.randint(-60, 60)
        y2 = y1 + random.randint(-40, 40)
        draw.line([(x1, y1), (x2, y2)], fill=(120, 150, 110), width=2)


def draw_celadon_texture(w, h):
    """青瓷: 青绿色底，可能带冰裂纹。"""
    img = Image.new('RGB', (w, h), (125, 160, 140))
    draw = ImageDraw.Draw(img)
    # 微妙的渐变
    for y in range(h):
        g = int(140 + 20 * math.sin(y / h * 2))
        draw.line([(0, y), (w, y)], fill=(115, g, 130))
    # 淡淡的釉面光泽线
    for x in range(0, w, 80):
        draw.line([(x, 0), (x, h)], fill=(135, 170, 150), width=1)
    return img


def draw_jun_texture(w, h, seed=1):
    """钧窑: 窑变紫红渐变，流淌感。"""
    random.seed(seed)
    img = Image.new('RGB', (w, h), (130, 110, 140))
    draw = ImageDraw.Draw(img)
    # 不规则流淌色块
    for _ in range(20):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(40, 120)
        color = random.choice([
            (140, 100, 140), (120, 90, 130), (150, 120, 160),
            (110, 100, 150), (130, 110, 120), (160, 130, 150),
        ])
        draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=color)
    img = img.filter(ImageFilter.GaussianBlur(radius=8))
    return img


def draw_sancai_texture(w, h, seed=1):
    """唐三彩: 黄绿白泼彩。"""
    random.seed(seed)
    img = Image.new('RGB', (w, h), (230, 220, 200))
    draw = ImageDraw.Draw(img)
    colors = [(200, 180, 100), (120, 160, 100), (230, 225, 210)]
    for _ in range(15):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(50, 150)
        color = random.choice(colors)
        draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=color)
    img = img.filter(ImageFilter.GaussianBlur(radius=10))
    return img


def draw_black_texture(w, h, seed=1):
    """黑陶: 漆黑 + 兔毫纹。"""
    random.seed(seed)
    img = Image.new('RGB', (w, h), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    # 兔毫纹: 细棕色条纹从上到下
    for _ in range(40):
        x = random.randint(0, w)
        y = 0
        while y < h:
            y_end = min(h, y + random.randint(20, 80))
            x_wiggle = x + random.randint(-3, 3)
            draw.line([(x, y), (x_wiggle, y_end)], fill=(80, 60, 40), width=1)
            y = y_end + random.randint(5, 15)
    # 光泽渐变
    for x in range(w):
        brightness = int(40 + 15 * math.sin(x / w * 2))
        draw.line([(x, 0), (x, h // 3)], fill=(brightness, brightness, brightness))
    return img


def draw_zisha_texture(w, h):
    """紫砂: 红褐底色 + 颗粒感。"""
    img = Image.new('RGB', (w, h), (140, 100, 85))
    draw = ImageDraw.Draw(img)
    random.seed(7)
    for _ in range(2000):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        shade = random.choice([(160, 120, 100), (120, 85, 70), (150, 110, 90), (130, 95, 80)])
        draw.point((x, y), fill=shade)
    return img


def draw_red_underglaze(draw, w, h, seed=1):
    """釉里红: 白底红花。"""
    random.seed(seed)
    # 底色已是米白
    for _ in range(5):
        cx = random.randint(w // 5, w * 4 // 5)
        cy = random.randint(h // 4, h * 3 // 4)
        for petal in range(6):
            angle = petal * 60
            rad = math.radians(angle)
            px = cx + math.cos(rad) * w * 0.035
            py = cy + math.sin(rad) * h * 0.03
            draw.ellipse([px - w * 0.02, py - h * 0.018, px + w * 0.02, py + h * 0.018],
                         fill=(170, 60, 60), outline=(140, 45, 45))
        draw.ellipse([cx - w * 0.01, cy - h * 0.008, cx + w * 0.01, cy + h * 0.008], fill=(220, 200, 100))


def draw_doucai(draw, w, h, seed=1):
    """斗彩: 青花轮廓 + 填彩。"""
    random.seed(seed)
    # 先画青花轮廓线
    for _ in range(4):
        cx = random.randint(w // 4, w * 3 // 4)
        cy = random.randint(h // 4, h * 3 // 4)
        r = w * 0.04
        draw.ellipse([cx - r, cy - r * 0.9, cx + r, cy + r * 0.9], outline=(35, 65, 110), width=2)
        # 内部填彩
        fill_colors = [(210, 140, 150), (180, 210, 160), (230, 210, 140)]
        draw.ellipse([cx - r * 0.7, cy - r * 0.6, cx + r * 0.7, cy + r * 0.6], fill=random.choice(fill_colors))


def draw_white_porcelain(draw, w, h, seed=1):
    """白瓷: 纯白微黄 + 极淡暗纹。"""
    random.seed(seed)
    for _ in range(3):
        y = random.randint(h // 4, h * 3 // 4)
        draw.arc([(-w, y - h * 0.05), (w * 2, y + h * 0.05)], start=0, end=360,
                 fill=(220, 215, 205), width=1)


def generate_texture(style, seed=1, size=(1024, 1024)):
    """根据风格生成纹理图。"""
    w, h = size
    img = Image.new('RGB', (w, h), (240, 235, 225))  # 默认米白底色
    draw = ImageDraw.Draw(img)

    if style == 'bluewhite':
        draw_bluewhite_pattern(draw, w, h, seed)
    elif style == 'fencai':
        return draw_fencai_pattern_img(w, h, seed)
    elif style == 'famillerose':
        return draw_fencai_pattern_img(w, h, seed)
    elif style == 'doucai':
        draw_doucai(draw, w, h, seed)
    elif style == 'celadon':
        return draw_celadon_texture(w, h)
    elif style == 'jun':
        return draw_jun_texture(w, h, seed)
    elif style == 'sancai':
        return draw_sancai_texture(w, h, seed)
    elif style == 'black':
        return draw_black_texture(w, h, seed)
    elif style == 'zisha':
        return draw_zisha_texture(w, h)
    elif style == 'red':
        draw_red_underglaze(draw, w, h, seed)
    elif style == 'ge':
        img = Image.new('RGB', (w, h), (195, 185, 165))
        draw_crackle(draw, w, h, density=100)
    elif style == 'white':
        draw_white_porcelain(draw, w, h, seed)
    elif style == 'cizhou':
        # 磁州窑白地黑花
        draw_white_porcelain(draw, w, h, seed)
        for _ in range(4):
            y = random.randint(h // 5, h * 4 // 5)
            draw.arc([(-w, y - h * 0.08), (w * 2, y + h * 0.08)], start=0, end=360,
                     fill=(40, 35, 30), width=2)
    else:
        pass  # 默认米白

    return img


def draw_fencai_pattern_img(w, h, seed):
    """粉彩专用返回。"""
    img = Image.new('RGB', (w, h), (245, 240, 230))
    draw = ImageDraw.Draw(img)
    draw_fencai_pattern(draw, w, h, seed)
    return img


# ---------------------------------------------------------------------------
# 4. GLB 打包
# ---------------------------------------------------------------------------

def build_glb(vertices, normals, uvs, indices, texture_image):
    """
    将顶点、法线、UV、索引和纹理图打包成二进制 GLB。
    完全手写，不依赖任何 3D 库。
    """
    # PNG 编码纹理
    tex_buf = io.BytesIO()
    texture_image.save(tex_buf, format='PNG')
    tex_bytes = tex_buf.getvalue()
    tex_buf.close()

    # 顶点数据 (float32, vec3)
    vert_bytes = b''.join(struct.pack('<3f', x, y, z) for x, y, z in vertices)
    # 法线数据 (float32, vec3)
    norm_bytes = b''.join(struct.pack('<3f', nx, ny, nz) for nx, ny, nz in normals)
    # UV 数据 (float32, vec2)
    uv_bytes = b''.join(struct.pack('<2f', u, v) for u, v in uvs)
    # 索引数据 (uint16)
    idx_bytes = struct.pack(f'<{len(indices)}H', *indices)
    # 索引补齐到 4 字节
    if len(idx_bytes) % 4 != 0:
        idx_bytes += b'\x00' * (4 - len(idx_bytes) % 4)

    # Buffer 布局
    buf_offsets = {
        'pos': 0,
        'norm': len(vert_bytes),
        'uv': len(vert_bytes) + len(norm_bytes),
        'idx': len(vert_bytes) + len(norm_bytes) + len(uv_bytes),
        'tex': len(vert_bytes) + len(norm_bytes) + len(uv_bytes) + len(idx_bytes),
    }
    buf_len = buf_offsets['tex'] + len(tex_bytes)
    bin_data = vert_bytes + norm_bytes + uv_bytes + idx_bytes + tex_bytes

    # 补齐 JSON chunk 到 4 字节边界 (JSON 用空格 0x20，BIN 用零字节)
    def pad4_spaces(data):
        rem = len(data) % 4
        return data + b' ' * rem if rem else data

    def pad4_zeros(data):
        rem = len(data) % 4
        return data + b'\x00' * rem if rem else data

    # 构建 JSON
    json_data = {
        "asset": {"version": "2.0", "generator": "vase-generator"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2,
                },
                "indices": 3,
                "material": 0,
            }]
        }],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.05,
                "roughnessFactor": 0.35,
            },
            "emissiveFactor": [0.02, 0.02, 0.02],
        }],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": 4, "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "buffers": [{"byteLength": buf_len}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": buf_offsets['pos'], "byteLength": len(vert_bytes)},
            {"buffer": 0, "byteOffset": buf_offsets['norm'], "byteLength": len(norm_bytes)},
            {"buffer": 0, "byteOffset": buf_offsets['uv'], "byteLength": len(uv_bytes)},
            {"buffer": 0, "byteOffset": buf_offsets['idx'], "byteLength": len(idx_bytes)},
            {"buffer": 0, "byteOffset": buf_offsets['tex'], "byteLength": len(tex_bytes)},
        ],
        "accessors": [
            {  # 0 POSITION
                "bufferView": 0, "componentType": 5126, "count": len(vertices),
                "type": "VEC3",
                "min": [min(v[0] for v in vertices), min(v[1] for v in vertices), min(v[2] for v in vertices)],
                "max": [max(v[0] for v in vertices), max(v[1] for v in vertices), max(v[2] for v in vertices)],
            },
            {  # 1 NORMAL
                "bufferView": 1, "componentType": 5126, "count": len(normals),
                "type": "VEC3",
            },
            {  # 2 TEXCOORD_0
                "bufferView": 2, "componentType": 5126, "count": len(uvs),
                "type": "VEC2",
            },
            {  # 3 INDICES
                "bufferView": 3, "componentType": 5123, "count": len(indices),
                "type": "SCALAR",
            },
        ],
    }

    json_str = json.dumps(json_data, separators=(',', ':'))
    json_bytes = pad4_spaces(json_str.encode('utf-8'))
    bin_data = pad4_zeros(bin_data)

    # GLB Header
    glb_header = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(json_bytes) + 8 + len(bin_data))
    # JSON Chunk
    json_chunk = struct.pack('<I', len(json_bytes)) + struct.pack('<I', 0x4E4F534A) + json_bytes
    # BIN Chunk
    bin_chunk = struct.pack('<I', len(bin_data)) + struct.pack('<I', 0x004E4942) + bin_data

    return glb_header + json_chunk + bin_chunk


# ---------------------------------------------------------------------------
# 5. 封面图转纹理
# ---------------------------------------------------------------------------

def cover_to_texture(cover_path, tex_size=(2048, 1024)):
    """将展品封面图转换为适合圆柱映射的纹理。中央放照片，两侧边缘色延伸。"""
    img = Image.open(cover_path).convert('RGBA')
    w, h = img.size

    # 目标纹理，米白陶瓷底色
    tex = Image.new('RGB', tex_size, (245, 240, 232))

    # 按纹理高度等比缩放封面图
    scale = tex_size[1] / h
    new_w = max(1, int(w * scale))
    new_h = tex_size[1]
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # 透明区域填充米白
    bg = Image.new('RGB', (new_w, new_h), (245, 240, 232))
    bg.paste(resized, (0, 0), resized)

    # 居中粘贴
    paste_x = (tex_size[0] - new_w) // 2
    tex.paste(bg, (paste_x, 0))

    # 两侧空隙用边缘像素水平拉伸填充
    if paste_x > 0:
        left_edge = bg.crop((0, 0, 1, new_h))
        left_stretch = left_edge.resize((paste_x, new_h), Image.LANCZOS)
        tex.paste(left_stretch, (0, 0))

        right_w = tex_size[0] - paste_x - new_w
        if right_w > 0:
            right_edge = bg.crop((new_w - 1, 0, new_w, new_h))
            right_stretch = right_edge.resize((right_w, new_h), Image.LANCZOS)
            tex.paste(right_stretch, (paste_x + new_w, 0))

    return tex


# ---------------------------------------------------------------------------
# 6. 展品配置
# ---------------------------------------------------------------------------

ITEMS = [
    {'id': 1, 'title': '青花瓷瓶', 'shape': 'meiping', 'style': 'bluewhite',
     'cover': os.path.join(BASE_DIR, 'static/image/show/JCI54553077015.png')},
    {'id': 2, 'title': '白瓷观音像', 'shape': 'guanyin', 'style': 'white',
     'cover': os.path.join(BASE_DIR, 'static/image/show/JCI54552677015.png')},
    {'id': 3, 'title': '粉彩花卉碗', 'shape': 'bowl', 'style': 'fencai',
     'cover': os.path.join(BASE_DIR, 'static/image/show/JCI54554677015.png')},
    {'id': 4, 'title': '汝窑天青釉盘', 'shape': 'plate', 'style': 'celadon',
     'cover': os.path.join(BASE_DIR, 'static/image/show/jc14785862.png')},
    {'id': 5, 'title': '龙泉青瓷梅瓶', 'shape': 'meiping', 'style': 'celadon',
     'cover': os.path.join(BASE_DIR, 'static/image/show/JJI54557705330.png')},
    {'id': 6, 'title': '唐三彩骆驼', 'shape': 'jar', 'style': 'sancai',
     'cover': os.path.join(BASE_DIR, 'static/image/show/JJI54553554409.png')},
    {'id': 7, 'title': '钧窑玫瑰紫釉洗', 'shape': 'washer', 'style': 'jun'},
    {'id': 8, 'title': '定窑白釉刻花莲纹盘', 'shape': 'plate', 'style': 'white'},
    {'id': 9, 'title': '哥窑金丝铁线瓶', 'shape': 'vase', 'style': 'ge'},
    {'id': 10, 'title': '建窑兔毫盏', 'shape': 'cup', 'style': 'black'},
    {'id': 11, 'title': '磁州窑白地黑花罐', 'shape': 'jar', 'style': 'cizhou'},
    {'id': 12, 'title': '紫砂茶壶', 'shape': 'jar', 'style': 'zisha'},
    {'id': 13, 'title': '釉里红高足杯', 'shape': 'cup', 'style': 'red'},
    {'id': 14, 'title': '斗彩鸡缸杯', 'shape': 'cup', 'style': 'doucai'},
    {'id': 15, 'title': '珐琅彩花卉瓶', 'shape': 'yuhuchun', 'style': 'famillerose'},
    {'id': 16, 'title': '黑陶蛋壳杯', 'shape': 'cup', 'style': 'black'},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"输出目录: {OUTPUT_DIR}")

    for item in ITEMS:
        shape_fn = SHAPE_BUILDERS.get(item['shape'], make_vase)
        profile = shape_fn()

        tex = generate_texture(item['style'], seed=item['id'], size=(1024, 1024))

        verts, norms, uvs, idxs = generate_lathe(profile, segments=64)
        glb_bytes = build_glb(verts, norms, uvs, idxs, tex)

        filename = f"exhibit_{item['id']}.glb"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(glb_bytes)

        size_kb = len(glb_bytes) / 1024
        print(f"  [{item['id']:2d}] {item['title']:12s} ({item['shape']:8s}/{item['style']:10s}) -> {filename} ({size_kb:.1f} KB)")

    print("\n全部生成完毕!")


if __name__ == '__main__':
    main()
