import re
import warnings
import xml.etree.ElementTree as ET

import pandas as pd
from bs4 import BeautifulSoup as Soup
from tifffile import TiffFile, TiffWriter
from skimage import img_as_uint
from skimage.color import rgb2gray

from renderapi.image_pyramid import ImagePyramid, MipMapLevel


# TU Delft storage server
HOST = 'https://sonic.tnw.tudelft.nl'


def create_tile_dict(fp, d_tile=None, host=HOST):
    """Parses Odemis OME-TIFF metadata to create a dict resembling a tile specification

    Parameters
    ----------
    fp : `pathlib.Path`
        Filepath
    d_tile : dict, (optional)
        Pre-populated tile dictionary
    host : str (optional)
        Host url for the image pyramid

    Returns
    -------
    d_tile : dict
        Almighty dictionary containing lots of juicy info about the image tile
    """
    # Extract metadata
    # ----------------
    tif = TiffFile(fp.as_posix())
    metadata = tif.pages[0].description
    soup = Soup(metadata, 'lxml')

    # Initialize tile dict
    # --------------------
    if d_tile is None:
        d_tile = {}
    # Infer stack, z value, and sectionId
    if 'stack' not in d_tile:
        d_tile['stack'] = fp.parents[2].name
    if 'z' not in d_tile:
        d_tile['z'] = -1
    if 'sectionId' not in d_tile:
        d_tile['sectionId'] = fp.parents[1].name

    # Layout parameters
    # -----------------
    # Infer image row and column from filepath
    col, row = [int(i) for i in re.findall(r'\d+', fp.parent.name)[:2]]
    d_tile['imageRow'] = row
    d_tile['imageCol'] = col
    # Parse metadata for stage coordinates
    d_tile['stageX'] = 1e6 * float(soup.plane['positionx'])  # m --> um
    d_tile['stageY'] = 1e6 * float(soup.plane['positiony'])  # m --> um
    # Parse metadata for pixel size
    psx = 1e3 * float(soup.pixels['physicalsizex'])  # um --> nm
    psy = 1e3 * float(soup.pixels['physicalsizey'])  # um --> nm
    d_tile['pixelsize'] = (psx + psy) / 2            # nm/px
    # Parse metadata for acquisition timestamp
    d_tile['acqTime'] = pd.to_datetime(soup.acquisitiondate.text)

    # Image pyramid
    # -------------
    # Create nested MipMapLevels
    mmls = []
    for mmfp in sorted(fp.parent.glob('[0-9].tif')):
        level = mmfp.stem
        imageUrl = f"{host}{mmfp.as_posix()}"
        mml = MipMapLevel(level, imageUrl=imageUrl, maskUrl=None)
        mmls.append(mml)
    # Create ImagePyramid from MipMapLevels
    ip = ImagePyramid({mm.level: mm.mipmap for mm in mmls})
    d_tile['imagePyramid'] = ip

    # Remaining tile specifications
    # -----------------------------
    # Set unique tileId
    d_tile['tileId'] = f"{d_tile['stack']}-{d_tile['sectionId']}-{col:05d}x{row:05d}"
    # Parse metadata for width and height
    d_tile['width'] = int(soup.pixels['sizex'])
    d_tile['height'] = int(soup.pixels['sizey'])
    # Set min, max intensity levels at 16bit uint limits
    d_tile['minint'] = 0
    d_tile['maxint'] = 2**16 - 1
    # Set empty list of transforms
    d_tile['tforms'] = []

    return d_tile
