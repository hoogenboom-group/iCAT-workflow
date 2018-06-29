# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   15-06-2018 14:57:10

Overview
  > Simple script for making data tables of image metadata for input into
    render-python scripts
  > The dataframe seeks to populate as many TileSpec attributes as reasonable

  > TileSpec Attributes:
     - tileId
     - z
     - width
     - height
     - imageUrl
     - maskUrl
     - minint
     - maxint
     - layout
     - tforms
  > For details:
    https://github.com/fcollman/render-python/blob/master/renderapi/tilespec.py#L17
"""

import os
from pathlib import Path
import itertools
from glob import glob
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as Soup
from skimage.external.tifffile import TiffFile


def build_dataframe(tile_path):
    """
    """
    # Glob together filenames
    tile_fns = Path(tile_path).glob('*')

    # Initialize dataframe
    df = pd.DataFrame(columns=['acqTime', 'tileId', 'stageX', 'stageY',
                               'pixelsize', 'width', 'height', 'imageUrl'])

    for i, tile_fn in enumerate(tile_fns):

        # Parse metadata for acquisition date
        tif = TiffFile(tile_fn.as_posix())
        page = tif.pages[0]
        xml = page.tags['image_description'].value
        soup = Soup(xml, 'lxml')
        acquisition_time = soup.find('acquisitiondate').text
        df.loc[i, 'acqTime'] = acquisition_time

        # Retrieve tile ID
        tile_id = os.path.basename(tile_fn.name).split('.')[0]
        df.loc[i, 'tileId'] = tile_id

        # Retrieve image URL
        image_url = tile_fn.as_uri()
        df.loc[i, 'imageUrl'] = image_url

        # Parse stage position (nm)
        plane_attrs = soup.find('plane').attrs
        df.loc[i, 'stageX'] = 1e9 * float(plane_attrs['positionx'])
        df.loc[i, 'stageY'] = 1e9 * float(plane_attrs['positiony'])

        # Parse pixel size (resolution = nm/px)
        pixels_attrs = soup.find('pixels').attrs
        df.loc[i, 'pixelsize'] = (1e3*float(pixels_attrs['physicalsizex']) +
                                  1e3*float(pixels_attrs['physicalsizey'])) / 2
        df.loc[i, 'width'] = pixels_attrs['sizex']
        df.loc[i, 'height'] = pixels_attrs['sizey']

    # Sort by acquisition time such that first entry is last acquired
    df['acqTime'] = pd.to_datetime(df['acqTime'])
    df.sort_values('acqTime', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Normalize stage positions such that first acquisition is at (0nm, 0nm)
    df['stageX'] =  df['stageX'].astype(float) - float(df['stageX'].iloc[-1])
    df['stageY'] = -df['stageY'].astype(float) + float(df['stageY'].iloc[-1])

    # Generate prefixes and append to dataframe
    prefixes = pd.Series(gen_prefix())[:len(df)]

    # Reformat tileId
    df['tileId'] = prefixes + '_' + df['tileId']

    return df.reset_index(drop=True)


def gen_prefix(length=3):
    """
    """
    characters = 'abcdefghijklmnopqrstuvwxyz'
    for s in itertools.product(characters, repeat=length):
        yield ''.join(s)



if __name__ == '__main__':

    tile_path = '/opt/tiles/big_kahuna/lil_tiles/'
    df = build_dataframe(tile_path)
    df.to_csv('pancrea_data.csv', index=False)
