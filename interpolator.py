import json
import copy
import numpy as np


class Interpolator():
    '''
    Class which facilitates the interpolation of the annotations
    Manipulates the annotations.json file 
    '''

    def __init__(self, path, type: str):
        self.path = path
        self.type = type
        self.file = self.__load_file()

    def filter(self):
        shapes = copy.deepcopy(self.file[0]['shapes'])
        return [shape for shape in shapes if shape['type'] ==
                'polygon' and shape['label'] in ['lungslidingpresent', 'lungslidingabsent']]

    def __load_file(self):
        with open(self.path) as json_file:
            return json.load(json_file)

    def interpolate(frames: list[dict]):
        """
        Interpolates between two frames
        If polygons have different number of vertices, it adds or substracts vertices

            Parameters:
                frames (list[dict]): shapes grouped by frames which they are present in
        """
        offset = 1
        # iterates over grouped by frame shapes
        for i, group in enumerate(frames[:-1]):
            cut = max(0, len(group) - len(frames[i+1]))
            frames_to_interpolate = frames[i+1][0]['frame'] - frames[i][0]['frame']
            difference, step = [], []
            # iterates over shapes in a group
            for j, shape in enumerate(group):
                # TODO: One less in 1st
                # add points to the shape if the next shape has less points
                if len(shape['points']) < len(frames[i+1][j]['points']):
                    shape['points'] = add_substract_point(
                        [shape['points'], frames[i+1][j]['points']])
                # get the difference between the points of the same shape in the next group
                difference = (np.subtract(
                    frames[i+1][j]['points'], shape['points']))
                # get the step by which the points will be interpolated
                step.append(difference / frames_to_interpolate)
            # iterates over each shape in a group
            for k in range(1, frames_to_interpolate):
                for j, shape in enumerate(group[:-cut] if cut > 0 else group):
                    points = shape['points'].copy() + (step[j] * k)
                    skelet['points'] = list(points)
                    skelet['frame'] = shape['frame'] + k
                    annots[0]['shapes'].insert(indicies.get(
                        shape['frame']) + offset, copy.deepcopy(skelet))
                    offset += 1

    def add_substract_point(shapes: list[list[float]]):
        upper_left_idx = []
        add = True if len(shapes[0]) < len(shapes[1]) else False
        coords = [list(chunks(shapes[0], 2)),
                list(chunks(shapes[1], 2))]
        for i in range(len(shapes)):
            magnitudes = [np.sqrt(x.dot(x)) for x in coords[i]]
            # get most upper left
            upper_left = min(magnitudes)
            # append index of the upper left coord to list of max 2 indicies
            upper_left_idx.append(magnitudes.index(upper_left))

        # value by which all points will be shifted
        shift = coords[1][upper_left_idx[1]] - coords[0][upper_left_idx[0]]
        # shift all points in the second shape - align polygons
        # shifted_polygon = [point - shift for point in coords[1]]
        # start polygons from the most upper left point
        if upper_left_idx[0] != 0:
            coords[0] = np.roll(coords[0], -upper_left_idx[0], axis=0)
        if upper_left_idx[1] != 0:
            coords[1] = np.roll(coords[1], -upper_left_idx[1], axis=0)
        # number of points to be added or substracted
        diff = abs(len(coords[0]) - len(coords[1]))
        # count distances between all points
        distances_in_first = [int(np.linalg.norm(
            coords[0][i] - coords[0][i+1])) for i in range(len(coords[0])-1)]
        distances_in_second = [int(np.linalg.norm(
            coords[1][i] - coords[1][i+1])) for i in range(len(coords[1])-1)]
        # add points
        if add:
            for i in range(diff):
                # find the index of the different distance
                for i in range(len(distances_in_first)):
                    if abs(distances_in_first[i] - distances_in_second[i]) > 10:
                        # add point between the two points
                        coords[0] = np.insert(
                            coords[0], i+1, (coords[1][i+1] - shift), axis=0)
                        break
        return coords[0].flatten().tolist()