import numpy as np
import pandas as pd
from matplotlib.transforms import Affine2D as AffineMPL

from renderapi.transform import AffineModel as AffineRender

from .render_pandas import create_stack_DataFrame, create_stack_from_DataFrame


__all__ = ['AffineMPL_2_AffineRender',
           'scale_stack',
           'rotate_stack',
           'translate_stack',
           'transform_stack']


def AffineMPL_2_AffineRender(T):
    """Convert `AffineMPL` object to `AffineRender` object"""
    A = AffineRender()
    A.M = T.get_matrix()
    return A


def scale_stack(stack_in, stack_out=None, sx=1.0, sy=1.0,
                render=None):
    """Scale stack by an arbitrary scale factor

    Parameters
    ----------
    stack_in : str
        Input stack name
    stack_out : str (optional)
        Output stack name
        Overwrites input stack if not provided
    sx : float
        x scale factor
    sy : float
        y scale factor
    """
    # Create DataFrame for input stack
    df_stack = create_stack_DataFrame(stack=stack_in,
                                      render=render)

    # Create scaling transform
    T = AffineMPL().scale(sx, sy)
    A = AffineRender()
    A.M = T.get_matrix()

    # Add scale transform to DataFrame
    for i, tile in df_stack.iterrows():
        df_stack.at[i, 'tforms'] += [A]

    # Set output stack name
    stack_out = stack_out if stack_out is not None else stack_in

    # Create scaled stack
    create_stack_from_DataFrame(df=df_stack,
                                name=stack_out,
                                render=render)


def rotate_stack(stack_in, stack_out=None, r=0,
                 render=None):
    """Rotate stack by an arbitrary rotation

    Parameters
    ----------
    stack_in : str
        Input stack name
    stack_out : str (optional)
        Output stack name
        Overwrites input stack if not provided
    r : float
        rotation angle [rad]
    """
    # Create DataFrame for input stack
    df_stack = create_stack_DataFrame(stack=stack_in,
                                      render=render)

    # Create scaling transform
    T = AffineMPL().rotate(ro)
    A = AffineRender()
    A.M = T.get_matrix()

    # Add rotation transform to DataFrame
    for i, tile in df_stack.iterrows():
        df_stack.at[i, 'tforms'] += [A]

    # Set output stack name
    stack_out = stack_out if stack_out is not None else stack_in

    # Create scaled stack
    create_stack_from_DataFrame(df=df_stack,
                                name=stack_out,
                                render=render)


def translate_stack(stack_in, stack_out=None, tx=0.0, ty=0.0,
                    render=None):
    """Translate stack by an arbitrary translation

    Parameters
    ----------
    stack_in : str
        Input stack name
    stack_out : str (optional)
        Output stack name
        Overwrites input stack if not provided
    tx : float
        x translation [px]
    ty : float
        y translation [px]
    """
    # Create DataFrame for input stack
    df_stack = create_stack_DataFrame(stack=stack_in,
                                      render=render)

    # Create scaling transform
    T = AffineMPL().translate(tx, ty)
    A = AffineRender()
    A.M = T.get_matrix()

    # Add translation transform to DataFrame
    for i, tile in df_stack.iterrows():
        df_stack.at[i, 'tforms'] += [A]

    # Set output stack name
    stack_out = stack_out if stack_out is not None else stack_in

    # Create scaled stack
    create_stack_from_DataFrame(df=df_stack,
                                name=stack_out,
                                render=render)


def transform_stack(stack_in, stack_out=None, T=None,
                    render=None):
    """Transform stack by an arbitrary affine transformation

    Parameters
    ----------
    stack_in : str
        Input stack name
    stack_out : str (optional)
        Output stack name
        Overwrites input stack if not provided
    T : 3x3 array, `AffineMPL`, or `AffineRender` object
        Affine transform
    """
    # Create DataFrame for input stack
    df_stack = create_stack_DataFrame(stack=stack_in,
                                      render=render)

    # Create `AffineRender` transform object from given transform
    A = AffineRender()
    if isinstance(T, AffineMPL):
        A.M = T.get_matrix()
    elif isinstance(T, np.ndarray) and (T.shape == (3, 3)):
        A.M = T
    elif isinstance(T, AffineRender):
        pass
    else:
        raise ValueError("Improper form for transform.")

    # Add scale transform to DataFrame
    for i, tile in df_stack.iterrows():
        df_stack.at[i, 'tforms'] += [A]

    # Set output stack name
    stack_out = stack_out if stack_out is not None else stack_in

    # Create scaled stack
    create_stack_from_DataFrame(df=df_stack,
                                name=stack_out,
                                render=render)
