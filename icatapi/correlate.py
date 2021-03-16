import numpy as np
import pandas as pd

from renderapi.tilespec import get_tile_spec, get_tile_specs_from_minmax_box


def bboxes_overlap(bbox_1, bbox_2):
    """Determines if two bounding boxes overlap or coincide

    Parameters
    ----------
    bbox_1 : 4-tuple
        1st bounding box
        convention: (minX, minY, maxX, maxY)

    bbox_2 : 4-tuple
        2nd bounding box
        convention: (minX, minY, maxX, maxY)

    Returns
    -------
    overlap : bool
        True if bounding boxes overlap / coincide
        False otherwise
    """
    # 2 tiles overlap iff their projections onto both x and y axis overlap
    # Overlap in 1D iff box1_max > box2_min AND box1_min < box2_max
    overlap = ((bbox_1[2] >= bbox_2[0]) and (bbox_1[0] <= bbox_2[2])) and \
              ((bbox_1[3] >= bbox_2[1]) and (bbox_1[1] <= bbox_2[3]))
    return overlap


def get_overlapping_tiles(stack, tileId, render, stack2=None):
    """Finds set of overlapping tiles for a given tile

    Parameters
    ----------
    stack : str
        Stack from which the tile is from
    tileId : str
        TileId
    render : `renderapi.render.RenderClient`
        `render-ws` instance
    stack2 : str, optional
        Stack for which to look for overlapping tiles

    Returns
    -------
    overlapping_tileIds : list
        Tile IDs of overlapping tiles
    """
    # Get tile specification
    ts = get_tile_spec(stack=stack,
                       tile=tileId,
                       render=render)

    # Get bounding box of tile specification
    bbox = ts.bbox

    # Get overlapping tiles
    overlap_stack = stack2 if stack2 is not None else stack
    overlapping_tileIds = [ts.tileId for ts in \
                           get_tile_specs_from_minmax_box(stack=overlap_stack,
                                                          z=ts.z,
                                                          xmin=bbox[0],
                                                          xmax=bbox[2],
                                                          ymin=bbox[1],
                                                          ymax=bbox[3],
                                                          render=render)]

    return overlapping_tileIds
