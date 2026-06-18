import os
import math
import random
from PIL import Image, ImageDraw


class SimpleRenderer:
    def __init__(self, size=800):
        self.size = size

    def render_vase(self, profile, texture_img):
        img = Image.new('RGBA', (self.size, self.size), (20, 20, 22, 255))
        draw = ImageDraw.Draw(img)
        tex_w, tex_h = texture_img.size
        tex_data = texture_img.load()

        scale = 250
        center_x = self.size // 2
        center_y = self.size // 2 + 50

        for angle_deg in range(360):
            angle_rad = math.radians(angle_deg)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            points_3d = []
            for (x, y) in profile:
                px = x * cos_a
                py = y * scale + center_y
                pz = x * sin_a

                if pz > 0:
                    points_3d.append((px * scale + center_x, py))

            if len(points_3d) >= 2:
                for i in range(len(points_3d) - 1):
                    x1, y1 = points_3d[i]
                    x2, y2 = points_3d[i + 1]

                    y = profile[i][1]
                    u = int((angle_deg / 360) * (tex_w - 1))
                    v = int(((y + 1) / 2) * (tex_h - 1))
                    u = max(0, min(u, tex_w - 1))
                    v = max(0, min(v, tex_h - 1))
                    color = tex_data[u, v]

                    light = 0.5 + 0.3 * cos_a
                    light = max(0.3, min(1.0, light))
                    r = int(color[0] * light)
                    g = int(color[1] * light)
                    b = int(color[2] * light)

                    draw.line([(x1, y1), (x2, y2)], fill=(r, g, b), width=2)

        draw.ellipse([center_x - 150, center_y + 150 - 20, center_x + 150, center_y + 150 + 20], fill=(0, 0, 0, 80))

        return img


