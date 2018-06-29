# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   08-06-2018 14:57:10
"""

from pathlib import Path
import renderapi
from renderapi.layout import Layout
from renderapi.transform import AffineModel
from renderapi.tilespec import TileSpec


# Render Parameters
project = 'pancrea'

stacks = ['big_EM',
          'hoechst',
          'amylase',
          'insulin']

match_collections = ['big_EM_matches',
                     'hoechst_matches',
                     'amylase_matches',
                     'insulin_matches']

# Tile Data Parameters
N_rows = 2
N_cols = 2
N_sections = 1
overlaps = [1 - -0.05,  # %
            1 - 0.15,  # %
            1 - 0.15,  # %
            1 - 0.15]  # %
resolutions = [175e3/2048,  # nm/px
               205e3/2048,  # nm/px
               205e3/2048,  # nm/px
               205e3/2048]  # nm/px
W = 2048  # pixels
H = 2048  # pixels
intensity_ranges = [(30400, 32100),
                    (2500, 15400),
                    (2000, 8000),
                    (1200, 5000)]

# Tile filepath parameters
tile_dir = '/opt/tiles/big_kahuna/big_tiles/'
tile_ext = '.ome.tif'
tile_convention = 'tile-__c__x__r__'


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
for stack in stacks:
    renderapi.stack.create_stack(stack, render=render)

# Import tile data
for i, stack in enumerate(stacks):
    tilespecs = []
    for section in range(N_sections):
        for r in range(N_rows):
            for c in range(N_cols):
                x_pos = c * W * overlaps[i] * resolutions[i]
                y_pos = r * H * overlaps[i] * resolutions[i]
                layout = Layout(sectionId=f'{section:05d}',
                                scopeId='Verios',
                                cameraId='Andor',
                                imageRow=0,
                                imageCol=0,
                                stageX=x_pos,
                                stageY=y_pos,
                                rotation=0.0,
                                pixelsize=resolutions[i])

                # Define a simple transformation - translation based on layout
                at = AffineModel(B0=layout.stageX/layout.pixelsize,
                                 B1=layout.stageY/layout.pixelsize)

                # Define unique tile specifications
                tileId = tile_convention.replace('__c__', f'{c:05d}').replace(
                                                 '__r__', f'{r:05d}')
                tileId = tileId.replace('tile', stack)
                tilePath = Path(tile_dir).joinpath(stack).joinpath(
                                tileId).with_suffix(tile_ext)
                imageUrl = tilePath.as_posix()
                ts = TileSpec(tileId=tileId,
                              z=section,
                              width=W,
                              height=H,
                              minint=intensity_ranges[i][0],
                              maxint=intensity_ranges[i][1],
                              imageUrl=imageUrl,
                              maskUrl=None,
                              layout=layout,
                              tforms=[at])
                # Append each tilespec to list
                tilespecs.append(ts)

    renderapi.client.import_tilespecs(stack,
                                      tilespecs,
                                      close_stack=True,
                                      render=render)

# Set stack state to complete
for stack in stacks:
    renderapi.stack.set_stack_state(stack, 'COMPLETE', render=render)

# # --------
# # Montage
# # --------
# for stack, match_collection in zip(stacks, match_collections):
#     # Get positional bounds of image stack
#     stack_bounds = renderapi.stack.get_stack_bounds(stack, render=render)
#     # Generate tile pairs for input into point match generator
#     tile_pairs = renderapi.client.tilePairClient(stack,
#                                                  minz=stack_bounds['minZ'],
#                                                  maxz=stack_bounds['maxZ'],
#                                                  render=render)

#     # Generate list of tile pairs
#     tile_pair_list = [(tp['p']['id'], tp['q']['id']) \
#                       for tp in tile_pairs['neighborPairs']]

#     # Generate point matches
#     renderapi.client.pointMatchClient(stack,
#                                       collection=match_collection,
#                                       tile_pairs=tile_pair_list,
#                                       render=render)
