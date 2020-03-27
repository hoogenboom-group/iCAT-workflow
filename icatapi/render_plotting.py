from tqdm.notebook import tqdm
import numpy as np
import pandas as pd
from seaborn import color_palette
from shapely.geometry import box
from shapely import affinity
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from skimage.io import imread
from renderapi.image import get_bb_image

from .render_pandas import create_stacks_DataFrame


__all__ = ['plot_tile_map']


def plot_tile_map(stacks, render):
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


def render_tileset_image(stack, z, render):
    """
    """
    pass


def render_tile_with_neighbors(stack, tileId, render):
    """
    """
    pass
