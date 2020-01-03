import numpy as np
import pandas as pd

from renderapi.render import get_stacks_by_owner_project
from renderapi.tilespec import get_tile_specs_from_stack
from renderapi.stack import get_z_values_for_stack
from renderapi.transform import AffineModel as AffineRender
from renderapi.client import tilePairClient


def create_stack_DataFrame(stack, render):
    """Create DataFrame of `TileSpec`s from a given stack

    Parameters
    ----------
    stack : str
        Stack from which to generate DataFrame
    render : `renderapi.render.RenderClient`
        `render-ws` instance

    Returns
    -------
    df_stack : `pd.DataFrame`
        DataFrame of all `TileSpec`s from given stack
    """
    # Gather tile specifications from specified stack
    tile_specs = get_tile_specs_from_stack(stack=stack,
                                           render=render)
    # Create DataFrame from tile specifications
    df_stack = pd.DataFrame([ts.to_dict() for ts in tile_specs])
    # Add stack to DataFrame
    df_stack['stack'] = stack

    # Expand `layout` column
    if 'layout' in df_stack.columns:
        df_stack = pd.concat([df_stack.drop('layout', axis=1),
                              df_stack['layout'].apply(pd.Series)], axis=1)

    # Collapse `mipmapLevels` column to get `imageUrl`
    if 'mipmapLevels' in df_stack.columns:
        df_stack = pd.concat([df_stack.drop('mipmapLevels', axis=1),
                              df_stack['mipmapLevels'].apply(pd.Series)['0']\
                                                      .apply(pd.Series)], axis=1)

    # Collapse `transforms` column and create list of `AffineRender` transforms
    if 'transforms' in df_stack.columns:
        df_stack = pd.concat([df_stack.drop('transforms', axis=1),
                              df_stack['transforms'].apply(
                                  lambda x: [AffineRender(*np.array(
                                  x['specList'][i]['dataString'].split(
                                  ' '), dtype=np.float))\
                                  for i in range(len(x['specList']))])], axis=1)

    return df_stack


def create_stacks_DataFrame(stacks, render):
    """Create DataFrame of `TileSpec`s from multiple stacks within a project

    Parameters
    ----------
    stacks : list
        List of stacks from which to generate DataFrame
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    
    Returns
    -------
    df_stacks : `pd.DataFrame`
        DataFrame of all `TileSpec`s from given stacks
    """
    # Initialize DataFrame
    df_stacks = pd.DataFrame()
    # Create and append DataFrames from each given stack
    for stack in stacks:
        df_stack = create_stack_DataFrame(stack, render=render)
        df_stacks = df_stacks.append(df_stack, sort=False)
    return df_stacks.reset_index(drop=True)


def create_project_DataFrame(render):
    """Create DataFrame of `TileSpec`s from all stacks within a project

    Parameters
    ----------
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    
    Returns
    -------
    df_project : `pd.DataFrame`
        DataFrame of all `TileSpec`s from within a project
    """
    # Get all stacks within project
    stacks = get_stacks_by_owner_project(render=render)
    df_project = create_stacks_DataFrame(stacks, render=render)
    return df_project


def get_tile_pairs_4_montage(stack, render):
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
