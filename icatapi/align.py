import numpy as np
import pandas as pd

from renderapi.client import tilePairClient
from renderapi.stack import get_z_values_for_stack


def get_tile_pairs_4_alignment(stack, render, zNeighborDistance=1):
    """Collect tile pairs across multiple sections for alignment

    Parameters
    ----------
    stack : str
        Stack from which to generate DataFrame
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    zNeighborDistance : int
        Number of z sections defining the half-height of search cylinder

    Returns
    -------
    df_pairs : `pd.DataFrame`
        DataFrame of tile pairs from a given stack
    """
    # Get stack's z values
    z_values = get_z_values_for_stack(stack=stack,
                                      render=render)

    # Search for tile pairs across all sections
    tile_pairs_json = tilePairClient(stack=stack,
                                     minz=min(z_values),
                                     maxz=max(z_values),
                                     excludeSameLayerNeighbors=True,
                                     zNeighborDistance=zNeighborDistance,
                                     render=render)

    # Create DataFrame from json
    df_pairs = pd.io.json.json_normalize(tile_pairs_json['neighborPairs'])
    df_pairs['stack'] = stack
    return df_pairs
