import tkinter as tk
import customtkinter as ctk
import numpy as np
from tkinter import filedialog
from .interpolator import Interpolator


class MainGUI:
    def __init__(self, master):
        self.master = master

        self.master.title("Lung USG Interpolator")
        self.master.geometry("900x500")
        # Create frames
        self.top_frame = tk.Frame(self.master, bg="black")
        self.top_frame.pack(expand=True)

        self.left_frame = tk.Frame(self.top_frame, bg="black")
        self.left_frame.pack(side="left", expand=True)

        self.middle_frame = tk.Frame(self.master, bg="black")
        self.middle_frame.pack(expand=True)

        self.bottom_frame = tk.Frame(self.master, bg="black")
        self.bottom_frame.pack(expand=True)

        self.state_list = None
        self.files = None
        self.output = None
        self.shapes_lst = ["lungslidingpresent", "lungslidingabsent", "aline", "bline"]

        self.createWidgets()

    def createWidgets(self):
        self.select = ctk.CTkButton(
            self.middle_frame, text="Choose File", command=self.selectFiles
        )
        self.select.pack(padx=10, side="left")

        self.output = ctk.CTkButton(
            self.middle_frame, text="Choose Output Folder", command=self.selectOutput
        )
        self.output.pack(padx=10, side="left")

        self.quit = ctk.CTkButton(
            self.middle_frame, text="Process", command=self.process
        )
        self.quit.pack(padx=10, side="left")

        self.checkboxes = [
            [
                ctk.CTkCheckBox(
                    self.bottom_frame,
                    command=self.update_box_state,
                    text="lungslidingpresent",
                ),
                ctk.CTkCheckBox(
                    self.bottom_frame,
                    command=self.update_box_state,
                    text="lungslidingabsent",
                ),
            ],
            [
                ctk.CTkCheckBox(
                    self.bottom_frame, command=self.update_box_state, text="aline"
                ),
                ctk.CTkCheckBox(
                    self.bottom_frame, command=self.update_box_state, text="bline"
                ),
            ],
        ]

        # arrange checkboxes in a grid placed at the bottom of the window
        for i, col in enumerate(self.checkboxes):
            for j, checkbox in enumerate(col):
                checkbox.grid(row=j, column=i, padx=10, pady=10)

    def selectFiles(self):
        self.files = filedialog.askopenfilenames(filetypes=[("Zip", "*.zip")])
        for i, filename in enumerate(self.files):
            tk.Label(
                self.left_frame,
                text=f"File {i+1}: " + filename.split("/")[-1],
                bg="black",
            ).pack(pady=5)

    def selectOutput(self):
        self.output_path = filedialog.askdirectory()

    def update_box_state(self):
        self.state_list = [[cb.get() for cb in col] for col in self.checkboxes]

    def process(self):
        if self.state_list is not None:
            shapes_lst = [
                x
                for i, x in enumerate(self.shapes_lst)
                if np.array(self.state_list).flatten()[i] == 1
            ]
        else:
            tk.messagebox.showerror("Error", "Please select some shapes.")
            pass
        if self.output_path is None:
            tk.messagebox.showerror("Error", "Please select an output folder.")
            pass
        if self.files is not None:
            for input_path in self.files:
                interpolator = Interpolator(input_path, self.output_path, shapes_lst)
                interpolator.interpolate()
                tk.messagebox.showinfo("Success", "Done!")
                self.master.destroy()
        else:
            tk.messagebox.showerror("Error", "Please select some files.")
            pass


# if __name__ == "__main__":
#     ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
#     # Themes: blue (default), dark-blue, green
#     ctk.set_default_color_theme("dark-blue")
#     root = ctk.CTk()
#     chooser = MultiFileSelect(root)
#     root.mainloop()
#     print(chooser.state_list)
