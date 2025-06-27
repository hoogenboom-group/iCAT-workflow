# %%
from icatapi.render_transforms import scale_stack
from icatapi.render_pandas import create_stack_DataFrame, upload_stack_DataFrame
from renderapi.transform import AffineModel as AffineRender
from matplotlib.transforms import Affine2D as AffineMPL
import subprocess
import os
from pprint import pprint
import json
from icatapi.montage import generate_point_matches
from renderapi.client import (MatchDerivationParameters,
                              FeatureExtractionParameters,
                              SiftPointMatchOptions)
from icatapi.montage import get_tile_pairs_4_montage
import re
from pathlib import Path

from tqdm.notebook import tqdm
import numpy as np
import pandas as pd
import seaborn as sns
import altair as alt
import matplotlib.pyplot as plt

import renderapi
import icatapi

# %% [markdown]
# #### Settings

# %%
# pandas display settings
pd.set_option('display.max_colwidth', 20)

# `altair` settings
alt.data_transformers.disable_max_rows()

# %% [markdown]
# ## 1) Set up `render-ws` environment
# ---
#
# #### Connect to `render-ws`

# %%
# `render-ws` parameters
owner = 'skaracoban'
project = '202412_02_SK002'
# Project directory
dir_project = Path("/long_term_storage/skaracoban/data/SK002/render_data_2")

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

# %% [markdown]
# #### Set montage stacks

# %%
# Infer stack and section info
# ----------------------------
stacks = renderapi.render.get_stacks_by_owner_project(render=render, **render_connect_params)
stacks_2_montage = ['EM_himag']
match_collections = {k: v for k, v in zip(stacks_2_montage,
                                          [f"{project}_{stack}_points" for stack in stacks_2_montage])}

# Output
# ------
out = f"""\
project directory... {dir_project} | Exists: {dir_project.exists()}
all stacks.......... {stacks}
stacks to montage... {stacks_2_montage}
match collections... {match_collections}
...
"""
print(out)

# Create project DataFrame
# ------------------------
df_project = icatapi.create_stacks_DataFrame(stacks=stacks_2_montage,
                                             render=render, **render_connect_params)
df_project.groupby('stack')\
          .apply(lambda x: x.head(3))

# %% [markdown]
# ## 2) Generate point matches
# ---
#
# #### Collect tile pairs
#
# Tile pairs are any two tiles that overlap with each other (possibly including diagonally). Collection of tile pairs is generated from a `render-python` client script. This client selects a set of tiles `p` based on its position in a stack and then searches for nearby `q` tiles using geometric parameters.
#
# script | code
# ------ | ----
# client script | [`renderapi.client.tilePairClient`](https://github.com/fcollman/render-python/blob/721ac8845e3067af6c81f3c67f2c0fa24fb1723c/renderapi/client/client_calls.py#L129)
# java script | [`TilePairClient.java`](https://github.com/saalfeldlab/render/blob/master/render-ws-java-client/src/main/java/org/janelia/render/client/TilePairClient.java)

# %%

# %%
# Initialize tile pairs DataFrame
df_pairs = pd.DataFrame()

# Loop through montage stacks
for stack in tqdm(stacks_2_montage):

    # Get tile pairs for each stack
    df = get_tile_pairs_4_montage(stack=stack,
                                  render=render, **render_connect_params)
    df_pairs = pd.concat([df_pairs, df])

# Preview
out = f"{len(df_pairs)} tile pairs"
print(out + '\n' + '.'*len(out))

df_pairs.reset_index(drop=True, inplace=True)
df_pairs.groupby('stack')\
        .apply(lambda x: x.sample(7))

# %% [markdown]
# ### Run `pointMatchClient`
# ##### Set `SIFT` & `RANSAC` parameters

# %%

# %%
# `RANSAC` parameters
match_params = MatchDerivationParameters(matchIterations=None,
                                         matchMaxEpsilon=25,        # maximal alignment error
                                         matchMaxNumInliers=None,
                                         matchMaxTrust=None,
                                         matchMinInlierRatio=0.05,  # minimal inlier ratio
                                         matchMinNumInliers=7,      # minimal number of inliers
                                         matchModelType='RIGID',    # expected transformation
                                         matchRod=0.92)             # closest/next closest ratio
# `SIFT` parameters
feature_params = FeatureExtractionParameters(SIFTfdSize=8,          # feature descriptor size
                                             SIFTmaxScale=0.20,     # (width/height *) maximum image size
                                             SIFTminScale=0.05,     # (width/height *) minimum image size
                                             SIFTsteps=7)           # steps per scale octave
