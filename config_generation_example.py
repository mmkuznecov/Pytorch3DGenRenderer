import os
import yaml

def create_yaml(obj_filename: str, save_dir: str, filename: str, save: str):
    # Create a dictionary with your parameters.
    # The dictionary keys should match the YAML keys.
    config = {
        "image_size": 224,
        "num_samples": 20,
        "randomize": True,
        "obj_filename": obj_filename,
        "sampling_method": "fibonacci_sphere",
        "seed": 42,
        "save_dir": save_dir,
        "save_gif": True,
        "save_vis": True
    }

    # Ensure the save directory exists
    if not os.path.exists(save):
        os.makedirs(save)

    # Define the filename for the YAML file.
    # Let's say we want to save it in the same directory as the OBJ file,
    # with the name 'config.yaml'.
    yaml_filename = os.path.join(save, f'{filename}.yaml')

    with open(yaml_filename, 'w') as yaml_file:
        yaml.dump(config, yaml_file, default_flow_style=False)

def main():

    OBJECTS_DIR = 'data'
    SAVE_DIR = 'params'

    for model_dir in os.listdir(OBJECTS_DIR):
        path = os.path.join(OBJECTS_DIR, model_dir)
        # considering we have only one .obj file per dir
        obj_file = [file for file in os.listdir(path) if file.endswith('.obj')][0]
        save_name = obj_file.split('.')[0]
        obj_file = os.path.join(path, obj_file)
        create_yaml(obj_file, path, save_name, SAVE_DIR)

if __name__ == "__main__":
    main()