from itertools import product
from tqdm.notebook import tqdm
import numpy as np
from seaborn import color_palette
from shapely.geometry import box
from shapely import affinity
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from renderapi.render import format_preamble
from renderapi.stack import (get_stack_bounds,
                             get_bounds_from_z,
                             get_z_values_for_stack)
from renderapi.tilespec import get_tile_spec, get_tile_specs_from_box
from renderapi.image import get_bb_image
from renderapi.errors import RenderError

from .render_pandas import create_stacks_DataFrame


__all__ = ['render_bbox_image',
           'render_partition_image',
           'render_tileset_image',
           'render_stack_images',
           'render_layer_images',
           'render_neighborhood_image',
           'plot_tile_map',
           'plot_stacks',
           'plot_neighborhoods']


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
    # Sometimes it overloads the system
    if isinstance(image, RenderError):
        request_url = format_preamble(
            host=render.DEFAULT_HOST,
            port=render.DEFAULT_PORT,
            owner=render.DEFAULT_OWNER,
            project=render.DEFAULT_PROJECT,
            stack=stack) + \
            f"/z/{z:.0f}/box/{x:.0f},{y:.0f},{w:.0f},{h:.0f},{s}/png-image"
        print(f"Failed to load {request_url}. Trying again with partitioned bboxes.")
        # Try to render image from smaller bboxes
        image = render_partition_image(stack, z, bbox, width, render,
                                       **renderapi_kwargs)
    return image


def render_partition_image(stack, z, bbox, width=1024, render=None,
                           **renderapi_kwargs):
    """Renders a bbox image from partitions"""
    # Unpack bbox
    x = bbox[0]
    y = bbox[1]
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    s = width / (bbox[2] - bbox[0])

    # Get tiles in bbox
    tiles = get_tile_specs_from_box(stack, z, x, y, w, h, s, render=render)
    # Average tile width/height
    width_p = np.mean([tile.width for tile in tiles])
    height_p = np.mean([tile.height for tile in tiles])

    # Get coordinates for partitions (sub-bboxes)
    Nx_p = int(np.ceil(w/width_p))      # num partitions in x
    Ny_p = int(np.ceil(h/height_p))     # num partitions in y
    xs_p = np.arange(x, x+w, width_p)   # x coords of partitions
    ys_p = np.arange(y, y+h, height_p)  # y coords of partitions
    ws_p = np.array((width_p,) * (Nx_p-1) + (w % width_p,))    # partition widths
    hs_p = np.array((height_p,) * (Ny_p-1) + (h % height_p,))  # partition heights
    s_p = width / width_p / Nx_p                      # scale
    # Create partitions from meshgrid
    partitions = np.array([g.ravel() for g in np.meshgrid(xs_p, ys_p)] +\
                          [g.ravel() for g in np.meshgrid(ws_p, hs_p)]).T

    # Global bbox image (to stitch together partitions)
    height = int((bbox[3]-bbox[1])/(bbox[2]-bbox[0]) * width)
    image = np.zeros((height, width))
    # Need and x, y offsets such that image starts at (0, 0)
    x0 = int(xs_p[0] * s_p)
    y0 = int(ys_p[0] * s_p)
    # Create a bbox image for each partition
    for p in tqdm(partitions[:], leave=False):
        image_p = get_bb_image(stack=stack, z=z, x=p[0], y=p[1],
                               width=p[2], height=p[3], scale=s_p,
                               render=render,
                               **renderapi_kwargs)[:,:,0]
        # Add partition to global bbox image
        x1 = int(p[0] * s_p) - x0
        x2 = x1 + int(p[2] * s_p)
        y1 = int(p[1] * s_p) - y0
        y2 = y1 + int(p[3] * s_p)
        image[y1:y2, x1:x2] = image_p

    return image.astype(image_p.dtype)


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


