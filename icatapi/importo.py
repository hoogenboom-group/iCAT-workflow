from pathlib import Path
import re

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as Soup
from tifffile import TiffFile


__all__ = ['parse_metadata']


def parse_metadata(filepath, section):
    """Parses Odemis (single-page) tif file metadata

    Parameters
    ----------
    filepath : `pathlib.Path`
        Path to image tile location as `pathlib.Path` object
    section : str
        Name of section to which image tile belongs

    Returns
    -------
    tile_dict : dict
        Almighty dictionary containing lots of juicy info about the image tile
    """

    # Read metadata
    # -------------
    tif = TiffFile(filepath.as_posix())
    metadata = tif.pages[0].description
    soup = Soup(metadata, 'lxml')
    tile_dict = {}

    # Layout parameters
    # -----------------
    # Set sectionId
    tile_dict['sectionId'] = section
    # Infer image row and column from image tile filename
    col, row = [int(i) for i in re.findall(r'\d+', filepath.name)[-2:]]
    tile_dict['imageRow'] = row
    tile_dict['imageCol'] = col
    # Parse metadata for stage coordinates
    tile_dict['stageX'] = 1e6 * float(soup.plane['positionx'])  # m --> um
    tile_dict['stageY'] = 1e6 * float(soup.plane['positiony'])  # m --> um
    # Parse metadata for pixel size
    psx = 1e3 * float(soup.pixels['physicalsizex'])  # um --> nm
    psy = 1e3 * float(soup.pixels['physicalsizey'])  # um --> nm
    tile_dict['pixelsize'] = (psx + psy) / 2         # nm/px

    # Tile specification parameters
    # -----------------------------
    # Set z based on section name
    tile_dict['z'] = int(re.findall(r'\d+', section)[-1])
    # Parse metadata for width and height
    tile_dict['width'] = int(soup.pixels['sizex'])
    tile_dict['height'] = int(soup.pixels['sizey'])
    # Set imageUrl and maskUrl
    tile_dict['imageUrl'] = filepath.as_uri()
    tile_dict['maskUrl'] = None
    # Set min, max intensity levels at 16bit uint limits
    tile_dict['minint'] = 0
    tile_dict['maxint'] = 2**16 - 1
    # Set empty list of transforms
    tile_dict['tforms'] = []
    # Set unique tileId
    tile_dict['tileId'] = f"{filepath.stem.split('-')[0]}-"\
                          f"{section}-{col:05d}x{row:05d}"

    # Additional tile specification parameters
    # ----------------------------------------
    # Parse metadata for acquisition time
    tile_dict['acqTime'] = pd.to_datetime(soup.acquisitiondate.text)

    return tile_dict