def generate_texture(style, seed=1, size=(512, 512)):
    random.seed(seed)
    img = Image.new('RGBA', size, (245, 242, 235, 255))
    draw = ImageDraw.Draw(img)
    w, h = size

    if style == 'bluewhite':
        draw.rectangle([0, 0, w, h], fill=(245, 242, 235))

        for i in range(20):
            cx = w * (i + 0.5) / 20
            cy = h * 0.1
            points = [
                (cx, cy - h*0.05),
                (cx - w*0.015, cy + h*0.03),
                (cx - w*0.006, cy + h*0.03),
                (cx, cy + h*0.015),
                (cx + w*0.006, cy + h*0.03),
                (cx + w*0.015, cy + h*0.03),
            ]
            draw.polygon(points, fill=(25, 50, 90))

        for band_idx in range(3):
            band_y = h*(0.25 + band_idx*0.18)
            for i in range(10):
                cx = w*(i + random.uniform(0.2, 0.8))/10
                cy = band_y + random.uniform(-h*0.03, h*0.03)
                r = w*0.02

                for petal_idx in range(6):
                    angle = petal_idx*60
                    rad = math.radians(angle)
                    px = cx + math.cos(rad)*r*0.7
                    py = cy + math.sin(rad)*r*0.7
                    pr = r*0.35
                    draw.ellipse([px-pr, py-pr*0.5, px+pr, py+pr*0.5], fill=(30, 60, 100))
                draw.ellipse([cx - r*0.15, cy - r*0.1, cx + r*0.15, cy + r*0.1], fill=(25, 50, 85))

        petal_count = 20
        for i in range(petal_count):
            cx = w*(i + 0.5)/petal_count
            cy = h*0.92
            points = [
                (cx, cy + h*0.05),
                (cx - w*0.012, cy + h*0.01),
                (cx - w*0.008, cy - h*0.04),
                (cx, cy - h*0.05),
                (cx + w*0.008, cy - h*0.04),
                (cx + w*0.012, cy + h*0.01),
            ]
            draw.polygon(points, fill=(28, 55, 95))

    elif style == 'celadon':
        draw.rectangle([0, 0, w, h], fill=(160, 170, 150))
        for i in range(150):
            x1, y1 = random.randint(0, w), random.randint(0, h)
            x2 = x1 + random.randint(-40, 40)
            y2 = y1 + random.randint(-40, 40)
            draw.line([(x1, y1), (x2, y2)], fill=(130, 140, 120), width=1)

    elif style == 'fencai':
        draw.rectangle([0, 0, w, h], fill=(250, 245, 235))
        colors = [(200, 100, 120), (120, 150, 200), (150, 200, 150), (220, 200, 100)]
        for i in range(15):
            cx = random.randint(80, w-80)
            cy = random.randint(80, h-80)
            r = random.randint(30, 60)
            color = random.choice(colors)
            for j in range(6):
                ang = j * 60
                px = cx + math.cos(math.radians(ang)) * r * 0.6
                py = cy + math.sin(math.radians(ang)) * r * 0.6
                draw.ellipse([px-15, py-15, px+15, py+15], fill=color)
            draw.ellipse([cx-15, cy-15, cx+15, cy+15], fill=(250, 220, 100))

    elif style == 'sancai':
        draw.rectangle([0, 0, w, h], fill=(240, 220, 180))
        for i in range(40):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(25, 80)
            c = random.choice([(100, 180, 100), (180, 180, 80), (160, 100, 80)])
            draw.ellipse([x-r, y-r, x+r, y+r], fill=c)

    elif style == 'jun':
        draw.rectangle([0, 0, w, h], fill=(130, 150, 160))
        for i in range(12):
            cx = random.randint(80, w-80)
            cy = random.randint(80, h-80)
            r = random.randint(40, 100)
            for dy in range(-r, r):
                for dx in range(-r, r):
                    if dx*dx + dy*dy < r*r:
                        d = math.sqrt(dx*dx + dy*dy) / r
                        if 0 <= cx+dx < w and 0 <= cy+dy < h:
                            img.putpixel((cx+dx, cy+dy),
                                         (int(150 + 105*(1-d)), int(80 + 70*(1-d)), int(100 + 60*(1-d))))

    elif style == 'white':
        draw.rectangle([0, 0, w, h], fill=(255, 252, 245))

    elif style == 'ge':
        draw.rectangle([0, 0, w, h], fill=(210, 205, 190))
        for i in range(120):
            x1, y1 = random.randint(0, w), random.randint(0, h)
            for j in range(3):
                x2 = x1 + random.randint(-50, 50)
                y2 = y1 + random.randint(-50, 50)
                color = (40, 30, 20) if random.random() > 0.7 else (150, 120, 60)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=2 if random.random() > 0.8 else 1)
                x1, y1 = x2, y2

    elif style == 'black':
        draw.rectangle([0, 0, w, h], fill=(20, 18, 20))
        for i in range(80):
            x = random.randint(0, w)
            y_start = random.randint(0, int(h*0.5))
            length = random.randint(80, 200)
            color = (180, 140, 80)
            for dy in range(length):
                if y_start + dy < h:
                    wobble = int(math.sin(dy * 0.12) * 2)
                    if 0 <= x + wobble < w:
                        draw.point((x + wobble, y_start + dy), fill=color)

    elif style == 'zisha':
        draw.rectangle([0, 0, w, h], fill=(140, 80, 60))
        for i in range(3000):
            x = random.randint(0, w)
            y = random.randint(0, h)
            c = random.randint(100, 160)
            draw.point((x, y), fill=(c, c-40, c-60))

    elif style == 'red':
        draw.rectangle([0, 0, w, h], fill=(245, 242, 235))
        for i in range(12):
            cx = random.randint(80, w-80)
            cy = random.randint(80, h-80)
            r = random.randint(25, 60)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(150, 60, 60))

    elif style == 'doucai':
        draw.rectangle([0, 0, w, h], fill=(245, 242, 235))
        colors = [(200, 60, 60), (60, 120, 180), (80, 160, 80), (220, 180, 80)]
        for i in range(10):
            cx = random.randint(80, w-80)
            cy = random.randint(80, h-80)
            r = random.randint(25, 50)
            color = random.choice(colors)
            for j in range(5):
                ang = j * 72
                px = cx + math.cos(math.radians(ang)) * r * 0.7
                py = cy + math.sin(math.radians(ang)) * r * 0.7
                draw.ellipse([px-12, py-12, px+12, py+12], fill=color, outline=(30, 30, 30), width=1)
            draw.ellipse([cx-12, cy-12, cx+12, cy+12], fill=(250, 220, 100), outline=(30, 30, 30), width=1)

    elif style == 'famillerose':
        draw.rectangle([0, 0, w, h], fill=(245, 242, 235))
        colors = [(220, 100, 100), (100, 140, 200), (140, 180, 140), (240, 220, 120)]
        for i in range(8):
            cx = random.randint(100, w-100)
            cy = random.randint(100, h-100)
            r = random.randint(40, 80)
            color = random.choice(colors)
            for j in range(8):
                ang = j * 45
                px = cx + math.cos(math.radians(ang)) * r * 0.7
                py = cy + math.sin(math.radians(ang)) * r * 0.7
                draw.ellipse([px-20, py-20, px+20, py+20], fill=color)
            draw.ellipse([cx-20, cy-20, cx+20, cy+20], fill=(250, 220, 100))

    return img


def make_meiping():
    pts = []
    for i in range(50):
        t = i / 49
        if t < 0.12:
            x = 0.12 + t * 1.08
        elif t < 0.35:
            x = 0.25 + (t - 0.12) * 2.17
        elif t < 0.7:
            x = 0.75 - (t - 0.35) * 1.43
        else:
            x = 0.25 - (t - 0.7) * 0.83
        y = -1.2 + t * 2.4
        pts.append((max(0.05, x), y))
    return pts


