# %% [markdown]
# # iCAT import
# ---
#
# #### Overview
# The purpose of this notebook is to guide and facilitate in the creation of `render-ws` stacks. These stacks are made up of metadata regarding a collection of image tiles such as the geometric bounds, number of tiles and sections, resolution, etc. Each image tile in a stack has its own respective metadata as well, called a [tile specification](https://render-python.readthedocs.io/en/latest/guide/index.html#making-a-new-stack). Using [`pandas`](https://pandas.pydata.org/) and the [`icatapi`](https://github.com/lanery/iCAT-workflow/tree/master/icatapi), this notebook creates these tile specifications from image metadata, gathers them into stacks, and uploads the stacks to a local `render-ws` server.
#
#
# #### Naming conventions
# Within the context of the iCAT workflow, a collection of images from a single data source (e.g. individual fluorescence channel) is referred to as a "tileset". The collection of multiple data sources across an individual section is referred to as a "layer", while a "stack" is the collection of the same individual data source across multiple sections. A "project" is then a collection of multiple stacks.
#
# -            | 1 section | > 1 section
# ------------ | --------- | -----------
# \> 1 channel | layer     | project (or stacks)
# 1 channel    | tileset   | stack
#
#
# #### Packages

# %%
from itertools import product
from renderapi.transform import AffineModel as AffineRender
import altair as alt
from curses import meta
from icatapi.importo import create_mipmaps
from bs4 import BeautifulSoup as Soup
from pathlib import Path
import re

from tqdm.notebook import tqdm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tifffile import TiffFile

import renderapi
import icatapi

# %% [markdown]
# #### Settings

# %%
# Indirectly enable autocomplete

# pandas display options
pd.set_option('display.max_colwidth', 20)

# %% [markdown]
# ## 1) Set up environment
# ---
#
# #### Connect to `render-ws`

# %%
# `render-ws` parameters
owner = 'skaracoban'
project = '202412_02_SK002'

# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'http://localhost',
    'port': 8081,
    'owner': owner,
    'project': project,
    'client_scripts': '/home/catmaid/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G',
}
render = renderapi.connect(**render_connect_params)
render.make_kwargs()

# %% [markdown]
# #### Set project directory

# %%
# Directory where raw data is stored
dir_project = Path("/long_term_storage/skaracoban/data/SK002/render_data")

# Stack directory
print(dir_project, ':\n'+'.'*len(dir_project.as_posix()))

# %% [markdown]
# #### Link sections to z values

# %%
# Create section mapping
dir_sections = [dir_ for dir_ in dir_project.glob('[!_]*') if dir_.is_dir()]
d_sections = {dir_section.name: i for i, dir_section in enumerate(dir_sections)}
d_sections

# %% [markdown]
# ## 2) Create mipmaps
# ---
#
# #### Raw data organization scheme
# ```
# ┌ {project}
# └───┬ {sectionId}
#     ├───┬ CLEM-grid
#     │   └──── tile-{col}x{row}.tif
#     └───┬ EM-grid
#         ├──── tile-00002x00002.tif
#         ├──── tile-00002x00003.tif
#         ├──── ...
#         └──── tile-{col}x{row}.tif
# ```
#
# #### Mipmap output scheme
# ```
# ┌ {project}
# └───┬ _mipmaps
#     └───┬ {stack}
#         └───┬ {sectionId}
#             ├───┬ 00002x00002
#             │   ├──── mm_00.tif
#             │   ├──── mm_01.tif
#             │   ├──── ...
#             │   └──── mm_{zoom}.tif
#             ├──── 00002x00003
#             ├──── ...
#             └──── {col}x{row}
# ```

# %%

# %%
# Assume subdirectories of project directory are different stacks (durr)


def _fnc(fp):
    # Read tiff
    tif = TiffFile(fp)
    # Extract metadata into dict as {'channel 1': metadata,
    #                                'channel 2': metadata, ...}
    metadata = tif.pages[0].description
    metadata = "\n".join(metadata.split("\n")[7:])
    # Infer col, row
    col, row = [int(i) for i in re.findall(r'\d+', fp.stem)][-2:]

    # Infer stack
    channel = tif.pages[0].tags['PageName'].value
    if channel == 'Secondary electrons':
        stack = 'EM_himag'
    else:
        raise ValueError(f"Channel {channel} is not electron microscopy data.")

    # Create mipmaps
    image = tif.asarray()
    dir_out = dir_project / '_mipmaps' / stack / sectionId / f"{col:05d}x{row:05d}"
    dir_out.mkdir(parents=True, exist_ok=True)
    create_mipmaps(image=image, dir_out=dir_out, invert=True,
                   metadata=metadata)


