import warnings
from itertools import product
from tqdm.notebook import tqdm
import numpy as np
import pandas as pd
from seaborn import color_palette
from shapely.geometry import box
from shapely import affinity
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from skimage import img_as_uint
from skimage.color import rgb2grey
from skimage.io import imread
from skimage.external.tifffile import TiffWriter

from renderapi.render import format_preamble
from renderapi.stack import (get_stack_bounds,
                             get_bounds_from_z,
                             get_z_values_for_stack)
from renderapi.image import get_bb_image
from renderapi.errors import RenderError

from .render_pandas import create_stacks_DataFrame


__all__ = ['render_bbox_image',
           'render_tileset_image',
           'render_stack_images',
           'render_layer_images',
           'write_tif',
           'plot_tile_map']


def render_bbox_image(stack, z, bbox, width=1024, render=None,
                      **renderapi_kwargs):
    """Renders an image given the specified bounding box

    Parameters
    ----------
    stack : str
        Input stack from which to render bbox image
    z : float
        Z layer at which to render bbox image
    bbox : list, tuple, array-like
        Coordinates of bounding box (minx, miny, maxx, maxy)
    width : float
        Width of rendered tileset image in pixels
    render : `renderapi.render.RenderClient`
        `render-ws` instance

    Returns
    -------
    image : ndarray
        Rendered bounding box image

    Notes
    -----
    Differs from `renderapi.image.get_bb_image` parameters:
        (x0, y0, width, height, scale)
    """
    # Unpack bbox
    x = bbox[0]
    y = bbox[1]
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    s = width / (bbox[2] - bbox[0])

    # Render image bounding box image as tif
    image = get_bb_image(stack=stack, z=z, x=x, y=y,
                         width=w, height=h, scale=s,
                         render=render,
                         **renderapi_kwargs)
    # Sometimes it does not work
    if isinstance(image, RenderError):
        request_url = format_preamble(
            host=render.DEFAULT_HOST,
            port=render.DEFAULT_PORT,
            owner=render.DEFAULT_OWNER,
            project=render.DEFAULT_PROJECT,
            stack=stack) + \
            f"/z/{z:.0f}/box/{x:.0f},{y:.0f},{w:.0f},{h:.0f},{s}/png-image"
        print(f"Failed to load {request_url}.")
    else:
        return image


def render_tileset_image(stack, z, width=1024, render=None,
                         **renderapi_kwargs):
    """Renders an image of a tileset

    Parameters
    ----------
    stack : str
        Stack with which to render the tileset image
    z : float
        Z value of stack at which to render tileset image
    width : float
        Width of rendered tileset image in pixels
    render : `renderapi.render.RenderClient`
        `render-ws` instance

    Returns
    -------
    image : ndarray
        Rendered image of the specified tileset
    """
    # Get bbox for z layer from stack bounds
    bounds = get_bounds_from_z(stack=stack,
                               z=z,
                               render=render)
    bbox = [bounds[k] for k in ['minX', 'minY', 'maxX', 'maxY']]
    # Render bbox image
    image = render_bbox_image(stack=stack,
                              z=z,
                              bbox=bbox,
                              width=width,
                              render=render,
                              **renderapi_kwargs)
    return image


def render_stack_images(stack, width=1024, render=None,
                        **renderapi_kwargs):
    """Renders tileset images for a given stack

    Parameters
    ----------
    stack : str
        Stack with which to render images for all z values
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    width : float
        Width of rendered tileset image in pixels
    
    Returns
    -------
    images : list
        List of tileset images comprising the stack
    """
    # Get z values of stack
    z_values = get_z_values_for_stack(stack=stack,
                                      render=render)
    # Get bbox of stack from stack bounds
    bounds = get_stack_bounds(stack=stack,
                              render=render)
    bbox = [bounds[k] for k in ['minX', 'minY', 'maxX', 'maxY']]
    # Loop through z values and collect images
    images = {}
    for z in tqdm(z_values, leave=False):
        image = render_bbox_image(stack=stack,
                                  z=z,
                                  bbox=bbox,
                                  width=width,
                                  render=render,
                                  **renderapi_kwargs)
        images[z] = image
    return images


def render_layer_images(stacks, z, width=1024, render=None,
                        **renderapi_kwargs):
    """Renders tileset images for a given layer

    Parameters
    ----------
    stacks : list
        List of stacks to with which to render layer images
    z : float
        Z value of stacks at which to render layer images
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    width : float
        Width of rendered layer images in pixels
    """
    # Loop through stacks and collect images
    images = {}
    for stack in tqdm(stacks, leave=False):
        image = render_tileset_image(stack=stack,
                                     z=z,
                                     width=width,
                                     render=render,
                                     **renderapi_kwargs)
        images[stack] = image
    return images


def render_tile_with_neighbors(stack, tileId, render=None):
    """
    """
    pass


