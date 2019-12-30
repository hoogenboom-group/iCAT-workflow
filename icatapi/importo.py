from pathlib import Path
import re

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as Soup
from skimage.external.tifffile import TiffFile


def parse_metadata(filepath, section):
    """Parses metadata from specified tile image filepath

    Parameters
    ----------
    filepath : `pathlib.Path`
        Path to tile image location in `pathlib.Path` representation
    section : str
        Name of section to which tile image belongs

    Returns
    -------
    tile_dict : dict
        Almighty dictionary containing lots of juicy info about the tile image
    """

    # Read metadata
    # -------------
    tif = TiffFile(filepath.as_posix())
    metadata = tif.pages[0].image_description
    soup = Soup(metadata, 'lxml')
    tile_dict = {}

    # Layout parameters
    # -----------------
    # Set sectionId
    tile_dict['sectionId'] = section
    # Parse metadata for scope and camera IDs
    tile_dict['scopeId'] = soup.microscope.get('model')
    tile_dict['cameraId'] = soup.detector.get('model')
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
    # Set unique tileId
    tile_dict['tileId'] = f"{filepath.stem.split('-')[0]}-"\
                          f"{section}-{col:05d}x{row:05d}"

    # Additional tile specification parameters
    # ----------------------------------------
    # Parse metadata for acquisition time
    tile_dict['acqTime'] = pd.to_datetime(soup.acquisitiondate.text)

    return tile_dict

