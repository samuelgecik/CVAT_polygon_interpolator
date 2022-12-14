from modules.utils import *
from modules.geometry import *
from modules.gui import *

shapes_lst = ["lungslidingpresent", "lungslidingabsent", "aline", "bline"]

if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
    # Themes: blue (default), dark-blue, green
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    window = MainGUI(root)
    root.mainloop()
