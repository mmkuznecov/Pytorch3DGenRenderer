import numpy as np

def pendulum(samples):
    # Constants
    a = 0.8
    k = 1
    R = 1
    t = np.linspace(0, 2*np.pi, samples)

    # Generate points
    xx = R * (np.cos(t) * np.cos(k*t) * np.cos(a) - np.sin(t) * np.sin(k*t))
    yy = R * (np.sin(t) * np.cos(k*t) * np.cos(a) + np.cos(t) * np.sin(k*t))
    zz = R * (np.cos(k*t) * np.sin(a))

    points = np.column_stack((xx, yy, zz))

    # Calculate angles
    azimuth = np.degrees(np.arctan2(points[:, 2], points[:, 0]))
    elevation = np.degrees(np.arcsin(points[:, 1]))

    angles = np.column_stack((azimuth, elevation))

    return angles

def fibonacci_sphere(samples=200, randomize=True):

    rnd = 1.0
    if randomize:
        rnd = np.random.random() * samples

    offset = 2.0 / samples
    increment = np.pi * (3.0 - np.sqrt(5.0))
    
    indices = np.arange(samples)
    y = ((indices * offset) - 1) + (offset / 2)
    r = np.sqrt(1 - y**2)
    phi = (indices + rnd) % samples * increment

    x = np.cos(phi) * r
    z = np.sin(phi) * r

    azimuth = np.arctan2(y, x) * (180 / np.pi)
    elevation = np.arccos(z) * (180 / np.pi)

    return np.column_stack((azimuth, elevation))

def circle(samples=24, elevation=35):

    azimuths = np.linspace(0, 360, samples, endpoint=False)
    elevations = np.full(samples, elevation)
    
    return np.column_stack((azimuths, elevations))