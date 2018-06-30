# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   29-06-2018 14:57:10
"""

import re
from pathlib import Path
import renderapi
from renderapi.layout import Layout
from renderapi.transform import AffineModel
from renderapi.tilespec import TileSpec


# --------
# 1 Create Stacks
# --------
# Project, stack, and match collection names
owner = 'lanery'
project = 'iCAT_demo'
stacks = ['lil_EM',
          'big_EM',
          'hoechst',
          'amylase',
          'insulin']
match_collections = ['EM_matches',
                     'hoechst_matches',
                     'amylase_matches',
                     'insulin_matches']

# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'localhost',
    'port': 8080,
    'owner': f'{owner}',
    'project': f'{project}',
    'client_scripts': \
        '/usr/local/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}
render = renderapi.connect(**render_connect_params)

# Actually create stacks
for stack in stacks:
    renderapi.stack.create_stack(stack, render=render)


# --------
# 2 Import Image Tile Data
# --------
# Storage parameters
data_dir = Path('/data/projects/iCAT_demo/iCAT_sample_data')
# big_tile_convention = ''

# Tile parameters
width = 2048  # px
height = 2048  # px
lil_EM_res = 4.88  # nm/px
big_EM_res = 84.9  # nm/px
FM_res = 99.6  # nm/px

# Grid parameters
EM_overlap = 20  # %
FM_overlap = 20  # %

# Acquisition parameters
scopeId = 'SECOM'
cameraId = 'Andor'


# for 

for i, stack in enumerate(stacks):
    tilespecs = []
    for r in range(N_rows):
        for c in range(N_cols):
            x_pos = c * W * (1 - overlaps[i]) * resolutions[i]
            y_pos = r * H * (1 - overlaps[i]) * resolutions[i]
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

