import numpy as np
import copy
import tempfile
import zipfile
import shutil
import os
from .geometry import *

np.seterr(all="raise")


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
    frame = filtered_shapes[0]["frame"]
    shapes_by_frame = []
    shapes_in_single_frame = []
    for shape in filtered_shapes:
        if shape["frame"] == frame:
            shapes_in_single_frame.append(shape)
        else:
            frame = shape["frame"]
            shapes_by_frame.append(shapes_in_single_frame)
            shapes_in_single_frame = []
            shapes_in_single_frame.append(shape)
    shapes_by_frame.append(shapes_in_single_frame)
    return shapes_by_frame


def remove_duplicates(shapes_by_frame: list[list]):
    """
    Removes duplicate shapes on the same frame
    """
    # remove duplicate shapes in the same frame
    for frame in shapes_by_frame:
        if len(frame) == 1:
            continue
        i = 0
        # find if two polygons intersect by comparing each other
        while i < len(frame):
            j = i + 1
            while j < len(frame):
                if intersect(
                    chunks(frame[i]["points"], 2), chunks(frame[j]["points"], 2)
                ):
                    # remove one of the polygons
                    frame.pop(j)
                j += 1
            i += 1


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
            # if same label and square intersect and frame difference < 10: then same id else: new id
            for prev_shape in shapes_by_frame[i - 1]:
                if (
                    shape["label"] == prev_shape["label"]
                    and (shape["frame"] - prev_shape["frame"]) <= 10
                    and intersect(
                        find_extrema_rectangle(chunks(shape["points"], 2)),
                        find_extrema_rectangle(chunks(prev_shape["points"], 2)),
                    )
                ):
                    shape["id"] = prev_shape["id"]
                    break
            else:
                shape["id"] = id_count
                id_count += 1


def align_points(shapes_by_frame: list[list]):
    """
    Aligns points of the shapes in the list of shapes grouped by frame
    """
    for i, frame in enumerate(shapes_by_frame[:-1]):
        for shape in frame:
            if shape["frame"] == 560:
                print("debug")
                print(shape)
            # check if the shape with the same id is present in the next frame
            if shape["id"] not in [x["id"] for x in shapes_by_frame[i + 1]]:
                continue
            next_shape = [x for x in shapes_by_frame[i + 1] if x["id"] == shape["id"]][
                0
            ]
            points = np.array(chunks(shape["points"], 2))
            next_points = np.array(chunks(next_shape["points"], 2))
            magnitudes = get_magnitudes(points)
            upper_left = min(magnitudes)
            magnitudes_in_next = get_magnitudes(next_points)
            upper_left_in_next = min(magnitudes_in_next)
            # start polygons from the most upper left point
            if magnitudes.index(upper_left) != 0:
                points = np.roll(points, -magnitudes.index(upper_left), axis=0)
            if magnitudes_in_next.index(upper_left_in_next) != 0:
                next_points = np.roll(
                    next_points, -magnitudes_in_next.index(upper_left_in_next), axis=0
                )
            # compare the direction of labeling by checking second points
            if (abs(points[1] - next_points[1]) > 100).any():
                # flip the points of the first shape
                points[1:] = np.flip(points[1:], axis=0)
                points = np.roll(
                    points, -(-magnitudes_in_next.index(upper_left_in_next)), axis=0
                )
                shape["points"] = points.flatten().tolist()


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
        magnitudes = get_magnitudes(coords[i])
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
        # check which shapes are missing in the next frame and remove them from the group
        # shapes are checked by treir id
        for shape in group:
            if shape["id"] not in [x["id"] for x in frames[i + 1]]:
                group.remove(shape)
        if len(group) == 0:
            continue
        frames_to_interpolate = frames[i + 1][0]["frame"] - frames[i][0]["frame"]
        step = {}
        # iterates over shapes in a group
        for j, shape in enumerate(group):
            # get shape from the next frame with the same id
            for next_shape in frames[i + 1]:
                if shape["id"] == next_shape["id"]:
                    break
            # add points to the shape if the next shape has less points
            if len(shape["points"]) < len(next_shape["points"]):
                shape["points"] = add_remove_point(
                    [shape["points"], next_shape["points"]]
                )
            # get the difference between the points of the same shape in the next group
            difference = np.subtract(next_shape["points"], shape["points"])
            # get the step by which the points will be interpolated
            step[next_shape["id"]] = difference / frames_to_interpolate
        # iterates over each shape in a group
        for k in range(1, frames_to_interpolate):
            for j, shape in enumerate(group):
                points = shape["points"].copy() + (step[shape["id"]] * k)
                skelet = get_skelet(shape["label"])
                skelet["points"] = list(points)
                skelet["frame"] = shape["frame"] + k
                annots[0]["shapes"].insert(
                    indicies.get(shape["frame"]) + offset, copy.deepcopy(skelet)
                )
                offset += 1


def remove_from_zip(zipfname, *filenames):
    tempdir = tempfile.mkdtemp()
    try:
        tempname = os.path.join(tempdir, "new.zip")
        with zipfile.ZipFile(zipfname, "r") as zipread:
            with zipfile.ZipFile(tempname, "w") as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in filenames:
                        data = zipread.read(item.filename)
                        zipwrite.writestr(item, data)
        shutil.move(tempname, zipfname)
    finally:
        shutil.rmtree(tempdir)
