import numpy as np
import pandas as pd

from renderapi.render import get_stacks_by_owner_project
from renderapi.tilespec import TileSpec, get_tile_specs_from_stack
from renderapi.transform import AffineModel as AffineRender
from renderapi.stack import create_stack, set_stack_state
from renderapi.client import import_tilespecs


__all__ = ['create_stack_DataFrame',
           'create_stacks_DataFrame',
           'create_project_DataFrame']


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


def create_stack_from_DataFrame(df, render):
    """Creates a `render-ws` stack from given DataFrame

    Parameters
    ----------
    df : `pd.DataFrame`
        DataFrame of tile data
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    """
    # Set stack name
    stack = df.iloc[0]['stack']

    # Loop through tiles
    tile_specs = []
    for i, tile in df.iterrows():
        # Create `TileSpec`s
        ts = TileSpec(**tile.to_dict())
        # Adjust tile specifications
        if ('minIntensity' in tile.keys()) and\
           ('maxIntensity' in tile.keys()):
            ts['minint'] = int(tile['minIntensity'])
            ts['maxint'] = int(tile['maxIntensity'])
        if 'transforms' in tile.keys():
            ts['tforms'] = tile['transforms']
        # Collect `TileSpec`s
        tile_specs.append(ts)

    # Create stack
    create_stack(stack=stack,
                 render=render)

    # Import TileSpecs to render
    import_tilespecs(stack=stack,
                     tilespecs=tile_specs,
                     render=render)

    # Close stack
    set_stack_state(stack=stack,
                    state='COMPLETE',
                    render=render)