def render_neighborhood_image(stack, tileId, neighborhood=1, width=1024,
                              render=None, return_bbox=False,
                              **renderapi_kwargs):
    """Renders an image of the local neighborhood surrounding a tile

    Parameters
    ----------
    stack : str
        Stack from which to render neighborhood image
    tileId : str
        tileId (duh)
    neighborhood : float
        Number of tiles surrounding center tile from which to render the image
    width : float
        Width of rendered layer images in pixels
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    """
    # Make alias for neighborhood
    N = neighborhood

    # Get bounding box of specified tile
    tile_spec = get_tile_spec(stack=stack,
                              tile=tileId,
                              render=render)

    # Get width of bbox
    bbox = tile_spec.bbox
    w = bbox[2] - bbox[0]

    # Assume surrounding tiles are squares with ~same width as the center tile
    bbox_neighborhood = (bbox[0] - N*w, bbox[1] - N*w,
                         bbox[2] + N*w, bbox[3] + N*w)

    # Render image of neighborhood
    image = render_bbox_image(stack=stack,
                              z=tile_spec.z,
                              bbox=bbox_neighborhood,
                              width=width,
                              render=render,
                              **renderapi_kwargs)
    
    if return_bbox:
        return image, bbox_neighborhood
    else:
        return image



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
    fig, axes = plt.subplots(ncols=ncols, sharex=True, sharey=True,
                             squeeze=False, figsize=(8*ncols, 8))
    axmap = {k: v for k, v in zip(sections_2_plot, axes.flat)}
    cmap = {k: v for k, v in zip(stacks_2_plot,
                                 color_palette(n_colors=len(stacks_2_plot)))}
    # Collect all tiles in each layer to determine bounds
    boxes = []

    # Iterate through layers
    for sectionId, layer in tqdm(df_stacks.groupby('sectionId')):
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
        ax.grid(ls=':', alpha=0.7)
        ax.set_aspect('equal')

    # Set axis limits based on bounding boxes
    bounds = np.swapaxes([b.exterior.xy for b in boxes], 1, 2).reshape(-1, 2)
    for ax in axmap.values():
        ax.set_xlim(bounds[:, 0].min(), bounds[:, 0].max())
        ax.set_ylim(bounds[:, 1].min(), bounds[:, 1].max())
        ax.invert_yaxis()


def plot_stacks(stacks, z_values=None, width=1024, render=None,
                **renderapi_kwargs):
    """Renders and plots tileset images for the given stacks"""
    # Create DataFrame from stacks
    df_stacks = create_stacks_DataFrame(stacks=stacks,
                                        render=render)

    # Plot all z values if none are provided
    if z_values is None:
        z_values = df_stacks['z'].unique().tolist()

    # Set up figure
    nrows = len(stacks)
    ncols = len(z_values)
    fig, axes = plt.subplots(nrows, ncols, squeeze=False,
                             figsize=(8*ncols, 8*nrows))
    axmap = {k: v for k, v in zip(product(stacks, z_values), axes.flat)}

    # Iterate through tilesets
    df_2_plot = df_stacks.loc[df_stacks['z'].isin(z_values)]
    for (stack, z), tileset in tqdm(df_2_plot.groupby(['stack', 'z'])):

        # Render tileset image
        image = render_tileset_image(stack=stack,
                                     z=z,
                                     width=width,
                                     render=render,
                                     **renderapi_kwargs)

        # Get extent of tileset image in render-space
        bounds = get_stack_bounds(stack=stack,
                                  render=render)
        extent = [bounds[k] for k in ['minX', 'maxX', 'minY', 'maxY']]

        # Plot image
        ax = axmap[(stack, z)]
        ax.imshow(image, origin='lower', extent=extent)
        # Axis aesthetics
        ax.invert_yaxis()
        sectionId = tileset['sectionId'].iloc[0]
        ax.set_title(f"{stack}\nz = {z:.0f} | {sectionId}")
        ax.set_xlabel('X [px]')
        ax.set_ylabel('Y [px]')


def plot_neighborhoods(stacks, z_values=None, neighborhood=1, width=1024,
                       render=None, **renderapi_kwargs):
    """Renders and plots a neighborhood image around the given tile"""
    # Create DataFrame from stacks
    df_stacks = create_stacks_DataFrame(stacks=stacks,
                                        render=render)

    # Plot all z values if none are provided
    if z_values is None:
        z_values = df_stacks['z'].unique().tolist()

    # Set up figure
    nrows = len(stacks)
    ncols = len(z_values)
    fig, axes = plt.subplots(nrows, ncols, squeeze=False,
                             figsize=(8*ncols, 8*nrows))
    axmap = {k: v for k, v in zip(product(stacks, z_values), axes.flat)}

    # Iterate through tilesets
    df_2_plot = df_stacks.loc[df_stacks['z'].isin(z_values)]
    for (stack, z), tileset in tqdm(df_2_plot.groupby(['stack', 'z'])):

        # Select a tile from the tileset randomly
        tileId = tileset.sample(1).iloc[0]['tileId']

        # Render neighborhood image
        image, bbox = render_neighborhood_image(stack=stack,
                                                tileId=tileId,
                                                neighborhood=neighborhood,
                                                width=width,
                                                return_bbox=True,
                                                render=render,
                                                **renderapi_kwargs)

        # Get extent of neighborhood image in render-space (L, R, B, T)
        extent = (bbox[0], bbox[2], bbox[1], bbox[3])

        # Plot image
        ax = axmap[(stack, z)]
        ax.imshow(image, origin='lower', extent=extent)
        # Axis aesthetics
        ax.invert_yaxis()
        sectionId = tileset['sectionId'].iloc[0]
        ax.set_title(f"{stack}\nz = {z:.0f} | {sectionId}\n{tileId}")
        ax.set_xlabel('X [px]')
        ax.set_ylabel('Y [px]')
