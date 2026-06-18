import os
import math
import numpy as np
from PIL import Image
import trimesh
import pyrender


def render_glb_to_frames(glb_path, output_dir, num_frames=36, width=800, height=800):
    os.makedirs(output_dir, exist_ok=True)
    
    mesh = trimesh.load(glb_path)
    
    scene = pyrender.Scene(bg_color=[20/255, 20/255, 22/255, 1.0])
    
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    
    mesh_node = pyrender.Mesh.from_trimesh(mesh)
    scene.add(mesh_node)
    
    camera = pyrender.PerspectiveCamera(yfov=math.pi / 4.0)
    camera_pose = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 3.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    scene.add(camera, pose=camera_pose)
    
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
    scene.add(light, pose=camera_pose)
    
    light2 = pyrender.DirectionalLight(color=[0.8, 0.8, 1.0], intensity=1.5)
    light_pose2 = np.array([
        [-0.5, 0.5, 0.7, 0.0],
        [0.5, 0.5, -0.5, 0.0],
        [0.5, -0.5, 0.5, 2.5],
        [0.0, 0.0, 0.0, 1.0]
    ])
    scene.add(light2, pose=light_pose2)
    
    renderer = pyrender.OffscreenRenderer(width, height)
    
    for frame in range(num_frames):
        angle = frame * (2 * math.pi / num_frames)
        
        rotation = np.array([
            [math.cos(angle), 0.0, math.sin(angle), 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-math.sin(angle), 0.0, math.cos(angle), 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        
        scene.set_pose(mesh_node, pose=rotation)
        
        color, depth = renderer.render(scene)
        
        img = Image.fromarray(color)
        output_path = os.path.join(output_dir, f'frame_{frame}.png')
        img.save(output_path)
        print(f'  保存 {output_path}')
    
    renderer.delete()


def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    models_dir = os.path.join(base_dir, 'static', 'models')
    output_root = os.path.join(base_dir, 'static', 'pseudo3d')
    os.makedirs(output_root, exist_ok=True)
    
    for i in range(1, 17):
        glb_path = os.path.join(models_dir, f'exhibit_{i}.glb')
        output_dir = os.path.join(output_root, f'exhibit_{i}')
        
        if os.path.exists(glb_path):
            print(f'渲染展品 {i}...')
            try:
                render_glb_to_frames(glb_path, output_dir, num_frames=36)
            except Exception as e:
                print(f'  错误: {e}')
        else:
            print(f'跳过展品 {i} - 模型文件不存在')
    
    print('全部渲染完成！')


if __name__ == '__main__':
    main()