dir_stacks = [dir_ for dir_ in dir_project.iterdir() if dir_.is_dir()]

# Loop through section directories
for z, dir_section in tqdm(enumerate(dir_sections),
                           total=len(dir_sections)):

    # Set sectionId
    sectionId = dir_section.name

    # CLEM-grid
    # ---------
    for fp in tqdm(list(dir_section.glob('CLEM-grid/*-*x*.tif')),
                   leave=False):
        # Read tiff
        tif = TiffFile(fp)
        # Extract metadata into dict as {'channel 1': metadata,
        #                                'channel 2': metadata, ...}
        metadata = tif.pages[0].description
        metadata = "\n".join(metadata.split("\n")[7:])

        d_metadata = {md.attrs['name']: md for md in Soup(metadata, 'lxml').find_all('image')}
        # Infer col, row
        col, row = [int(i) for i in re.findall(r'\d+', fp.stem)][-2:]

        # Loop through tiff pages
        for page in tif.pages:

            # Infer stack
            channel = page.tags['PageName'].value
            if channel == 'Secondary electrons':
                stack = 'EM_lomag'
                invert = True
            else:  # set stack name based on the excitation wavelength for FM channels
                wavelength = d_metadata[channel].channel.attrs['excitationwavelength']
                stack = f"exc_{wavelength}nm"
                invert = False

            # Create mipmaps
            image = page.asarray()
            dir_out = dir_project / '_mipmaps' / stack / sectionId / f"{col:05d}x{row:05d}"
            dir_out.mkdir(parents=True, exist_ok=True)
            _metadata = d_metadata[channel].encode(encoding='utf-8')
            create_mipmaps(image=image, dir_out=dir_out, invert=invert,
                           metadata=_metadata)

    # EM-grid
    # -------
    for fp in tqdm(list(dir_section.glob('EM-grid/*-*x*.tif')),
                   leave=False):
        # Read tiff
        tif = TiffFile(fp)
        # Extract metadata into dict as {'channel 1': metadata,
        #                                'channel 2': metadata, ...}
        try:
            metadata = tif.pages[0].description
        except IndexError:
            continue
        metadata = "\n".join(metadata.split("\n")[7:])
        # Infer col, row
        col, row = [int(i) for i in re.findall(r'\d+', fp.stem)][-2:]

        # Infer stack
        channel = tif.pages[0].tags['PageName'].value
        if channel == 'Secondary electrons':
            stack = 'EM_himag'
        else:
            raise ValueError(f"Channel {channel} is not electron microscopy data.")

        # Create mipmaps
        image = tif.asarray()
        dir_out = dir_project / '_mipmaps' / stack / sectionId / f"{col:05d}x{row:05d}"
        dir_out.mkdir(parents=True, exist_ok=True)
        create_mipmaps(image=image, dir_out=dir_out, invert=True,
                       metadata=metadata)

# %% [markdown]
# ## 3) Create tile specifications
# ---
#
# #### [`TileSpec`](https://github.com/fcollman/render-python/blob/master/renderapi/tilespec.py#L17) parameters
#
# | Field        | Type           | Default | Description
# | -----        | ----           | ------- | -----------
# | tileId       | str            | None    | Unique string specifying a tile's identity
# | z            | float          | None    | z values this tile exists within
# | width        | int            | None    | Width in pixels of the raw tile
# | height       | int            | None    | Height in pixels of the raw tile
# | imagePyramid | `ImagePyramid` | None    | `ImagePyramid` for this tile
# | minint       | int            | 0       | Pixel intensity value to display as black
# | maxint       | int            | 65535   | Pixel intensity value to display as white
# | layout       | `Layout`       | None    | a `Layout` object for this tile
# | tforms       | list           | [ ]     | Transform objects
#
#
# #### [`Layout`](https://github.com/fcollman/render-python/blob/master/renderapi/layout.py#L1) parameters
#
# | Field     | Type  | Default | Description                                  |
# | -----     | ----  | ------- | -----------                                  |
# | sectionId | str   | None    | sectionId this tile was taken from           |
# | scopeId   | str   | None    | What microscope this came from               |
# | cameraId  | str   | None    | Camera this was taken with                   |
# | imageRow  | int   | None    | Row from a row,col layout this was taken     |
# | imageCol  | int   | None    | Column from a row,col layout this was taken  |
# | stageX    | float | None    | X stage coordinates for where this was taken |
# | stageY    | float | None    | Y stage coordinates for where this was taken |
# | rotation  | float | None    | Angle of camera when this was taken          |
# | pixelsize | float | None    | Effective size of pixels                     |
#
#
# #### Building tile specifications
# Will build tile specifications from base level mipmaps (which contain the metadata).

