import re
import warnings
import xml.etree.ElementTree as ET

import pandas as pd
from bs4 import BeautifulSoup as Soup
from tifffile import TiffFile, TiffWriter

from skimage import img_as_uint
from skimage.color import rgb2gray


__all__ = ['parse_metadata',
           'write_tif',
           'split_tif']


# TU Delft storage server
HOST = 'https://sonic.tnw.tudelft.nl'


def parse_metadata(filepath, stack=None, z=None, sectionId=None, host=HOST):
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

    # Infer stack and section info
    # ----------------------------
    if stack is None:
        stack = filepath.parents[1].name
    if sectionId is None:
        sectionId = filepath.parents[0].name
    if z is None:
        z = int(re.findall(r'\d+', sectionId)[-1])

    # Layout parameters
    # -----------------
    tile_dict = {}
    # Infer image row and column from image tile filename
    col, row = [int(i) for i in re.findall(r'\d+', filepath.stem)[-2:]]
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
    tile_dict['stack'] = stack
    tile_dict['z'] = z
    tile_dict['sectionId'] = sectionId
    # Set unique tileId
    tile_dict['tileId'] = f"{stack}-{sectionId}-{col:05d}x{row:05d}"
    # Parse metadata for width and height
    tile_dict['width'] = int(soup.pixels['sizex'])
    tile_dict['height'] = int(soup.pixels['sizey'])
    # Set imageUrl and maskUrl
    tile_dict['imageUrl'] = f"{host}{filepath.as_posix()}"
    tile_dict['maskUrl'] = None
    # Set min, max intensity levels at 16bit uint limits
    tile_dict['minint'] = 0
    tile_dict['maxint'] = 2**16 - 1
    # Set empty list of transforms
    tile_dict['tforms'] = []

    # Additional tile specification parameters
    # ----------------------------------------
    # Parse metadata for acquisition time
    tile_dict['acqTime'] = pd.to_datetime(soup.acquisitiondate.text)

    return tile_dict


def write_tif(fp, image):
    """Simple wrapper for tifffile.TiffWriter"""
    # Convert to grey scale 16-bit image
    with warnings.catch_warnings():      # Suppress precision
        warnings.simplefilter('ignore')  # loss warnings
        image = img_as_uint(rgb2gray(image))

    # Save to disk with `TiffWriter`
    fp.parent.mkdir(parents=False, exist_ok=True)
    with TiffWriter(fp.as_posix()) as tif:
        tif.save(image)


def split_tif(tif):
    """Divide multi-channel tif

    Parameters
    ----------
    tif : `TiffFile`
        Input tif file

    Returns
    -------
    tifs : dict
        Mapping from each channel to tuple containing image data + metadata
        {'channel': (ndarray, Soup)}
    """
    # Read tif metadata
    soup = Soup(tif.pages[0].description, 'lxml')

    # Iterate through pages and image metadata
    tifs = {}
    for page, metadata in zip(tif.pages, soup.find_all('image')):

        # --- Build up metadata for each new tif ---
        # Create ET root with OME header info
        root = ET.Element('OME', attrib={
                "xmlns": "http://www.openmicroscopy.org/Schemas/OME/2012-06",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.openmicroscopy.org/Schemas/OME/2012-06 "
                                      "http://www.openmicroscopy.org/Schemas/OME/2012-06/ome.xsd"})
        # Add OME comment
        com_txt = ("Warning: this comment is an OME-XML metadata block, which "
                   "contains crucial dimensional parameters and other important "
                   "metadata. Please edit cautiously (if at all), and back up the "
                   "original data before doing so. For more information, see the "
                   "OME-TIFF web site: http://ome-xml.org/wiki/OmeTiff.")
        root.append(ET.Comment(com_txt))

        # --- Instrument layout ---
        # Add instrument and microscope tags
        instr = ET.SubElement(root, "Instrument", attrib={"ID": "Instrument:0"})
        micro = ET.SubElement(instr, "Microscope", attrib={
            "Manufacturer": "Delmic",
            "Model": "SECOM"})

        # Extract detector, lightsource, and objective settings
        # Add detector settings to instrument
        if metadata.detectorsettings is not None:
            for detector in soup.find_all('detector'):
                if detector['id'] == metadata.detectorsettings['id']:
                    instr.append(ET.fromstring(detector.decode()))
        else:
            detector = ET.SubElement(instr, "Detector", attrib={
                "ID": "Detector:0",
                "model": "pcie-6251"})
        # Add lightsource settings to instrument
        if metadata.lightsourcesettings is not None:
            for lightsource in soup.find_all('lightsource'):
                if lightsource['id'] == metadata.lightsourcesettings['id']:
                    instr.append(ET.fromstring(lightsource.decode()))
        # Add objective settings to instrument
        if metadata.objectivesettings is not None:
            for objective in soup.find_all('objective'):
                if objective['id'] == metadata.objectivesettings['id']:
                    instr.append(ET.fromstring(objective.decode()))

        # --- Image layout ---
        root.append(ET.fromstring(metadata.decode()))

        # Convert ElementTree to Soup
        tree = ET.ElementTree(root)
        et = (b'<?xml version="1.0" encoding="UTF-8"?>' +
              ET.tostring(tree.getroot(), encoding='utf-8'))
        md = Soup(et, 'lxml')

        # --- Populate tifs dict ---
        tifs[page.tags['PageName'].value] = (page.asarray(), md)

    return tifs
