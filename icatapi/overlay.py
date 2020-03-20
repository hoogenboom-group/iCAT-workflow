from pathlib import Path
import re

import numpy as np
from bs4 import BeautifulSoup as Soup
from matplotlib.transforms import Affine2D as AffineMPL
from skimage.external.tifffile import TiffFile


__all__ = ['get_transform_metadata',
           'compute_relative_transform',
           'compute_relative_transform_from_filepaths']


def get_transform_metadata(filepath):
    """Parse Odemis tif file for transform data

    Parameters
    ----------
    filepath : `Path`
        Path to image file

    Returns
    -------
    tform_md : tuple
        All the relevant Odemis transform data
        * pixelsize     | pixel size in x, y [m]
        * rotation      | rotation angle [rad]
        * shear         | shear [?]
        * translation   | stage-based translation in x, y [m]
    """
    # Gather metadata as `Soup`
    tif = TiffFile(filepath.as_posix())
    xml_data = tif.pages[0].image_description
    metadata = Soup(xml_data, 'lxml')

    # Parse the transform metadata for each image in tif
    tform_md = {}
    for md in metadata.find_all('image'):
        if md['name'] != 'Composited image preview':
            tform_md[md['name']] = parse_transform_metadata(md)
    return tform_md


def parse_transform_metadata(metadata):
    """Parse Odemis metadata for transform data

    Parameters
    ----------
    metadata : `Soup`
        Odemis metadata in a warm bowl of soup

    Returns
    -------
    pixelsize : tuple
        Image pixel size in x, y [m]
    rotation : float
        Image rotation angle [rad]
    shear : float
        Image shear [?]
    translation : tuple
        Stage-based translation in x, y [m]
    """
    # Calculate pixel size in x & y
    md = metadata.pixels
    psx = 1e-6 * float(md['physicalsizex'])  # um --> m
    psy = 1e-6 * float(md['physicalsizey'])  # um --> m
    pixelsize = (psx, psy)

    # Parse out rotation matrix
    md = metadata.transform
    A00 = float(md['a00'])  # /         \
    A01 = float(md['a01'])  # | a00  a01 |
    A10 = float(md['a10'])  # | a10  a11 |
    A11 = float(md['a11'])  # \         /
    # QR decomposition into Rotation and Scale matrices
    A = np.array([[A00, A10],
                  [A01, A11]])
    R, S = np.linalg.qr(A)
    mask = np.diag(S) < 0.
    R[:, mask] *= -1.
    S[mask, :] *= -1.
    # Calculate rotation angle and shear
    rotation = np.arctan2(R[1, 0], R[0, 0])
    rotation %= (2*np.pi)  # Odemis convention
    shear = S[0, 1] / S[0, 0]

    # Translation
    md = metadata.plane
    x0 = float(md['positionx'])
    y0 = float(md['positiony'])
    translation = (x0, y0)

    return pixelsize, rotation, shear, translation


def compute_relative_transform(psx_EM, psy_EM,
                               ro_EM, sh_EM,
                               trx_EM, try_EM,
                               psx_FM, psy_FM,
                               ro_FM, sh_FM,
                               trx_FM, try_FM):
    """Compute relative affine transformation

    Parameters
    ----------
    psx_EM, psy_EM : float
        EM pixel size in x, y [m]
    ro_EM : float
        EM rotation (should be ~0)
    sh_EM : float
        EM shear
    trx_EM, try_EM : float
        EM translation in x, y [m]
    psx_FM, psy_FM : float
        FM pixel size in x, y [m]
    ro_FM : float
        FM rotation
    sh_FM : float
        FM shear (should be ~0)
    trx_FM, try_FM : float
        FM translation in x, y [m]

    Returns
    -------
    A : 3x3 array
        Relative affine transformation
    """
    A = AffineMPL().rotate(-ro_FM)\
                   .skew(0, -sh_EM)\
                   .scale(psx_FM / psx_EM,
                          psy_FM / psy_EM)\
                   .translate((trx_FM - trx_EM) /  psx_EM,
                              (try_FM - try_EM) / -psy_EM)
    return A.get_matrix()


def compute_relative_transform_from_filepaths(fp_EM, fp_FM):
    """Compute affine transformation between correlative EM and FM image tiles

    Parameters
    ----------
    fp_EM : `Path`
        Filepath to EM image tile

    fp_FM : `Path`
        Filepath to FM image tile

    Returns
    -------
    A : 3x3 array
        Relative affine transformation
    """
    # Parse transform data
    (psx_EM, psy_EM), ro_EM, sh_EM, (trx_EM, try_EM) = get_transform_metadata(fp_EM)
    (psx_FM, psy_FM), ro_FM, sh_FM, (trx_FM, try_FM) = get_transform_metadata(fp_FM)

    # Pass transform data to `compute_relative_transform`
    A = compute_relative_transform(psx_EM, psy_EM,
                                   ro_EM, sh_EM,
                                   trx_EM, try_EM,
                                   psx_FM, psy_FM,
                                   ro_FM, sh_FM,
                                   trx_FM, try_FM)
    return A
