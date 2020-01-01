from pathlib import Path
import re

import numpy as np
from bs4 import BeautifulSoup as Soup
from skimage.external.tifffile import TiffFile


def get_tform_metadata(filepath):
    """Parse Odemis (single-page) tiff file for transformation data

    Parameters
    ----------
    filepath : `Path`
        Path to image file

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
    # Gather metadata as `Soup`
    tif = TiffFile(filepath.as_posix())
    metadata = tif.pages[0].image_description
    soup = Soup(metadata, 'lxml')

    # Calculate pixel size in x & y
    md = soup.pixels
    psx = 1e-6 * float(md['physicalsizex'])  # um --> m
    psy = 1e-6 * float(md['physicalsizey'])  # um --> m
    pixelsize = (psx, psy)

    # Parse out rotation matrix
    md = soup.transform
    A00 = float(md['a00'])  #  /         \
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
    md = soup.plane
    x0 = float(md['positionx'])
    y0 = float(md['positiony'])
    translation = (x0, y0)

    return pixelsize, rotation, shear, translation
