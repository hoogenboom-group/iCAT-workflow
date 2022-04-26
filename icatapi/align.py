import requests
from functools import partial

from tqdm.notebook import tqdm
import numpy as np
import pandas as pd

from renderapi.client import (tilePairClient, pointMatchClient,
                              WithPool, SiftPointMatchOptions)
from renderapi.stack import get_z_values_for_stack

from .montage import run_point_match_client


__all__ = ['get_tile_pairs_4_alignment']


def get_tile_pairs_4_alignment(stack, render,
                               **renderapi_kwargs):
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
                                     render=render,
                                     **renderapi_kwargs)

    # Create DataFrame from json
    df_pairs = pd.json_normalize(tile_pairs_json['neighborPairs'])
    df_pairs['stack'] = stack
    return df_pairs


def run_point_match_client(tile_pair_batch, sift_options, stack, collection,
                           render, **pointMatchClient_kwargs):
    """Point match client wrapper for use in multiprocessing"""
    pointMatchClient(stack=stack,
                     collection=collection,
                     tile_pairs=tile_pair_batch,
                     sift_options=sift_options,
                     render=render,
                     **pointMatchClient_kwargs)


def generate_point_matches(df_pairs, match_collections, sift_options, render,
                           N_cores=4, batch_size=12, **pointMatchClient_kwargs):
    """Generate point matches for a set of tile pairs

    Parameters
    ----------
    df_pairs : `pd.DataFrame`
        DataFrame of tile pairs from a given stack (or stacks)
    match_collections : dict
        Mapping of stack names to names of
        e.g. {'lil_EM': 'zebrafish_lil_EM_points',
              'hoechst': 'zebrafish_hoechst_points'}
    sift_options : `renderapi.client.params.SiftPointMatchOptions`
        Parameter set for SIFT and RANSAC algorithms
    N_cores : scalar (optional)
        Number of cores to run point match generation in parallel
    batch_size : scalar (optional)
        Number of tile pairs to include in each batch
    pointMatchClient_kwargs : dict
        stack : str
            stack containing the tiles
        stack2 : str
            second optional stack containing tiles (if stack2 is not none, then
            tile_pair['p'] comes from stack and tile_pair['q'] comes from stack2)
        collection : str
            point match collection to save results into
        tile_pairs : iterable
            list of iterables of length 2 containing tileIds to calculate point matches between
        sift_options: SiftOptions
            options for running point matching
        pointMatchRender : renderapi.render.renderaccess
            renderaccess object specifying the render server to store point matches in
            defaults to values specified by render and its keyword argument overrides
        debugDirectory : str
            directory to store debug results (optional)
        filter: bool
            whether to apply default filtering to tile (default=False)
        renderWithoutMask: bool
            whether to exclude the mask when rendering tile (default=False)
        normalizeForMatching: bool
            whether to apply traditional 'normalizeForMatching' transform manipulation
            to image this removes the last transform from the transformList, then if
            there are more than 3 transforms continues to remove transforms until
            there are exactly 3.  Then assumes the image will be near 0,0 with a
            width/height that is about equal to the raw image width/height. This is
            true for Janelia's conventions for transformation alignment, but use at
            your own risk. (default=True)
        excludeTransformsAfterLast: str or None
            alternative to normalizeForMatching, which uses transformLabels.  Will
            remove all transformations after the last transformation with this transform
            label. i.e. if all lens corrections have a 'lens' label.  Then this will
            remove all non-lens transformations from the list. This is more general
            than normalizeForMatching=true, but requires you have transform labels applied.
            (default = None)
        excludeFirstTransformAndAllAfter: str
            alternative to normalizeForMatching which finds the first transform in the list with a given label
            and then removes that transform and all transforms that follow it. i.e. if you had a compound list
            of transformations, and you had labelled the first non-local transform 'montage' then setting
            excludeFirstTransformAndAllAfter='montage' would remove that montage transform and any other
            transforms that you had applied after it. (default=None).
        excludeAllTransforms: bool
            alternative to normalizeForMatching which simply removes all transforms from the list.
            (default=False)
        stackChannels: str or None
            If specified, option to select which channel is used for the stack.
            (default=None)
        stack2Channels: str or None
            If specified, option to select which channel is used for stack2, if specified.
            (default=None)
    """
    # Loop through alignment stacks
    for stack, tile_pairs in tqdm(df_pairs.groupby('stack')):

        # Group tile pairs into batches
        grouping = np.arange(len(tile_pairs)) // batch_size
        for _, batch in tqdm(tile_pairs.groupby(grouping), leave=False):

            # Set up `pointMatchClient` partial
            point_match_client_partial = partial(run_point_match_client,
                                                 stack=stack,
                                                 collection=match_collections[stack],
                                                 sift_options=sift_options,
                                                 render=render,
                                                 **pointMatchClient_kwargs)

            # Create batch of tile pairs
            tp_batch = [[tuple(tp)] for tp in batch[['p.id', 'q.id']].values.tolist()]

            # Run `pointMatchClient` on `N_cores`
            with WithPool(N_cores) as pool:
                pool.map(point_match_client_partial, tp_batch)


def delete_match_collection(match_collection, render):
    owner = render.DEFAULT_OWNER
    url = f'https://sonic.tnw.tudelft.nl/render-ws/v1/owner/{owner}/matchCollection/{match_collection}'
    response = requests.delete(url)
    return response
