import re

import numpy as np
import pandas as pd
from pd.io.json import json_normalize

from renderapi.client import tilePairClient
from renderapi.stack import get_z_values_for_stack
from rendearpi.pointmatch import get_matches_within_group


__all__ = ['get_tile_pairs_4_montage',
           'get_matches_within_section']


def get_tile_pairs_4_montage(stack, render):
    """Collect tile pairs from stack one section at a time for montaging

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


def get_matches_within_section(match_collection, sectionId, render):
    """Create DataFrame of point matches for a given section

    Parameters
    ----------
    match_collection : str
        Name of match collection
    sectionId : str
        Name of section
        Aka `groupId` in `renderapi` terminology
    render : `renderapi.render.RenderClient`
        `render-ws` instance

    Returns
    -------
    df_matches : `pd.DataFrame`
        DataFrame of point matches from a given section
    """
    # Initialize point matches DataFrame
    matches_cols = ['pc', 'pr', 'qc', 'qr', 'N_matches']
    df_matches = pd.DataFrame(columns=matches_cols)

    # Get point match data as json via `renderapi`
    matches_json = get_matches_within_group(matchCollection=match_collection,
                                            groupId=sectionId,
                                            render=render)
    # Create DataFrame from json and concatenate with point matches DataFrame
    df_matches = pd.concat([df_matches, json_normalize(matches_json)],
                           axis=1, sort=False)

    # Populate DataFrame with row, column and number of matches data
    df_matches[['pc', 'pr']] = np.stack(df_matches['pId'].apply(lambda x:\
                                   [int(i) for i in re.findall('\d+', x)[-2:]]))
    df_matches[['qc', 'qr']] = np.stack(df_matches['qId'].apply(lambda x:\
                                   [int(i) for i in re.findall('\d+', x)[-2:]]))
    df_matches['N_matches'] = df_matches['matches.p'].apply(lambda x:\
                                  np.array(x).shape[1])
    return df_matches
