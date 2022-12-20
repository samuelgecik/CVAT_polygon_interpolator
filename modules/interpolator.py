from .file_utils import *
from .utils import *


class Interpolator:
    def __init__(self, input_path, output_path, shapes_lst):
        self.input_path = input_path
        self.output_path = output_path
        self.shapes_lst = shapes_lst
        self.annots = get_annots_file(self.input_path)

    def interpolate(self):
        annots_duplicates_removal(self.annots[0]["shapes"])
        shapes = copy.deepcopy(self.annots[0]["shapes"])
        filtered_shapes = filter_shapes(shapes, self.shapes_lst)
        indicies = get_indicies(shapes)
        shapes_by_frame = group_shapes_by_frame(filtered_shapes)
        assign_id(shapes_by_frame)
        interpolator(shapes_by_frame, indicies, self.annots)
        save_zip(self.input_path, self.output_path, self.annots)
