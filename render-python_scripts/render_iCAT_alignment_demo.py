# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   29-06-2018 14:57:10
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


# Project, Stack, and Match Collection Names
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

# Tile Data
# tile_df = pd.read_csv('pancrea_data.csv')

# Tile parameters
overlap = 20  # %
resolution = 5  # nm/px

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

# Make a new stack
# renderapi.stack.create_stack(stack, render=render)