def write_tif(fp, image):
    """
    """
    # Convert to grey scale 16-bit image
    with warnings.catch_warnings():      # Suppress precision
        warnings.simplefilter('ignore')  # loss warnings
        image = img_as_uint(rgb2grey(image))

    # Save to disk with `TiffWriter`
    fp.parent.mkdir(parents=False, exist_ok=True)
    with TiffWriter(fp.as_posix()) as tif:
        tif.save(image)


def plot_tile_map(stacks, render=None):
    """Plots tiles (as matplotlib patches) in `render-ws`

    Parameters
    ----------
    stacks : list
        List of stacks to plot
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    """

    # Create stacks DataFrame
    df_stacks = create_stacks_DataFrame(stacks=stacks,
                                        render=render)

    # Specify stacks and sections for plotting
    stacks_2_plot = df_stacks['stack'].unique().tolist()
    sections_2_plot = df_stacks['sectionId'].unique().tolist()

    # Set up figure
    ncols = len(sections_2_plot)
    fig, axes = plt.subplots(ncols=ncols, squeeze=False,
                             figsize=(8*ncols, 8))
    axmap = {k: v for k, v in zip(sections_2_plot, axes.flat)}
    cmap = {k: v for k, v in zip(stacks_2_plot,
                                 color_palette(n_colors=len(stacks_2_plot)))}

    # Iterate through layers
    for sectionId, layer in tqdm(df_stacks.groupby('sectionId')):
        # Collect all tiles in each layer to determine bounds
        boxes = []
        # Set axis
        ax = axmap[sectionId]
        # Collect legend handles
        handles = []

        # Loop through tilesets within each layer
        for stack, tileset in layer.groupby('stack'):

            # Loop through each tile
            for i, tile in tileset.reset_index().iterrows():

                # Create `shapely.box` resembling raw image tile
                b = box(0, 0, tile['width'], tile['height'])
                # Apply transforms to `shapely.box`
                for tform in tile['tforms']:
                    A = (tform.M[:2, :2].ravel().tolist() +
                         tform.M[:2,  2].ravel().tolist())
                    b = affinity.affine_transform(b, A)
                boxes.append(b)

                # Get coordinates of `shapely.box` to plot matplotlib polygon patch
                xy = np.array(b.exterior.xy).T
                p = Polygon(xy, color=cmap[stack], alpha=0.2, label=stack)
                # Add patch to axis
                if i != 0: ax.add_patch(p)             # Only add first patch
                else: handles.append(ax.add_patch(p))  # to legend handles
                # Label first tile in tileset
                x, y = np.array(b.centroid.xy).ravel()
                s = f"{stack}\n{sectionId}\n"\
                    f"{tile['imageCol']:02.0f}x{tile['imageRow']:02.0f}"
                if i == 0: ax.text(x, y, s, ha='center', va='center')

        # Axis aesthetics
        ax.set_title(sectionId)
        ax.legend(handles=handles, loc='lower right')
        ax.set_xlabel('X [px]')
        ax.set_ylabel('Y [px]')
        # Determine bounds
        bounds = np.swapaxes([b.exterior.xy for b in boxes], 1, 2).reshape(-1, 2)
        ax.set_xlim(bounds[:, 0].min(), bounds[:, 0].max())
        ax.set_ylim(bounds[:, 1].min(), bounds[:, 1].max())
        ax.invert_yaxis()
        ax.set_aspect('equal')


def plot_stacks(stacks, z_values=None, width=1024, render=None,
                **renderapi_kwargs):
    """Renders and plots tileset images for the given stacks"""
    # Create DataFrame from stacks
    df_stacks = create_stacks_DataFrame(stacks=stacks,
                                        render=render)
    if z_values is None:
        z_values = df_stacks['z'].unique().tolist()

    # Set up figure
    nrows = len(stacks)
    ncols = len(z_values)
    fig, axes = plt.subplots(nrows, ncols, squeeze=False,
                             figsize=(8*ncols, 8*nrows))
    axmap = {k: v for k, v in zip(product(stacks, z_values), axes.flat)}

    # Iterate through tilesets
    for (stack, z), tileset in tqdm(df_stacks.groupby(['stack', 'z'])):

        # Render tileset image
        image = render_tileset_image(stack=stack,
                                     z=z,
                                     width=width,
                                     render=render,
                                     **renderapi_kwargs)

        # Get extent of tileset image in render-space
        bounds = get_bounds_from_z(stack=stack,
                                   z=z,
                                   render=render)
        extent = [bounds[k] for k in ['minX', 'maxX', 'minY', 'maxY']]

        # Plot image
        ax = axmap[(stack, z)]
        ax.imshow(image, origin='lower', extent=extent)
        # Axis aesthetics
        ax.invert_yaxis()
        sectionId = tileset['sectionId'].iloc[0]
        ax.set_title(f"{stack}\n{z} | {sectionId}")
        ax.set_xlabel('X [px]')
        ax.set_ylabel('Y [px]')
