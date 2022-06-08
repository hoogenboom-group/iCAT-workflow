import numpy as np
from skimage import color, exposure


__all__ = ['colorize']


def colorize(image, T):
    """Colorize image
    Parameters
    ----------
    image : (M, N) array
    Returns
    -------
    rescaled : rgba float array
        Color transformed image
    """
    # Convert to rgba
    rgba = color.gray2rgba(image, alpha=True)
    # Apply transform
    transformed = np.dot(rgba, T)
    rescaled = exposure.rescale_intensity(transformed)
    return rescaled


# Color transformations
# ---------------------
# Labels
T_HOECHST = [[0.2, 0.0, 0.0, 0.2],  # blueish
             [0.0, 0.2, 0.0, 0.2],
             [0.0, 0.0, 1.0, 1.0],
             [0.0, 0.0, 0.0, 0.0]]
T_AF594 = [[1.0, 0.0, 0.0, 1.0],  # orangeish
           [0.0, 0.6, 0.0, 0.6],
           [0.0, 0.0, 0.0, 0.0],
           [0.0, 0.0, 0.0, 0.0]]
# Primary colors
T_RED = [[1.0, 0.0, 0.0, 1.0],
         [0.0, 0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0, 0.0]]
T_GREEN = [[0.0, 0.0, 0.0, 0.0],
           [0.0, 1.0, 0.0, 1.0],
           [0.0, 0.0, 0.0, 0.0],
           [0.0, 0.0, 0.0, 0.0]]
T_BLUE = [[0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 1.0],
          [0.0, 0.0, 0.0, 0.0]]
T_YELLOW = [[1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0]]