# Combined `SIFT` & `RANSAC` parameters
sift_options = SiftPointMatchOptions(**{**match_params.__dict__,
                                        **feature_params.__dict__})
# Add clipping options
sift_options.clipWidth = 1000   # N pixels included in rendered clips of LEFT/RIGHT oriented montage tiles
sift_options.clipHeight = 1000  # N pixels included in rendered clips of TOP/BOTTOM oriented montage tiles

# Preview
list(sift_options.to_java_args())

# %% [markdown]
# #### \*\****COMPUTATIONALLY EXPENSIVE*** \**
#
# ##### Run `pointMatchClient` on `N_cores`

# %%

# %%
# Set number of cores and batch size
N_cores = 40
batch_size = 4

# Generate point matches
generate_point_matches(df_pairs,
                       match_collections=match_collections,
                       sift_options=sift_options,
                       excludeAllTransforms=True,
                       N_cores=N_cores,
                       batch_size=batch_size,
                       render=render, **render_connect_params)

# %% [markdown]
# ## 3) Analyze point matches
# ---
#
# ### Collect point matches
# Sort of forced to iterate through tile pairs because no data is returned for tile pairs with no matches

# %%
# Collect point matches from montage stacks
df_matches = pd.DataFrame()
for stack in tqdm(stacks_2_montage):
    # Get matches per stack
    df = icatapi.montage.get_matches_within_stack(stack=stack,
                                                  match_collection=match_collections[stack],
                                                  render=render)
    df_matches = pd.concat([df_matches, df])

# Merge with DataFrame of tile pairs to also get empty matches
df_matches = pd.merge(
    df_matches,
    df_pairs.rename(columns={'p.groupId': 'pGroupId',
                             'q.groupId': 'qGroupId',
                             'p.id': 'pId',
                             'q.id': 'qId'})
    .drop(['p.relativePosition',
           'q.relativePosition'], axis=1, errors='ignore'),
    how='outer',
    on=['stack', 'z', 'pGroupId', 'pId', 'qGroupId', 'qId'])

# Add row/col indices
df_matches[['pc', 'pr']] = np.stack(df_matches['pId'].apply(lambda x:
                                    [int(i) for i in re.findall(r'\d+', x)[-2:]]))
df_matches[['qc', 'qr']] = np.stack(df_matches['qId'].apply(lambda x:
                                    [int(i) for i in re.findall(r'\d+', x)[-2:]]))

# Preview
out = f"""\
{len(df_matches.dropna())} / \
{len(df_matches)} \
({len(df_matches.dropna())/len(df_matches):.1%}) \
tile pair matches"""
print(out + '\n' + '.'*len(out))
df_matches.groupby('stack')\
          .apply(lambda x: x.sample(3))

# %% [markdown]
# ### Heatmaps of point matches
#
# #### East-West point matches

# %%
icatapi.plotting.plot_matches_within_section(df_matches,
                                             direction='east-west',
                                             width=150,
                                             height=150)

# %% [markdown]
# #### North-South point matches

# %%
icatapi.plotting.plot_matches_within_section(df_matches,
                                             direction='north-south',
                                             width=150,
                                             height=150)

# %% [markdown]
# ## 4) Montage
# ---
#
# #### Edit `montage.json`

# %%

# %%
# Load montage json template
template_montage_json = Path('/home/skaracoban/render_code/iCAT-workflow/templates/montage.json')
with template_montage_json.open('r') as json_data:
    montage_settings = json.load(json_data)

# Edit montage settings for each montage stack
for (stack, z, sectionId), df in df_project.loc[(df_project['stack'].isin(stacks_2_montage))] \
                                           .groupby(['stack', 'z', 'sectionId']):

    # Edit BigFeta solver schema
    montage_settings['first_section'] = z
    montage_settings['last_section'] = z
    montage_settings['solve_type'] = 'montage'
    montage_settings['transformation'] = 'rigid'
    montage_settings['log_level'] = 'INFO'

    # Edit input stack data
    montage_settings['input_stack']['owner'] = owner
    montage_settings['input_stack']['project'] = project
    montage_settings['input_stack']['name'] = stack

    # Edit point match stack data
    montage_settings['pointmatch']['owner'] = owner
    montage_settings['pointmatch']['name'] = match_collections[stack]

    # Edit output stack data
    montage_settings['output_stack']['owner'] = owner
    montage_settings['output_stack']['project'] = project
    montage_settings['output_stack']['name'] = f'{stack}_montaged'

    # Edit regularization parameters
    montage_settings['regularization']['default_lambda'] = 0.005      # default: 0.005
    montage_settings['regularization']['translation_factor'] = 0.005  # default: 0.005
    montage_settings['regularization']['thinplate_factor'] = 1e-5     # default: 1e-5

    # Export montage settings to
    montage_json = dir_project / '_jsons_montage' / stack / f"{sectionId}_montage.json"
    montage_json.parent.mkdir(parents=True, exist_ok=True)
    with montage_json.open('w') as json_data:
        json.dump(montage_settings, json_data, indent=2)

