import matplotlib.pyplot as plt
import yaml
import torch
from PIL import Image
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
import os


def image_grid(
    images,
    rows=None,
    cols=None,
    fill: bool = True,
    show_axes: bool = False,
    rgb: bool = True,
):
    """
    A util function for plotting a grid of images.

    Args:
        images: (N, H, W, 4) array of RGBA images
        rows: number of rows in the grid
        cols: number of columns in the grid
        fill: boolean indicating if the space between images should be filled
        show_axes: boolean indicating if the axes of the plots should be visible
        rgb: boolean, If True, only RGB channels are plotted.
            If False, only the alpha channel is plotted.

    Returns:
        None
    """
    if (rows is None) != (cols is None):
        raise ValueError("Specify either both rows and cols or neither.")

    if rows is None:
        rows = len(images)
        cols = 1

    gridspec_kw = {"wspace": 0.0, "hspace": 0.0} if fill else {}
    fig, axarr = plt.subplots(rows, cols, gridspec_kw=gridspec_kw, figsize=(15, 9))
    bleed = 0
    fig.subplots_adjust(left=bleed, bottom=bleed, right=(1 - bleed), top=(1 - bleed))

    for ax, im in zip(axarr.ravel(), images):
        if rgb:
            # only render RGB channels
            ax.imshow(im[..., :3])
        else:
            # only render Alpha channel
            ax.imshow(im[..., 3])
        if not show_axes:
            ax.set_axis_off()



def read_yaml_config(path):

    with open(path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return config


def get_device():

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        torch.cuda.set_device(device)
        print('USING GPU')
    else:
        device = torch.device("cpu")
        print('USING CPU')

    return device


def seed_everything(seed):
    import random, os
    import numpy as np
    import torch
    
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = True
    

def write_image_metadata(img_path, data: str, tag_hex = 0x9286):
    '''
    Info - dict with params you want write directly into image
    '''
    img = Image.open(img_path)
    exif = img.getexif()
    exif[tag_hex] = data
    img.save(img_path, exif=exif)

    
def read_image_metadata(img_path, tag_hex = 0x9286):
    
    img = Image.open(img_path)
    metadata = img.getexif()[tag_hex]
    
    return metadata

def spherical_to_cartesian(azimuth, elevation, radius=1):
    azimuth_rad = np.radians(azimuth)
    elevation_rad = np.radians(elevation)
    
    x = radius * np.sin(elevation_rad) * np.cos(azimuth_rad)
    y = radius * np.sin(elevation_rad) * np.sin(azimuth_rad)
    z = radius * np.cos(elevation_rad)
    
    return x, y, z

def save_visualization(angles, save_path):

    azimuths, elevations = angles[:, 0], angles[:, 1]
    x, y, z = spherical_to_cartesian(azimuths, elevations)

    df = pd.DataFrame({'x': x, 'y': y, 'z': z})
    fig = px.scatter_3d(df, x='x', y='y', z='z')

    save_path = os.path.join(save_path, 'points_distribution.html')

    pio.write_html(fig, file=save_path, auto_open=False)