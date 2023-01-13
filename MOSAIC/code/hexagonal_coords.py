import numpy as np


def hex_coordinates(distance, n_rings):
    """
    Central coordinates for each element in concentric rings of hexagons

    This function generates coordonates (x, y) for a specific hexagonal number
    by using a specific distance between the center of each hexagonal.

    Contributed by: Jean-Sebastien Kersaint Tournebize

    Parameters
    ----------
    distance : float
        The distance between the center of each hexagonal
    n_rings : int
        The number of hexagonal groups
        E.: 1 n_hex = 7 hexagonals | 2 n_hex = 19 hexagonals

    Returns
    -------
    coordinates : list
        coordinates of each hexagonal

    """

    x, y = [0], [0]
    for q in range(-n_rings, n_rings + 1):
        r1 = max(-n_rings, -q - n_rings)
        r2 = min(n_rings, -q + n_rings)
        for r in range(r1, r2 + 1):
            x += [distance * (3 ** 0.5) * (q + r / 2)]
            y += [distance * 3 * r]

    return x, y


import matplotlib.pyplot as plt
x, y = hex_coordinates(0.19, 3)
plt.plot(x, y, ".")
plt.gca().set_aspect("equal")
plt.show()
plt.pause()