# Sample montage json
print(montage_json)
print('...')
pprint(montage_settings)

# %% [markdown]
# ### Run `BigFeta` montage

# %%

# %%
# Path to `BigFeta`
cwd = Path.cwd().as_posix()
BigFeta_dir = Path('/home/catmaid/BigFeta/')

# Loop through each section of montage stacks
for (stack, z, sectionId), df in tqdm(df_project.loc[(df_project['stack'].isin(stacks_2_montage))]
                                                .groupby(['stack', 'z', 'sectionId'])):

    # Select montage json
    montage_json = dir_project / '_jsons_montage' / stack / f"{sectionId}_montage.json"

    # Call `BigFeta.BigFeta` process -- have to switch to BigFeta directory
    os.chdir(BigFeta_dir.as_posix())
    subprocess.run(['python', '-m', 'bigfeta.bigfeta', '--input_json', montage_json.as_posix()])
    os.chdir(cwd)

# %% [markdown]
# ## 5) Inspect montaged stacks
# ---
#

# %% [markdown]
# #### Tile map

# %%
stacks = renderapi.render.get_stacks_by_owner_project(render=render, **render_connect_params)
stacks_2_plot = [stack for stack in stacks if '_montaged' in stack] +\
    stacks_2_montage

icatapi.plot_tile_map(stacks=stacks_2_plot,
                      render=render, **render_connect_params)

# %% [markdown]
# #### Plot stacks

# %%
icatapi.plot_stacks(stacks_2_plot,
                    maxTileSpecsToRender=1000,
                    render=render)

# %%
stacks_2_plot

# %% [markdown]
# ## Scale montage
# ---

# %%


# %% [markdown]
# #### Determine scaling factor
# Scale each tileset by the same factor. So determine the average scale and multiply by that

# %%
# Collect scaling factors
scales_x = []
scales_y = []

# Create stack DataFrame
df_stack = create_stack_DataFrame(stack='EM_himag_montaged',
                                  render=render, **render_connect_params)

# Loop through sections
for z, layer in tqdm(df_stack.groupby('z'),
                     total=len(df_stack['z'].unique())):

    # Get transform data
    columns = ['M00', 'M10', 'M01', 'M11', 'B0', 'B1']
    tforms = pd.DataFrame(layer['tforms']
                          .apply(lambda x: x[0].dataString)
                          .str.split(' ', expand=True).values, columns=columns)\
        .astype(float)

    # Extract scale from affine transform
    M = AffineMPL(np.array([[tforms['M00'].mean(), tforms['M01'].mean(), 0],
                            [tforms['M10'].mean(), tforms['M11'].mean(), 0],
                            [0,                    0, 1]]))
    R, S = np.linalg.qr(M.get_matrix())
    mask = np.diag(S) < 0.
    S[mask, :] *= -1.
    # Set scale
    sx = 1/S[0, 0]
    sy = 1/S[1, 1]

    # Collect scaling factors
    scales_x.append(sx)
    scales_y.append(sy)

# Put into arrays
scales_x = np.array(scales_x)
scales_y = np.array(scales_y)
# Find average
sx = scales_x.mean()
sy = scales_y.mean()

# Out
sx, sy

# %% [markdown]
# #### Scale stack

# %%
# Scale stack
scale_stack(stack_in='EM_himag_montaged',
            stack_out='EM_himag_stitched',
            sx=sx,
            sy=sy,
            translate=True,
            render=render, **render_connect_params)

# %% [markdown]
# #### Plot tiles

# %%
stacks_2_plot = stacks_2_montage + ['EM_himag_montaged', 'EM_himag_stitched']

fig = icatapi.plotting.plot_tile_map(stacks=stacks_2_plot,
                                     render=render)
fig.savefig('tile_map.png')
# %%
stacks_2_montage
