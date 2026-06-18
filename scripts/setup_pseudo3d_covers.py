import os
import shutil
from PIL import Image


def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_root = os.path.join(base_dir, 'static', 'pseudo3d')
    os.makedirs(output_root, exist_ok=True)
    
    covers = {
        1: 'image/show/JCI54553077015.png',
        2: 'image/show/JCI54552677015.png',
        3: 'image/show/JCI54554677015.png',
        4: 'image/show/jc14785862.png',
        5: 'image/show/JJI54557705330.png',
        6: 'image/show/JJI54553554409.png',
        7: 'image/show/JCI54553077015.png',
        8: 'image/show/JCI54552677015.png',
        9: 'image/show/jc14785862.png',
        10: 'image/show/JCI54554677015.png',
        11: 'image/show/JJI54557705330.png',
        12: 'image/show/JJI54553554409.png',
        13: 'image/show/JCI54553077015.png',
        14: 'image/show/JCI54552677015.png',
        15: 'image/show/JCI54554677015.png',
        16: 'image/show/jc14785862.png',
    }
    
    static_dir = os.path.join(base_dir, 'static')
    
    for item_id, cover_path in covers.items():
        src_path = os.path.join(static_dir, cover_path)
        
        if os.path.exists(src_path):
            item_dir = os.path.join(output_root, f'exhibit_{item_id}')
            os.makedirs(item_dir, exist_ok=True)
            
            img = Image.open(src_path)
            
            for frame in range(36):
                dst_path = os.path.join(item_dir, f'frame_{frame}.png')
                shutil.copy(src_path, dst_path)
            
            print(f'展品 {item_id}: 已复制封面图片')
        else:
            print(f'展品 {item_id}: 封面图片不存在 - {src_path}')
    
    print('全部完成！')


if __name__ == '__main__':
    main()
