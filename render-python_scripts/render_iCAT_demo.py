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


# ------------
# 0 Stack Data
# ------------
stack_data = {
    'data_dir': Path('/long_term_storage/rlane/SECOM/iCAT_sample_data'),
    'tile_convention': '{stack}/{stack}-{c}x{r}.ome.tif',
    'width': 2048,
    'height': 2048,
    'N_sections': 1,
    'lil_EM': {
        'px_size': 4.829,  # nm/px
        'overlap': 20,  # %
        'intensity_range': (31800, 35200),
        'scopeId': 'Verios',
        'cameraId': 'TLD',
    },
    'big_EM': {
        'stacks': ['big_EM'],
        'px_size': 84.9,  # nm/px
        'overlap': 20,  # %
        'intensity_range': (30400, 32100),
        'scopeId': 'Verios',
        'cameraId': 'TLD',
    },
    'hoechst': {
        'px_size': 99.6,  # nm/px
        'overlap': 20,  # %
        'intensity_range': (2500, 15400),
        'scopeId': 'SECOM',
        'cameraId': 'Andor',
    },
    'amylase': {
        'px_size': 99.6,  # nm/px
        'overlap': 20,  # %
        'intensity_range': (2000, 8000),
        'scopeId': 'SECOM',
        'cameraId': 'Andor',
    },
    'insulin': {
        'px_size': 99.6,  # nm/px
        'overlap': 20,  # %
        'intensity_range': (1200, 5000),
        'scopeId': 'SECOM',
        'cameraId': 'Andor',
    }
}


# ---------------
# 1 Create Stacks
# ---------------

# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'sonic',
    'port': 8080,
    'owner': 'rlane',  # reset to <owner>
    'project': 'iCAT_demo',
    'client_scripts': \
        '/home/catmaid/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}
render = renderapi.connect(**render_connect_params)

# Create (empty) stacks
stacks = ['lil_EM',
          'big_EM',
          'hoechst',
          'amylase',
          'insulin']

for stack in stacks:
    renderapi.stack.create_stack(stack, render=render)


# ------------------------
# 2 Import Image Tile Data
# ------------------------

def gen_tile_specs(stack, stack_data):
    """
    """
    # Get input from stack_data
    data_dir = stack_data['data_dir']
    N_sections = stack_data.get('N_sections', 1)
    width = stack_data['width']
    height = stack_data['height']
    overlap = stack_data.get('overlap', 20)
    px_size = stack_data[stack]['px_size']
    intensity_range = stack_data[stack].get('intensity_range', (0, 65535))

    # TODO: use tile_convention instead
    tiles = list(data_dir.glob(f'{stack}/*.ome.tif'))
    tile_specs = []
    for z in range(N_sections):
        for tile in tiles:

            # TODO: use tile_convention instead
            c, r = [int(i) for i in re.findall('\d+', tile.name)]
            x_pos = c * width * (1 - overlap) * px_size
            y_pos = r * height * (1 - overlap) * px_size

            layout = Layout(sectionId=f'{z:05d}',
                            scopeId=stack_data.get('scopeId'),
                            cameraId=stack_data.get('cameraId'),
                            imageRow=r,
                            imageCol=c,
                            stageX=x_pos,
                            stageY=y_pos,
                            rotation=0.0,
                            pixelsize=px_size)

            at = AffineModel(B0=layout.stageX/layout.pixelsize,
                             B1=layout.stageY/layout.pixelsize)

            tileId = tile.name.split('.')[0]
            imageUrl = tile.as_uri()
            tile_spec = TileSpec(tileId=tileId,
                                 z=z,
                                 width=width,
                                 height=height,
                                 minint=intensity_range[0],
                                 maxint=intensity_range[1],
                                 imageUrl=imageUrl,
                                 maskUrl=None,
                                 layout=layout,
                                 tforms=[at])

            tile_specs.append(tile_spec)

    return tile_specs


# Generate TileSpecs
tile_specs = {}
for stack in stacks:

    # Get TileSpecs from stack_data
    tile_specs[stack] = gen_tile_specs(stack, stack_data)

    # Import TileSpecs to render
    renderapi.client.import_tilespecs(stack,
                                      tile_specs[stack],
                                      close_stack=True,
                                      render=render)

    # Set stack state to complete
    renderapi.stack.set_stack_state(stack, 'COMPLETE', render=render)