def make_vase():
    pts = []
    for i in range(40):
        t = i / 39
        x = 0.15 + 0.5 * math.sin(t * math.pi)
        y = -1.0 + t * 2.0
        pts.append((x, y))
    return pts


def make_plate():
    pts = []
    for i in range(30):
        t = i / 29
        if t < 0.7:
            x = 0.05 + t * 1.36
        else:
            x = 1.0 - (t - 0.7) * 1.5
        y = -0.25 + t * 0.5
        pts.append((x, y))
    return pts


def make_bowl():
    pts = []
    for i in range(30):
        t = i / 29
        x = 0.08 + 0.6 * t
        y = -0.6 + t * 1.2
        pts.append((x, y))
    return pts


def make_guanyin():
    pts = []
    for i in range(40):
        t = i / 39
        x = 0.15 + 0.35 * math.sin(t * math.pi * 0.8)
        y = -1.2 + t * 2.4
        pts.append((x, y))
    return pts


def make_jar():
    pts = []
    for i in range(35):
        t = i / 34
        if t < 0.15:
            x = 0.15 + t * 3.0
        elif t < 0.85:
            x = 0.6
        else:
            x = 0.6 - (t - 0.85) * 4.0
        y = -1.0 + t * 2.0
        pts.append((max(0.05, x), y))
    return pts


def make_cup():
    pts = []
    for i in range(25):
        t = i / 24
        x = 0.1 + 0.4 * t
        y = -0.5 + t * 1.0
        pts.append((x, y))
    return pts


def make_yuhuchun():
    pts = []
    for i in range(40):
        t = i / 39
        if t < 0.15:
            x = 0.35 - t * 1.67
        elif t < 0.45:
            x = 0.1 + (t - 0.15) * 2.14
        elif t < 0.85:
            x = 0.75 - (t - 0.45) * 1.5
        else:
            x = 0.15 - (t - 0.85) * 1.5
        y = -1.2 + t * 2.4
        pts.append((max(0.05, x), y))
    return pts


def make_washer():
    pts = []
    for i in range(30):
        t = i / 29
        if t < 0.5:
            x = 0.08 + t * 1.84
        else:
            x = 1.0 - (t - 0.5) * 1.84
        y = -0.3 + t * 0.6
        pts.append((x, y))
    return pts


def main():
    output_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'pseudo3d')
    os.makedirs(output_root, exist_ok=True)

    ITEMS = [
        {'id': 1, 'shape': 'meiping', 'style': 'bluewhite'},
        {'id': 2, 'shape': 'guanyin', 'style': 'white'},
        {'id': 3, 'shape': 'bowl', 'style': 'fencai'},
        {'id': 4, 'shape': 'plate', 'style': 'celadon'},
        {'id': 5, 'shape': 'meiping', 'style': 'celadon'},
        {'id': 6, 'shape': 'jar', 'style': 'sancai'},
        {'id': 7, 'shape': 'washer', 'style': 'jun'},
        {'id': 8, 'shape': 'plate', 'style': 'white'},
        {'id': 9, 'shape': 'vase', 'style': 'ge'},
        {'id': 10, 'shape': 'cup', 'style': 'black'},
        {'id': 11, 'shape': 'jar', 'style': 'white'},
        {'id': 12, 'shape': 'jar', 'style': 'zisha'},
        {'id': 13, 'shape': 'cup', 'style': 'red'},
        {'id': 14, 'shape': 'cup', 'style': 'doucai'},
        {'id': 15, 'shape': 'yuhuchun', 'style': 'famillerose'},
        {'id': 16, 'shape': 'cup', 'style': 'black'},
    ]

    SHAPE_BUILDERS = {
        'vase': make_vase,
        'plate': make_plate,
        'bowl': make_bowl,
        'guanyin': make_guanyin,
        'meiping': make_meiping,
        'jar': make_jar,
        'cup': make_cup,
        'yuhuchun': make_yuhuchun,
        'washer': make_washer,
    }

    renderer = SimpleRenderer(size=800)

    for item in ITEMS:
        print(f"生成展品 {item['id']}...")
        item_dir = os.path.join(output_root, f'exhibit_{item["id"]}')
        os.makedirs(item_dir, exist_ok=True)

        shape_fn = SHAPE_BUILDERS.get(item['shape'], make_vase)
        profile = shape_fn()
        tex = generate_texture(item['style'], seed=item['id'], size=(512, 512))

        for frame in range(36):
            angle_offset = frame * 10
            rotated_tex = tex.rotate(angle_offset)
            img = renderer.render_vase(profile, rotated_tex)

            filename = os.path.join(item_dir, f'frame_{frame}.png')
            img.save(filename)

    print("全部生成完毕！")


if __name__ == '__main__':
    main()