# %%
d_sections

# %%
# Collect tile specifications
tile_dicts = []

# Subdirectories of _mipmpap directory are the different stacks
dir_stacks = [dir_ for dir_ in (dir_project/'_mipmaps').iterdir() if dir_.is_dir()]
# Loop through stacks
for dir_stack in tqdm(dir_stacks):

    # Set stack name
    stack = dir_stack.name

    # Loop through sections
    dir_sections = [dir_ for dir_ in dir_stack.iterdir() if dir_.is_dir()]
    for dir_section in tqdm(dir_sections):

        # Set sectionId and z value
        sectionId = dir_section.name
        z = d_sections[sectionId]

        # Loop through mipmap directories within each section
        for dir_mipmap in dir_section.glob('*x*'):

            # Set base-level tiff
            fp = dir_mipmap / '0.tif'

            # Create tile dict
            d_tile = {}
            d_tile['stack'] = stack
            d_tile['z'] = z
            d_tile['sectionId'] = sectionId
            d_tile = icatapi.importo.create_tile_dict(fp, d_tile=d_tile, host="")
            # Add to collection
            tile_dicts.append(d_tile)

# %% [markdown]
# #### Create stack DataFrames

# %%
# Create DataFrame from list of tile specifications
df_stacks = pd.DataFrame(tile_dicts)
# Infer stacks and z values
stacks = df_stacks['stack'].unique().tolist()
z_values = df_stacks['z'].unique().tolist()


# Sneak peak
df_stacks.groupby('stack')\
         .apply(lambda x: x.sample(1))

# %% [markdown]
# #### Check tile count

# %%

# %%
# Make tile count DataFrame for plotting / display purposes
source = df_stacks.loc[:, ['sectionId', 'stack', 'z']]
bars = alt.Chart(source).mark_bar().encode(
    x='count()',
    y='stack:N',
    color='stack:N',
)

text = bars.mark_text(
    align='left',
    baseline='middle'
).encode(
    text='count()'
)

alt.layer(bars, text, data=source).properties(
    width=200,
    height=150,
).facet(
    column='sectionId:N'
)

# %% [markdown]
# ## 4) Refine tile specifications
# ---
#
# ### `tileId` - add alphanumeric prefix
# This is because `render-ws` renders tiles alphanumerically. So we add an alphabetic prefix to tile names so that newer tiles appear on top.

# %%

# %%


def gen_prefix(n=3):
    """Generates a sequence of length `n` characters in alphabetical order
    e.g. for n=3 [aaa, aab, aac, ..., zzx, zzy, zzz]"""
    n = min(n, 4)
    characters = 'abcdefghijklmnopqrstuvwxyz'
    for s in product(characters, repeat=n):
        yield ''.join(s)


# %%
# Loop through tilesets
df_tilesets = []
for (stack, z), df_tileset in df_stacks.groupby(['stack', 'z']):

    # Sort by acquisition time such that top entry is last acquired
    df_tileset = df_tileset.sort_values('acqTime', ascending=False)\
        .reset_index(drop=True).copy()

    # Prepend alphanumeric prefix to each tileId
    prefixes = pd.Series(gen_prefix())[:len(df_tileset)]
    df_tileset['tileId'] = prefixes + '_' + df_tileset['tileId']
    df_tilesets.append(df_tileset)

# Concatenate tilesets
df_stacks = pd.concat(df_tilesets).reset_index(drop=True)
# Sneak peak
df_stacks.groupby('stack')\
         .apply(lambda x: x.sample(1))

# %% [markdown]
# ### `tforms` - set affine transformations
# Place image tiles in `render` coordinate space (aka pixel space) such that top left image tile is at ~(0, 0) and its width and height are simply its width and height in pixels. Translation is derived from converting the stage position (`stageX`, `stageY`) into pixel space by dividing by the pixel size. But first, visualize the layout of each tileset.

