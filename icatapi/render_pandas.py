

import numpy as np
import pandas as pd

from renderapi.tilespec import get_tile_specs_from_stack


def create_stack_DataFrame(stack, render):
    """
    """
    # Gather tile specifications from specified stack
    tile_specs = get_tile_specs_from_stack(stack=stack,
                                        render=render)
    # Create DataFrame from tile specifications
    df_stack = pd.DataFrame([ts.to_dict() for ts in tile_specs])
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


def create_project_DataFrame():
    """
    """
    pass


def create_transform_DataFrame():
    """
    """
    pass
