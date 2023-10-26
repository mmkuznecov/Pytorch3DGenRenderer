import os
import torch
import numpy as np
from pytorch3d.io import load_obj
from pytorch3d.structures import Meshes
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras,
    RasterizationSettings,
    MeshRenderer,
    MeshRasterizer,
    SoftPhongShader,
    TexturesAtlas,
    AmbientLights
)

from PIL import Image
from renderer.utils import get_device

class Render:

    def __init__(self):

        self.device = get_device()

    def get_mesh(self, obj_filename):

        """
        Generates Meshes object and initializes the mesh with vertices, faces,
        and textures.

        Args:
            obj_filename: str, path to the 3D obj filename
            device: str, the torch device containing a device type ('cpu' or
            'cuda')

        Returns:
            mesh: Meshes object
        """
        # Get vertices, faces, and auxiliary information
        
        verts, faces, aux = load_obj(
            obj_filename,
            device=self.device,
            load_textures=True,
            create_texture_atlas=True,
            texture_atlas_size=4,
            texture_wrap="repeat"
            )
        # Create a textures object
        atlas = aux.texture_atlas
        # Create Meshes object
        
        vertMax = torch.max(verts, 0)
        vertMin = torch.min(verts, 0)
        verts -= ((vertMax[0] + vertMin[0])/2)
        
        mesh = Meshes(
            verts=[verts],
            faces=[faces.verts_idx],
            textures=TexturesAtlas(atlas=[atlas]),) 
        return mesh
    
    def correct_obj_file(self, obj_filename):

        dirString = os.path.dirname(obj_filename)
        f = open(obj_filename, "r")
        lines = f.readlines()
        noMatLine = True
        for i in range(len(lines)):
            if "usemtl" in lines[i]:
                noMatLine = False
                break
                
        if noMatLine:
            bufferFullName = dirString + "filtered.txt"
            writer = open(bufferFullName, 'w')
            for i in range(len(lines)):
                if ("f" == lines[i][0] and " " == lines[i][1]) and noMatLine:
                    writer.write("usemtl material_0\n")
                    noMatLine = False
                writer.write(lines[i])        
            os.remove(obj_filename)
            os.rename(bufferFullName, obj_filename)
            print("OBJ FILE WAS CORRECTED")

    
    def calculate_camera_distance(self, mesh, fov_degrees=60.0, image_width_pixels=1024, desired_percentage=0.8):
        """
        Calculate the camera distance based on the size of the mesh, the FOV, and the image size in pixels.

        Args:
            mesh: Meshes object
            fov_degrees: float, field of view in degrees
            image_width_pixels: int, the width of the rendered image in pixels (optional)
            desired_percentage: float, the desired percentage of the object size in the final image (default is 0.8)

        Returns:
            dist: float, the calculated distance
        """

        # WL additions
        bounding_box = mesh.get_bounding_boxes()

        aLow = bounding_box[0][0][0].cpu().numpy()
        aHigh = bounding_box[0][0][1].cpu().numpy()
        
        bLow = bounding_box[0][1][0].cpu().numpy()
        bHigh = bounding_box[0][1][1].cpu().numpy()
        
        cLow = bounding_box[0][2][0].cpu().numpy()
        cHigh = bounding_box[0][2][1].cpu().numpy()
        
        aSquared = np.power(aHigh - aLow, 2)
        bSquared = np.power(bHigh - bLow, 2)
        cSquared = np.power(cHigh - cLow, 2)
        max_diagonal = np.sqrt(aSquared + bSquared + cSquared)
        
        fov_radians = np.radians(fov_degrees)

        if (max_diagonal < 0.78):
            dist = 0.68
        else:
            desired_width_pixels = image_width_pixels * desired_percentage    
            focal_length_pixels = (image_width_pixels / 2) / np.tan(fov_radians / 2)
            dist = (max_diagonal * focal_length_pixels) / desired_width_pixels
        
        return dist
    

    def get_renderer(self, image_size, dist, elev, azim):
        """
        Generates a mesh renderer by combining a rasterizer and a shader.

        Args:
            image_size: int, the size of the rendered .png image
            dist: int, distance between the camera and 3D object
            device: str, the torch device containing a device type ('cpu' or
            'cuda')
            elev: list, contains elevation values
            azim: list, contains azimuth angle values

        Returns:
            renderer: MeshRenderer class
        """
        # Initialize the camera with camera distance, elevation, azimuth angle,
        # and image size
        R, T = look_at_view_transform(dist=dist, elev=elev, azim=azim)
        cameras = FoVPerspectiveCameras(device=self.device, R=R, T=T, fov=60.0, zfar = dist * 2)
        raster_settings = RasterizationSettings(
            image_size=image_size,
            blur_radius=0.0,
            faces_per_pixel=5,
        )
        # Initialize rasterizer by using a MeshRasterizer class
        rasterizer = MeshRasterizer(
            cameras=cameras,
            raster_settings=raster_settings
        )
        # The textured phong shader interpolates the texture uv coordinates for
        # each vertex, and samples from a texture image.
        shader = SoftPhongShader(device = self.device, cameras=cameras, lights=AmbientLights(device=self.device, ambient_color = (1.0, 1.0, 1.0)))
        #shader = HardPhongShader(device=device, cameras=cameras)  
        
        # Create a mesh renderer by composing a rasterizer and a shader
        renderer = MeshRenderer(rasterizer, shader)
        return renderer
    
    def render_image(self, renderer, mesh):
        image = renderer(mesh)
        image_data = image[0, ...].cpu().numpy()  # Shape should be (height, width, 4)
    
        # Convert RGB channels to uint8
        rgb_data = (image_data[..., :3] * 255).astype(np.uint8)
        
        # Convert alpha channel to uint8
        alpha_data = (image_data[..., 3] * 255).astype(np.uint8).reshape(rgb_data.shape[0], rgb_data.shape[1], 1)
        
        # Make transparent pixels black
        mask = alpha_data == 0
        rgb_data[mask[..., 0]] = 0
        
        # Concatenate RGB and alpha to get final image data
        final_image_data = np.concatenate([rgb_data, alpha_data], axis=-1)
        
        pil_image = Image.fromarray(final_image_data)
        
        return pil_image

    
    def compile_all_steps(self, image_size, dist, elev, azim, mesh):
        """
        Combines the above steps.

        Args:
            image_size: int, the size of the rendered .png image
            dist: int, distance between the camera and 3D object
            device: str, the torch device containing a device type ('cpu' or
            'cuda')
            elev: list, contains elevation values
            azim: list, contains azimuth angle values
            obj_filename: str, path to the 3D obj filename

        Returns:
            None
        """

        renderer = self.get_renderer(image_size, dist, elev, azim)
        image = self.render_image(renderer, mesh)
        return image