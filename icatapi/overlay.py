from pathlib import Path
import re

import numpy as np
from bs4 import BeautifulSoup as Soup
from skimage.external.tifffile import TiffFile


def get_transform_metadata(filepath):
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
    md = soup.plane
    x0 = float(md['positionx'])
    y0 = float(md['positiony'])
    translation = (x0, y0)

    return pixelsize, rotation, shear, translation


def compute_relative_transform(fp_EM, fp_FM):
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
    # --------------------
    tform_md_EM = get_transform_metadata(fp_EM)
    tform_md_FM = get_transform_metadata(fp_FM)

    # Calculate relative transform
    # ----------------------------
    scale_x = tform_md_FM[0][0] / tform_md_EM[0][0]
    scale_y = tform_md_FM[0][1] / tform_md_EM[0][1]
    rotation = tform_md_FM[1]
    shear = tform_md_EM[2]
    translation_x = (tform_md_FM[3][0] - tform_md_EM[3][0]) / tform_md_EM[0][0]
    translation_y = (tform_md_FM[3][1] - tform_md_EM[3][1]) / tform_md_EM[0][1]

    # Create transformation matrices
    # ------------------------------
    # Scale
    S = np.array([[scale_x, 0, 0],
                  [0, scale_y, 0],
                  [0,       0, 1]])
    # Rotation
    R = np.array([[np.cos(-rotation), -np.sin(-rotation), 0],
                  [np.sin(-rotation),  np.cos(-rotation), 0],
                  [                0,                  0, 1]])
    # Shear
    Sh = np.array([[1, shear, 0],
                  [0,     1, 0],
                  [0,     0, 1]])
    # Translation
    Tr = np.array([[1, 0, translation_x],
                  [0, 1, translation_y],
                  [0, 0,             1]])
    # Product
    A = R @ Tr @ Sh @ S
    return A
