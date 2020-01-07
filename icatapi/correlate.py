import numpy as np
import pandas as pd


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