# %% [markdown]
# #### Apply translations

# %%

# %%
# Loop through tilesets
for (stack, z), df_tileset in df_stacks.groupby(['stack', 'z']):

    # Offset by stage position
    # ------------------------
    # Normalize to (0, 0) since Odemis stage position is basically random
    xs = df_tileset['stageX'] - df_tileset['stageX'].min()
    ys = df_tileset['stageY'] - df_tileset['stageY'].min()
    # Divide by pixelsize and flip y axis
    xs = xs / (df_tileset['pixelsize']/1e3)  # um / (um/px) = px
    ys = -ys / (df_tileset['pixelsize']/1e3)  # um / (um/px) = px
    # Shift y translation up so that it's all positivo
    ys -= ys.min()

    # add a margin of 1 tile to the left and top
    # Create `render` affine transformations
    # --------------------------------------
    A = [[AffineRender(B0=(x + (4096 * 1)), B1=(y + (4096 * 1)))] for x, y in zip(xs, ys)]
    # A = [[AffineRender(B0=(x), B1=(y))] for x, y in zip(xs, ys)]
    print(A)

    # Add to DataFrame
    for j, (i, tile) in enumerate(df_tileset.iterrows()):
        df_stacks.loc[i, 'tforms'] = [A[j]]

# Sneak peak
df_stacks.groupby('stack')\
         .apply(lambda x: x.sample(1)).drop('tileId', axis=1)

# %% [markdown]
# ### `minint`, `maxint` - set min, max intensity levels
# Sample `n` images/section to determine reasonable min/max intensity values.

# %%
# Set parameters
n = 10              # sample size (per section)
pcts_FM = (30, 99)  # % for intensity clipping of FM stacks
pcts_EM = (1, 99)   # % for intensity clipping of EM stacks

# Loop through stacks and sections
for (stack, z), df_tileset in tqdm(df_stacks.groupby(['stack', 'z'])):

    # Sample filepaths
    fps = df_tileset.sample(min(n, len(df_tileset)))['imagePyramid']\
                    .apply(lambda x: x[0]['imageUrl'])\
                    .tolist()

    # Collect min/max intensity values
    minints = []
    maxints = []
    # Loop through sample tiles
    for fp in fps:

        # Load tiff image
        try:
            fp_tiff = fp.split('.nl')[1]
        except IndexError:
            fp_tiff = fp
        tiff = TiffFile(fp_tiff)
        image = tiff.asarray()

        # Get intensity percentiles
        pcts = pcts_FM if 'EM' not in stack else pcts_EM
        minint, maxint = np.percentile(image, pcts)
        minints.append(minint)
        maxints.append(maxint)

    # Set min/max intensity
    df_stacks.loc[(df_stacks['stack'] == stack) &
                  (df_stacks['z'] == z), 'minint'] = np.mean(minints, dtype=int)
    df_stacks.loc[(df_stacks['stack'] == stack) &
                  (df_stacks['z'] == z), 'maxint'] = np.mean(maxints, dtype=int)

# Sneak peak
df_stacks.groupby('stack')\
         .apply(lambda x: x.head(3)).drop('tforms', axis=1)

# %% [markdown]
# ## 5) Upload stacks to `render-ws`
# ---

# %%
# Loop through stacks
for stack, df_stack in tqdm(df_stacks.groupby('stack')):

    # Set stack resolution
    Rx = df_stack['pixelsize'].iloc[0]
    Ry = df_stack['pixelsize'].iloc[0]
    Rz = 100

    # Create stacks
    icatapi.upload_stack_DataFrame(df=df_stack,
                                   name=stack,
                                   stackResolutionX=Rx,
                                   stackResolutionY=Ry,
                                   stackResolutionZ=Rz,
                                   render=render)

# %% [markdown]
# #### Inspect stacks

# %%
# Get stacks
stacks = renderapi.render.get_stacks_by_owner_project(render=render)

# Plot tile map
stacks_2_plot = stacks
icatapi.plot_tile_map(stacks_2_plot,
                      render=render)

# %%
stacks_2_plot

# %%
# Plot stack images
icatapi.plot_stacks(stacks=stacks_2_plot,
                    maxTileSpecsToRender=500,
                    render=render)
