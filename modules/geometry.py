import cv2
import numpy as np

def find_extrema_rectangle(points):
    """Find the extrema of a polygon and return rectangle coordinates."""
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    return [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]

def intersect(polygon1, polygon2):
    """Check if two polygons intersect"""
    polygon1 = np.array(polygon1, dtype=np.int32)
    polygon2 = np.array(polygon2, dtype=np.int32)
    basic_img = np.zeros([1000, 1000], dtype=np.uint8)
    red_poly = basic_img.copy()
    cv2.fillPoly(red_poly, [polygon1], 1)
    blue_poly = basic_img.copy()
    cv2.fillPoly(blue_poly, [polygon2], 1)
    intersection = red_poly * blue_poly
    return np.any(intersection)