# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   27-05-2018 14:57:10
"""

import re
from pathlib import Path
from functools import partial
from tqdm import tqdm
import pandas as pd
import renderapi
from renderapi.layout import Layout
from renderapi.transform import AffineModel
from renderapi.tilespec import TileSpec


# Render Parameters
project = 'pancrea'
stack = 'lil_EM_grid'
match_collection = 'EM_matches'
# Tile Data
tile_df = pd.read_csv('pancrea_data.csv')

# Tile parameters
overlap = 20  # %
resolution = 5  # nm/px

# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'localhost',
    'port': 8080,
    'owner': 'lanery',
    'project': f'{project}',
    'client_scripts': \
        '/usr/local/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}
render = renderapi.connect(**render_connect_params)

# Make a new stack
renderapi.stack.create_stack(stack, render=render)

# Import tile data
tilespecs = []
for i, row in tile_df.iterrows():

    # Use estimated stage position instead of recorded stage position
    c, r = re.findall(r'\d+', row['tileId'])
    c = int(c); r = int(r)
    x_est = c * row['width'] * (1 - overlap/100) * resolution
    y_est = r * row['height'] * (1 - overlap/100) * resolution

    # Tile ID and URL
    tileId = row['tileId']
    imageUrl = row['imageUrl']

    # Layout
    layout = Layout(sectionId=f'{0:05d}',
                    scopeId='Verios',
                    cameraId='Andor',
                    imageRow=0,
                    imageCol=0,
                    # stageX=row['stageX'],
                    # stageY=row['stageY'],
                    stageX=x_est,
                    stageY=y_est,
                    rotation=0.0,
                    pixelsize=row['pixelsize'])

    # Affine Transform
    x_translation = layout.stageX / layout.pixelsize
    y_translation = layout.stageY / layout.pixelsize
    at = AffineModel(B0=x_translation,
                     B1=y_translation)

    # TileSpec
    ts = TileSpec(tileId=tileId,
                  z=0,
                  width=row['width'],
                  height=row['height'],
                  minint=31800,
                  maxint=35200,
                  imageUrl=row['imageUrl'],
                  maskUrl=None,
                  layout=layout,
                  tforms=[at])

    # Append each tilespec to list
    tilespecs.append(ts)

# Import tile specs to stack
renderapi.client.import_tilespecs(stack,
                                  tilespecs,
                                  close_stack=True,
                                  render=render)

# Set stack state to complete
renderapi.stack.set_stack_state(stack, 'COMPLETE', render=render)

# Get positional bounds of image stack
stack_bounds = renderapi.stack.get_stack_bounds(stack, render=render)
# Generate tile pairs for input into point match generator
tile_pairs = renderapi.client.tilePairClient(stack,
                                             minz=stack_bounds['minZ'],
                                             maxz=stack_bounds['maxZ'],
                                             render=render)

# Generate list of tile pairs
tile_pair_list = [(tp['p']['id'], tp['q']['id']) \
                  for tp in tile_pairs['neighborPairs']]

# --------
# Generate point matches (in chunks)
# --------

def run_point_match_client(tile_pair_chunk, stack, collection, render):
    renderapi.client.pointMatchClient(stack=stack,
                                      collection=collection,
                                      tile_pairs=tile_pair_chunk,
                                      render=render)


chunk_size = 6
tile_pair_chunks = []
for i in range(0, len(tile_pair_list), chunk_size):
    tile_pair_chunk = tile_pair_list[i : i+chunk_size]
    tile_pair_chunks.append(tile_pair_chunk)

myp = partial(run_point_match_client,
              stack=stack,
              collection=match_collection,
              render=render)

with renderapi.client.WithPool(3) as pool:
    pool.map(myp, tile_pair_chunks)
