import numpy as np
import pandas as pd
import renderapi


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
    tile_specs = renderapi.tilespec.get_tile_specs_from_stack(stack=stack,
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
    # Drop `transforms` column
    if 'transforms' in df_stack.columns:
        df_stack.drop('transforms', axis=1, inplace=True)
    # Return stack DataFrame
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
    return df_stacks


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
    stacks = renderapi.render.get_stacks_by_owner_project(render=render)
    df_project = create_stacks_DataFrame(stacks, render=render)
    return df_project


def create_transforms_DataFrame(stack, render):
    """
    """
    # Gather tile specifications from specified stack
    tile_specs = renderapi.tilespec.get_tile_specs_from_stack(stack=stack,
                                                              render=render)
    # Create DataFrame from tile specifications
    df_stack = pd.DataFrame([ts.to_dict() for ts in tile_specs])
    # Do a ridiculous number of pandas hacks to unpack transforms
    df_transforms = df_stack['transforms'].apply(pd.Series)['specList']\
                                          .apply(pd.Series)\
                                          .unstack()\
                                          .apply(pd.Series)['dataString']\
                                          .str.split(' ')\
                                          .to_frame()\
                                          .unstack(level=0)
    # Remove multiindex column
    df_transforms.columns = df_transforms.columns.droplevel()
    # Rename columns to (`T0`, `T1`, `T2`, ...)
    mapping = zip(df_transforms.columns,
                  [f"T{i}" for i in df_transforms.columns])
    df_transforms.rename(columns={k: v for k, v in mapping}, inplace=True)
    # Convert string data to float
    df_transforms = pd.DataFrame([df_transforms[T].apply(
        np.array, **{'dtype': float}) for T in df_transforms.columns]).T
    return df_transforms
