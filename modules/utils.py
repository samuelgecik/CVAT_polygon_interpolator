import numpy as np
import copy
from .geometry import *


def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.
    """
    chunks_lst = []
    for i in range(0, len(lst), n):
        chunks_lst.append(lst[i : i + n])
    return chunks_lst


def get_indicies(shapes: list[dict]):
    """
    Get indiecies of the last shapes in each frame
    """
    return dict((d["frame"], index) for (index, d) in enumerate(shapes))


def group_shapes_by_frame(filtered_shapes: list):
    """
    Groups shapes by frame
    """
    frame = 0
    last_frame = filtered_shapes[-1]["frame"]
    last_shape_idx = len(filtered_shapes) - 1
    shapes_by_frame = []
    shapes_in_single_frame = []
    for i, shape in enumerate(filtered_shapes):
        if shape["frame"] == frame:
            shapes_in_single_frame.append(shape)
            # if multiple shapes in the last frame, add to shapes_by_frame
            if i == last_shape_idx:
                shapes_by_frame.append(shapes_in_single_frame)

        else:
            frame = frame + 10 if (frame + 10) < last_frame else last_frame
            shapes_by_frame.append(shapes_in_single_frame)
            shapes_in_single_frame = []
            shapes_in_single_frame.append(shape)
    return shapes_by_frame


def remove_duplicates(shapes_by_frame: list[list]):
    """
    Removes duplicate shapes on the same frame
    """
    # remove duplicate shapes in the same frame
    for frame in shapes_by_frame:
        if len(frame) == 1:
            continue
        # find if two polygons intersect by comparing each other
        for i in range(len(frame)):
            for j in range(i + 1, len(frame)):
                if intersect(
                    chunks(frame[i]["points"], 2), chunks(frame[j]["points"], 2)
                ):
                    # remove one of the polygons
                    frame.pop(j)


def assign_id(shapes_by_frame: list[list]):
    """
    Assigns id to each shape in the list of shapes grouped by frame
    ID is assigned according to the position of the shape in the frame
    """
    id_count = 0
    # assign id to shapes in the first frame
    for i, shape in enumerate(shapes_by_frame[0]):
        shape["id"] = i
        id_count += 1

    # assign id to shapes in the rest of the frames
    for i, frame in enumerate(shapes_by_frame[1:], start=1):
        for shape in frame:
            # check if the shape with the same id is present in the previous frame
            # if same label and square intersect: then same id else: new id
            for prev_shape in shapes_by_frame[i - 1]:
                if shape["label"] == prev_shape["label"] and intersect(
                    find_extrema_rectangle(chunks(shape["points"], 2)),
                    find_extrema_rectangle(chunks(prev_shape["points"], 2)),
                ):
                    shape["id"] = prev_shape["id"]
                    break
            else:
                shape["id"] = id_count
                id_count += 1


def get_skelet(type: str):
    """
    Get the skeleton of the shape
    """
    return {
        "type": "polygon",
        "occluded": False,
        "z_order": 0,
        "points": [],
        "frame": 0,
        "group": 0,
        "source": "manual",
        "attributes": [],
        "label": type,
    }


def add_remove_point(shapes: list[list[float]]):
    """
    Add or remove a point to/from the shape
    """
    upper_left_idx = []
    add = True if len(shapes[0]) < len(shapes[1]) else False
    coords = np.array([list(chunks(shapes[0], 2)), list(chunks(shapes[1], 2))])
    for i in range(len(shapes)):
        magnitudes = [np.sqrt(x.dot(x)) for x in coords[i]]
        # get most upper left
        upper_left = min(magnitudes)
        # append index of the upper left coord to list of max 2 indicies
        upper_left_idx.append(magnitudes.index(upper_left))

    # value by which all points will be shifted
    shift = coords[1][upper_left_idx[1]] - coords[0][upper_left_idx[0]]
    # start polygons from the most upper left point
    if upper_left_idx[0] != 0:
        coords[0] = np.roll(coords[0], -upper_left_idx[0], axis=0)
    if upper_left_idx[1] != 0:
        coords[1] = np.roll(coords[1], -upper_left_idx[1], axis=0)
    # number of points to be added or substracted
    diff = abs(len(coords[0]) - len(coords[1]))
    # count distances between all points
    distances_in_first = [
        int(np.linalg.norm(coords[0][i] - coords[0][i + 1]))
        for i in range(len(coords[0]) - 1)
    ]
    distances_in_second = [
        int(np.linalg.norm(coords[1][i] - coords[1][i + 1]))
        for i in range(len(coords[1]) - 1)
    ]

    for _ in range(diff):
        for i in range(len(distances_in_first)):
            # compare differences between distances with treshold
            if abs(distances_in_first[i] - distances_in_second[i]) > 10:
                # add or substract point
                if add:
                    coords[0] = np.insert(
                        coords[0], i + 1, (coords[1][i + 1] - shift), axis=0
                    )
                else:
                    coords[0] = np.delete(coords[0], i + 1, axis=0)
                distances_in_first = [
                    int(np.linalg.norm(coords[0][i] - coords[0][i + 1]))
                    for i in range(len(coords[0]) - 1)
                ]
                break

    return coords[0].flatten().tolist()


def interpolator(frames: list[dict], indicies: dict, annots: list):
    """
    Interpolates between two frames
    If polygons have different number of vertices, it adds or substracts vertices

        Parameters:
            frames (list[dict]): shapes grouped by frames which they are present in
    """
    offset = 1
    # iterates over grouped by frame shapes
    for i, group in enumerate(frames[:-1]):
        # check if some shapes are missing in the next frame
        cut = max(0, len(group) - len(frames[i + 1]))
        # check which shapes are missing in the next frame and remove them from the group
        # shapes are checked by treir id
        if cut > 0:
            for _ in range(cut):
                for shape in group:
                    if shape["id"] not in [x["id"] for x in frames[i + 1]]:
                        group.remove(shape)
                        break
        frames_to_interpolate = frames[i + 1][0]["frame"] - frames[i][0]["frame"]
        difference, step = [], []
        # iterates over shapes in a group
        for j, shape in enumerate(group):
            # TODO: id
            # add points to the shape if the next shape has less points
            if len(shape["points"]) < len(frames[i + 1][j]["points"]):
                shape["points"] = add_remove_point(
                    [shape["points"], frames[i + 1][j]["points"]]
                )
            # get the difference between the points of the same shape in the next group
            difference = np.subtract(frames[i + 1][j]["points"], shape["points"])
            # get the step by which the points will be interpolated
            step.append(difference / frames_to_interpolate)
        # iterates over each shape in a group
        for k in range(1, frames_to_interpolate):
            for j, shape in enumerate(group):
                points = shape["points"].copy() + (step[j] * k)
                skelet = get_skelet(shape["label"])
                skelet["points"] = list(points)
                skelet["frame"] = shape["frame"] + k
                annots[0]["shapes"].insert(
                    indicies.get(shape["frame"]) + offset, copy.deepcopy(skelet)
                )
                offset += 1
