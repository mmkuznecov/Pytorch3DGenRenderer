from renderer.render import Render
from renderer.utils import *
import renderer.point_sampling as point_sampling
import torch.multiprocessing as mp
from multiprocessing import Process, Manager
import os
import argparse
import logging
from tqdm import tqdm
import time


def chunk_list(input_list, chunks):
    """Divide a list into N chunks."""
    return [input_list[i::chunks] for i in range(chunks)]

def process_chunk(chunk, gpu_id, progress, progress_lock, total):
    torch.cuda.set_device(gpu_id)
    renderer = Render()
    for param_file in chunk:
        try:
            
            params = read_yaml_config(param_file)

            num_samples = int(params['num_samples'])
            randomize = bool(params['randomize'])
            sampling_method = str(params['sampling_method'])
            seed = int(params['seed'])
            obj_filename = str(params['obj_filename'])
            image_size = int(params['image_size'])
            save_gif = bool(params['save_gif'])
            save_vis = bool(params['save_vis'])
            save_dir = os.path.join(str(params['save_dir']), "projections")

            if seed is not None:
                seed_everything(seed)

            sampling_func = getattr(point_sampling, sampling_method)
            angles = sampling_func(num_samples, randomize)
            renderer.correct_obj_file(obj_filename)
            mesh = renderer.get_mesh(obj_filename)

            camera_dist = renderer.calculate_camera_distance(mesh)
            frames = []

            angles_num = len(str(len(angles)))

            for idx, angle in enumerate(angles):
                azimuth, elevation = angle
                new_image = renderer.compile_all_steps(image_size, camera_dist, elevation, azimuth, mesh)

                os.makedirs(save_dir, exist_ok=True)
                
                file_to_save = f"{str(idx).zfill(angles_num)}.png"
                filename = os.path.join(save_dir, file_to_save)
                new_image.save(filename)
                
                metadata_info = ';'.join([str(elevation), str(azimuth), str(camera_dist)])
                
                write_image_metadata(filename, metadata_info)

                frames.append(new_image)

            if save_gif:
                
                frames[0].save(os.path.join(save_dir, 'moving_frames.gif'), format='GIF', append_images=frames[1:], save_all=True, duration=angles_num, loop=0)

            if save_vis:
                
                save_visualization(angles, save_dir)
            
        except Exception as e:
            logging.error(f"Error processing {param_file} on GPU {gpu_id}: {str(e)}")
        with progress_lock:
            progress.value += 1
        tqdm.write(f"GPU {gpu_id}: Processed {progress.value}/{total} param_files")

def main():

    parser = argparse.ArgumentParser(description="Render 3D objects.")
    parser.add_argument("--config", type=str, help="Path to the configuration yaml file")
    args = parser.parse_args()

    render_params = read_yaml_config(args.config)

    param_files_dir = str(render_params['params_dir_path'])
    param_files = [os.path.join(param_files_dir, f) for f in os.listdir(param_files_dir)]

    gpus_num = render_params['gpus_num']
    num_gpus = torch.cuda.device_count() if gpus_num==-1 else gpus_num
    chunks = chunk_list(param_files, num_gpus)

    mp.set_start_method('spawn', force=True)

    with Manager() as manager:
        progress = manager.Value('i', 0)  # 'i' indicates integer type
        progress_lock = manager.Lock()
        success_count = manager.Value('i', 0)
        processes = []
        pbar = tqdm(total=len(param_files))
        
        for i in range(num_gpus):
            p = Process(target=process_chunk, args=(chunks[i], i, progress, progress_lock, len(param_files)))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        pbar.close()
        total_count = len(param_files)
        success_percentage = (success_count.value / total_count) * 100
        logging.info(f"Processed {success_percentage:.2f}% of objects successfully.")

if __name__ == "__main__":
    main()