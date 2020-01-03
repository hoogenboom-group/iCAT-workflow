import numpy as np
import pandas as pd

from renderapi.client import tilePairClient
from renderapi.stack import get_z_values_for_stack


def get_tile_pairs(stack, render):
    """Collect tile pairs from stack one section at a time

    Parameters
    ----------
    stack : str
        Stack from which to generate DataFrame
    render : `renderapi.render.RenderClient`
        `render-ws` instance

    Returns
    -------
    df_pairs : `pd.DataFrame`
        DataFrame of tile pairs from a given stack
    """
    # Initialize tile pairs DataFrame
    pairs_cols = ['stack', 'z']
    df_pairs = pd.DataFrame(columns=pairs_cols)

    # Iterate through stack's z values
    z_values = get_z_values_for_stack(stack=stack,
                                      render=render)
    for z in z_values:

        # Generate tile pairs
        tile_pairs_json = tilePairClient(stack,
                                         minz=z,
                                         maxz=z,
                                         render=render)
        # Create DataFrame from json
        df = pd.io.json.json_normalize(tile_pairs_json['neighborPairs'])
        df['z'] = z
        df_pairs = df_pairs.append(df, sort=False)

    # Add stack info and reset index
    df_pairs['stack'] = stack
    return df_pairs.reset_index(drop=True)
