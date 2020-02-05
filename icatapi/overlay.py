from pathlib import Path
import re

import numpy as np
from bs4 import BeautifulSoup as Soup
from skimage.external.tifffile import TiffFile


__all__ = ['get_transform_metadata',
           'compute_relative_transform',
           'compute_relative_transform_from_filepaths']


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


def compute_relative_transform(ps_EM, ps_FM,
                               ro_EM, ro_FM,
                               sh_EM, sh_FM,
                               tr_EM, tr_FM):
    """Compute relative affine transformation

    Parameters
    ----------
    ps_EM, ps_FM : tuple
        EM, FM pixelsize respectively
    ro_EM, ro_FM : float
        EM, FM rotation respectively
    sh_EM, sh_FM : float
        EM, FM shear respectively
    tr_EM, tr_FM : tuple
        EM, FM translation respectively

    Returns
    -------
    A : 3x3 array
        Relative affine transformation

    Notes
    -----
    Still some question over the correct order in which to apply the
    transformations. "Best" order found empirically was
        1. Rotation
        2. Translation
        3. Shear
        4. Scale
    Order seemingly used in Odemis
    (https://github.com/delmic/odemis/blob/master/src/odemis/gui/comp/canvas.py#L1044)
        1. Rotation
        2. Shear
        3. Translation
        4. Scale
    """
    # Calculate relative transform
    # ----------------------------
    sc_x = ps_FM[0] / ps_EM[0]
    sc_y = ps_FM[1] / ps_EM[1]
    ro = ro_FM - ro_EM
    sh = sh_EM - sh_FM
    tr_x = (tr_FM[0] - tr_EM[0]) / ps_EM[0]
    tr_y = (tr_FM[1] - tr_EM[1]) / ps_EM[1]

    # Create transformation matrices
    # ------------------------------
    # Scale
    S = np.array([[sc_x, 0, 0],
                  [0, sc_y, 0],
                  [0,    0, 1]])
    # Rotation
    R = np.array([[np.cos(-ro), -np.sin(-ro), 0],
                  [np.sin(-ro),  np.cos(-ro), 0],
                  [          0,            0, 1]])
    # Shear
    Sh = np.array([[1, sh, 0],
                   [0,  1, 0],
                   [0,  0, 1]])
    # Translation
    Tr = np.array([[1, 0, tr_x],
                   [0, 1, tr_y],
                   [0, 0,    1]])
    # Product
    A = R @ Sh @ Tr @ S
    return A


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
    tform_md_EM = get_transform_metadata(fp_EM)
    tform_md_FM = get_transform_metadata(fp_FM)

    # Pass transform data to `compute_relative_transform`
    tform_args = [tform_md_EM[0], tform_md_FM[0],
                  tform_md_EM[1], tform_md_FM[1],
                  tform_md_EM[2], tform_md_FM[2],
                  tform_md_EM[3], tform_md_FM[3]]
    A = compute_relative_transform(*tform_args)
    return A
