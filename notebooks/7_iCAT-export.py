# %% [markdown]
# # iCAT Export
# ---
#
# #### Overview
# Export data in pyramidal png stacks for CATMAID.

# %%
import json
from bs4 import BeautifulSoup as Soup
from tifffile import TiffFile
from ruamel.yaml import YAML
import sys
from icatapi.utils import colorize, T_HOECHST, T_AF594
from skimage import io, transform, img_as_ubyte
from shutil import rmtree
from multiprocessing import Pool
from functools import partial
import subprocess
from renderapi.client import ArgumentParameters
from random import sample
from pathlib import Path
from tqdm.notebook import tqdm

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import renderapi
import icatapi

# %% [markdown]
# #### Settings

# %%
# pandas display settings
pd.set_option('display.max_rows', 20)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 15)

# Indirectly enable autocomplete
# %config Completer.use_jedi = False

# %% [markdown]
# ## Set up `render-ws` environment
# ---

# %%
# `render` project parameters
# ---------------------------
owner = 'skaracoban'
project = '202412_02_SK002'
dir_project = Path("/long_term_storage/skaracoban/data/SK002/render_data_2/")
dir_catmaid = Path('/long_term_storage/catmaid_projects/skaracoban/202412_02_SK002/')

# Create a renderapi.connect.Render object
# ----------------------------------------
render_connect_params = {
    'host': 'http://localhost',
    'port': 8081,
    'owner': owner,
    'project': project,
    'client_scripts': '/home/catmaid/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}
render = renderapi.connect(**render_connect_params)
render.make_kwargs()

# %%
# Infer stack and section info
# ----------------------------
stacks = renderapi.render.get_stacks_by_owner_project(render=render)
stacks_EM = [stack for stack in stacks if 'EM' in stack]
stacks_FM = [stack for stack in stacks if 'EM' not in stack]
stacks_2_export = [
    # 'EM_himag_stitched',
    'EM_himag_stitched_filtered',
    'exc_405nm_correlated',
    'exc_555nm_correlated',
    # "EM_lomag_correlated",
]
# stacks_2_export = [
#     'EM_lomag_overlaid',
#     'exc_470nm_overlaid',
# ]

# Output
# ------
out = f"""\
project directory... {dir_project} | Exists: {dir_project.exists()}
export directory.... {dir_catmaid} | Exists: {dir_catmaid.exists()}
all stacks.......... {stacks}
EM stacks........... {stacks_EM}
FM stacks........... {stacks_FM}
stacks to export.... {stacks_2_export}
...
"""
print(out)

# Create project DataFrame
# ------------------------
df_project = icatapi.create_stacks_DataFrame(stacks=stacks_2_export,
                                             render=render)
df_project.groupby('stack')\
          .apply(lambda x: x.head(5))

# %% [markdown]
# ## Export `render-ws` stacks to CATMAID
# ---
# ### Set up CATMAID export parameters

# %%

# %%


class CatmaidBoxesParameters(ArgumentParameters):
    """Subclass of `ArgumentParameters` for facilitating CATMAID export client script"""

    def __init__(self, stack, root_directory,
                 height=1024, width=1024, fmt='png', max_level=0,
                 host=None, port=None, baseurl=None,
                 owner=None, project=None, render=None, **kwargs):

        super(CatmaidBoxesParameters, self).__init__(**kwargs)

        self.stack = stack
        self.rootDirectory = root_directory
        self.height = height
        self.width = width
        self.format = fmt
        self.maxLevel = max_level

        render_kwargs = render.make_kwargs()
        host = render_kwargs.get('host')
        port = render_kwargs.get('port')
        self.baseDataUrl = renderapi.render.format_baseurl(host, port)
        self.owner = render_kwargs.get('owner') if owner is None else owner
        self.project = render_kwargs.get('project') if project is None else project

# %% [markdown]
# #### Logic for maximum zoom level
#
# Ideally `max_level` is set such that
#
# \begin{equation}
# \left( \frac{w_s}{w_t \,\, 2^m} \right) < 1
# \end{equation}
#
# where $m$ is `max_level`, $w_s$ is the width of the stack and $w_t$ is the width of each tile. Then
#
# \begin{equation}
# m = \textrm{ceil} \left( \log{\frac{w_s}{w_t}} \times \frac{1}{\log{2}} \right)
# \end{equation}


# %%
# Initialize collection for export parameters
export_data = {}
# Update max level
maxest_level = 0
# Set format
fmt = 'png'
# Set CATMAID tile width/height
w_tile = 1024
h_tile = 1024

# Iterate through stacks
for stack, df_stack in df_project.groupby('stack'):

    # Determine `max_level` such that the full section is in view when fully zoomed out

    stack_bounds = renderapi.stack.get_stack_bounds(stack=stack,
                                                    render=render)
    w_stack = max(stack_bounds['maxX'] - stack_bounds['minX'],
                  stack_bounds['maxY'] - stack_bounds['minY'])
    max_level = int(np.ceil(np.log(w_stack / w_tile) * 1/np.log(2)))
    # Export each stack to highest level in the project
    maxest_level = max(max_level, maxest_level)

    # Set parameters for export to CATMAID
    export_params = CatmaidBoxesParameters(stack=stack,
                                           root_directory=dir_catmaid.parent.as_posix(),
                                           width=w_tile,
                                           height=h_tile,
                                           max_level=maxest_level,
                                           fmt=fmt,
                                           project=project,
                                           render=render)

    # Add CATMAID export parameters to collection
    export_data[stack] = export_params

# Preview
stack = sample(export_data.keys(), 1)[0]
list(export_data[stack].to_java_args())

# %% [markdown]
# ### Call render script
# `render_catmaid_boxes.sh`
# ```sh
# Usage: java -cp <render-module>-standalone.jar
#       org.janelia.render.client.BoxClient [options] Z values for layers to
#       render
#   Options:
#   * --baseDataUrl
#       Base web service URL for data (e.g. http://host[:port]/render-ws/v1)
#     --binaryMask
#       use binary mask (e.g. for DMG data)
#       Default: false
#     --createIGrid
#       create an IGrid file
#       Default: false
#     --doFilter
#       Use ad hoc filter to support alignment
#       Default: false
#     --filterListName
#       Apply this filter list to all rendering (overrides doFilter option)
#     --forceGeneration
#       Regenerate boxes even if they already exist
#       Default: false
#     --format
#       Format for rendered boxes
#       Default: png
#   * --height
#       Height of each box
#     --help
#       Display this note
#     --label
#       Generate single color tile labels instead of actual tile images
#       Default: false
#     --maxLevel
#       Maximum mipmap level to generate
#       Default: 0
#     --maxOverviewWidthAndHeight
#       Max width and height of layer overview image (omit or set to zero to
#       disable overview generation)
#     --numberOfRenderGroups
#       Total number of parallel jobs being used to render this layer (omit if
#       only one job is being used)
#   * --owner
#       Stack owner
#   * --project
#       Stack project
#     --renderGroup
#       Index (1-n) that identifies portion of layer to render (omit if only one
#       job is being used)
#   * --rootDirectory
#       Root directory for rendered tiles (e.g.
#       /tier2/flyTEM/nobackup/rendered_boxes)
#     --skipInterpolation
#       skip interpolation (e.g. for DMG data)
#       Default: false
#   * --stack
#       Stack name
#   * --width
#       Width of each box
# ```

# %% [markdown]
# #### Wrapper for `render_catmaid_boxes` script for multiprocessing
# Multiprocessing is done across sections, so a process is created for each section.

# %%


def run_render_catmaid_boxes(z, client_script, java_args):
    """Wrapper for `render_catmaid_boxes` script to enable multiprocessing"""
    p = subprocess.run([client_script.as_posix(), f'{z:.0f}'] + java_args,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)

# %% [markdown]
# #### \*\****COMPUTATIONALLY EXPENSIVE*** \**
#
# ##### Run `render_catmaid_boxes` on `N_cores`
#
# `renderapi.client.WithPool` ends prematurely (after exporting one section).
# Weirdly only happens with `lil_EM_montaged` stack...


# %%

# %%
# Path to `render_catmaid_boxes` shell script
fp_client = Path(render_connect_params['client_scripts']) / 'render_catmaid_boxes.sh'
# Set number of cores for multiprocessing
N_cores = min(15, df_project['z'].unique().size)
# Get z values
z_values = np.unique([x for x in renderapi.stack.get_z_values_for_stack(stack, render=render)
                      for stack in stacks_2_export])

# Iterate through stacks to export
# for stack in tqdm(stacks_2_export):
for stack in tqdm(stacks_2_export):

    # Create java arguments from export parameters
    java_args = list(export_data[stack].to_java_args())

    # Set up `render_catmaid_boxes` client script
    render_catmaid_boxes_partial = partial(run_render_catmaid_boxes,
                                           client_script=fp_client,
                                           java_args=java_args)

    # Run `render_catmaid_boxes` across `N_cores`
    with Pool(N_cores) as pool:
        pool.map(render_catmaid_boxes_partial, z_values)

# %% [markdown]
# ## Set up tiles for import to CATMAID
# ---
# ### Resort CATMAID tiles
# By (unchangeable) default, `render_catmaid_boxes` exports tiles as
#
# `root directory` / `project` / `stack` / `width x height` / `zoomlevel` / `z` / `row` / `col.fmt`
#
# This is ok, but preferred format for importing to CATMAID is [tile source convention 1](https://catmaid.readthedocs.io/en/stable/tile_sources.html#tile-source-types) --- "[File-based image stack](https://catmaid.readthedocs.io/en/stable/tile_sources.html#file-based-image-stack)"
#
# `root directory` / `project` / `stack` / `z` / `row_col_zoomlevel.fmt`
#
# One other tidbit is that CATMAID annoyingly assumes that sections are 0-indexed so $z_{min}$ is subtracted.

# %% [markdown]
# #### \*\****CHANGES LOTS & LOTS OF FILEPATHS ON DISK*** \**

# %%

# %%
# Iterate through stacks to export
for stack in tqdm(stacks_2_export):

    # Loop through all the exported tiles per stack
    fps = (dir_catmaid / stack).glob(f"1024x1024/**/[0-9]*.{fmt}")
    for fp in fps:

        # Extract tile info from filepath
        zoom_level = int(fp.parents[2].name)
        z = int(fp.parents[1].name) - int(z_values.min())  # 0-index
        row = int(fp.parents[0].name)
        col = int(fp.stem)

        # Reformat tile
        tile_format_1 = dir_catmaid / stack / f"{z}/{row}_{col}_{zoom_level}.{fmt}"
        tile_format_1.parent.mkdir(parents=True, exist_ok=True)
        fp.rename(tile_format_1)

    # Clean up (now presumably empty) directory tree
    rmtree((dir_catmaid / stack / '1024x1024').as_posix())

# %% [markdown]
# #### Make thumbnails

# %%

# %%
# Colorize settings
d_colorize = {
    'exc_405nm_T': [[0.2, 0.0, 0.0, 0.0],
                    [0.0, 0.2, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0]],
    'exc_470nm_correlated': [[0.2, 0.0, 0.0, 0.0],
                             [0.0, 0.2, 0.0, 0.0],
                             [0.0, 0.0, 1.0, 0.0],
                             [0.0, 0.0, 0.0, 1.0]],
    'exc_405nm_correlated': [[0.2, 0.0, 0.0, 0.0],
                             [0.0, 0.2, 0.0, 0.0],
                             [0.0, 0.0, 1.0, 0.0],
                             [0.0, 0.0, 0.0, 1.0]],
    'exc_470nm_overlaid': [[0.2, 0.0, 0.0, 0.0],
                           [0.0, 0.2, 0.0, 0.0],
                           [0.0, 0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0, 1.0]],
    'exc_555nm_T': [[1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.6, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0]],
    'exc_555nm_correlated': [[1.0, 0.0, 0.0, 0.0],
                             [0.0, 0.6, 0.0, 0.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.0, 0.0, 1.0]],
}

# Loop through stacks to export
for stack in tqdm(stacks_2_export):

    # Loop through each section
    for z in (z_values - z_values.min()):

        # Load most zoomed out image (0, 0, `max_level`)
        try:
            fp = max(dir_catmaid.glob(f"{stack}/{z:.0f}/0_0_*.{fmt}"))
        except:
            continue
        zoom = int(fp.stem[-1])
        image = io.imread(fp)

        # Resize
        bounds = renderapi.stack.get_stack_bounds(stack=stack,
                                                  render=render)
        width_ds = bounds['maxX'] - bounds['minX']  # width of dataset at zoom level 0
        width_rs = (192 / (width_ds/2**zoom)) * w_tile
        image_rs = transform.resize(image, output_shape=(width_rs, width_rs))
        # Crop to content
        thumb = image_rs[np.ix_((image_rs > 0).any(1), (image_rs > 0).any(0))]
        try:
            thumb_rs = transform.resize(thumb, output_shape=(192, 192))
        except:
            thumb_rs = np.zeros((192, 192))
        # Colorize
        if stack in stacks_FM:
            thumb_rs = colorize(thumb_rs, d_colorize[stack])
        # Save
        fp_thumb = dir_catmaid / f"{stack}/{z:.0f}/small.{fmt}"
        io.imsave(fp_thumb, img_as_ubyte(thumb_rs))

# %%
stacks_2_export

# %%
dir_catmaid

# %% [markdown]
# #### Create `project.yaml` file

# %%

# %%
# Set project yaml file
project_yaml = dir_catmaid / 'project.yaml'

# Collect stack data
stack_data = []
for stack in tqdm(stacks_2_export):

    # Get dimension data
    bounds = renderapi.stack.get_stack_bounds(stack=stack,
                                              render=render)
    dimensions = (int((bounds['maxX'] - bounds['minX']) * 1.1),
                  int((bounds['maxY'] - bounds['minY']) * 1.1),
                  int(bounds['maxZ'] - bounds['minZ'] + 1))

    # Get resolution data (base it off OG EM himag resolution data)
    stack_metadata = renderapi.stack.get_full_stack_metadata(stack='EM_himag',
                                                             render=render)
    resolution = (np.round(stack_metadata['currentVersion']['stackResolutionX'], 5),
                  np.round(stack_metadata['currentVersion']['stackResolutionY'], 5),
                  np.round(stack_metadata['currentVersion']['stackResolutionZ'], 5))

    # Get metadata
    ts = sample(renderapi.tilespec.get_tile_specs_from_stack(stack=stack,
                                                             render=render), 1)[0]
    # fp = ts.ip[0]['imageUrl'].split('.nl')[1]
    fp = ts.ip[0]['imageUrl']
    tif = TiffFile(fp)
    metadata = tif.pages[0].description

    # Project data for output to project yaml file
    stack_datum = {
        "title": f"{stack}",
        "dimension": f"{dimensions}",
        "resolution": f"{resolution}",
        "zoomlevels": f"{(maxest_level + 1):.0f}",
        "metadata": metadata,
        "mirrors": [{
            "title": f"{project}_{stack.split('_')[0]}",
            "tile_width": 1024,
            "tile_height": 1024,
            "tile_source_type": 1,
            "fileextension": f"{fmt}",
            "url": f"https://sonic.tnw.tudelft.nl{(dir_catmaid/stack).as_posix()}"
        }]
    }
    stack_data.append(stack_datum)

# Create dict for input into project yaml file
project_data = {
    "project": {
        "title": f"{project}",
        "stacks": stack_data
    }
}

# %%
out = f"""\
{project_yaml}
--------\
"""
print(out)

yaml = YAML()
yaml.indent(mapping=2, offset=0)
yaml.dump(project_data, project_yaml)
yaml.dump(project_data, sys.stdout)
