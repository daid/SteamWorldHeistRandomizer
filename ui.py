import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import main as mainmodule
import os
import random
import base64


class MainUI:
    def __init__(self):
        self.__root = tk.Tk()
        self.__root.title("Steamworld Heist Randomizer")
        self.__root.resizable(False, False)
        self.__tooltip = None
        self.__install_path = tk.StringVar(value=mainmodule.find_game())
        self.__seed = tk.StringVar()
        self.random_seed()
        self.__options = {}

        self.__row = 0

        self.__frame = ttk.Frame(self.__root, padding="12 12 12 12")
        self.__frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        ttk.Label(self.__frame, text="Install path:", anchor=tk.E).grid(column=0, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        subframe = ttk.Frame(self.__frame)
        subframe.grid(column=1, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Entry(subframe, textvariable=self.__install_path).grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Button(subframe, text="Browse", command=self.browse_install_path).grid(column=1, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.__row += 1

        ttk.Label(self.__frame, text="Seed:", anchor=tk.E).grid(column=0, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        subframe = ttk.Frame(self.__frame)
        subframe.grid(column=1, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Entry(subframe, textvariable=self.__seed).grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Button(subframe, text="Random", command=self.random_seed).grid(column=1, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.__row += 1

        self.__addOption("stripquests", "Remove quests", default=True, help_text="""
Removes most of the story related elements that
require you to visit bars and other locations.
Also removes the dialogs from your crew after 
you finished certain missions.""")
        self.__addOption("charweapon", "Character weapon options", ["default", "basic", "wild"], default="basic", help_text="""
Sets which weapon classes crew can use.
Default: Normal, not randomized.
Basic: Always ensure basic handguns can
\tbe used by everyone
Wild: Completely random. Gives one or two
\trandom weapon classes""")
        self.__addOption("charlevelup", "Character level up rewards", ["default", "basic", "wild"], default="basic", help_text="""
Randomizes the upgrades that crew get on level up.
Default: No randomization.
Basic: Distributes one main chained upgrade path per crew member
\tFills other upgrade slots with basic entries.
Wild: Anything goes. No guarantees that upgrade paths are complete.
\tCould give you many different upgrade chains unfinished.""")

        subframe = ttk.Frame(self.__frame)
        subframe.grid(column=1, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Button(subframe, text="Randomize!", command=self.randomize).grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        ttk.Button(subframe, text="Remove randomization", command=self.clean).grid(column=1, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    def __addOption(self, key, label, options=None, *, default=None, help_text=None):
        if options is not None:
            if default is None:
                assert default in options
                default = options[0]
            self.__options[key] = tk.StringVar(value=default)
            ttk.Label(self.__frame, text=label, anchor=tk.E).grid(column=0, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
            ctrl = ttk.Combobox(self.__frame, textvariable=self.__options[key], values=options, state=["readonly"])
            ctrl.grid(column=1, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        else:
            if default is None:
                default = False
            self.__options[key] = tk.BooleanVar(value=default)
            ttk.Label(self.__frame, text=label, anchor=tk.E).grid(column=0, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
            ctrl = ttk.Checkbutton(self.__frame, variable=self.__options[key], onvalue=True, offvalue=False)
            ctrl.grid(column=1, row=self.__row, sticky=(tk.N, tk.W, tk.E, tk.S))
        if help_text:
            ctrl.bind('<Enter>', lambda e: self.show_tooltip(help_text, ctrl))
            ctrl.bind('<Leave>', lambda e: self.hide_tooltip())
        self.__row += 1

    def show_tooltip(self, text, ctrl):
        self.hide_tooltip()
        self.__tooltip = tk.Toplevel()
        self.__tooltip.overrideredirect(1)
        self.__tooltip.attributes("-topmost", 1)
        x = int(self.__root.geometry().split("+")[1])
        y = int(self.__root.geometry().split("+")[2])
        x += int(ctrl.winfo_geometry().split("+")[1])
        y += int(ctrl.winfo_geometry().split("+")[2])
        self.__tooltip.geometry("+%d+%d" % (ctrl.winfo_rootx(), ctrl.winfo_rooty() + ctrl.winfo_height()))
        label = tk.Label(self.__tooltip, text=text.strip(), justify=tk.LEFT)
        label.configure(bg="#ffff80")
        label.pack()

    def hide_tooltip(self):
        if self.__tooltip:
            self.__tooltip.destroy()
            self.__tooltip = None

    def run(self):
        self.__root.mainloop()

    def randomize(self):
        args = [self.__install_path.get()]
        if self.__seed.get():
            args += ["--seed", self.__seed.get()]
        for key, value in self.__options.items():
            if isinstance(value, tk.StringVar):
                args.append("--%s" % (key))
                args.append(value.get())
            if isinstance(value, tk.BooleanVar):
                if value.get():
                    args.append("--%s" % (key))
        mainmodule.main(args)
        messagebox.showinfo("Steamworld Heist Randomizer", "Randomization complete.\nBest start a new save!")

    def clean(self):
        mainmodule.main([self.__install_path.get(), "--clean"])
        messagebox.showinfo("Steamworld Heist Randomizer", "Randomization removed,\nvanilla game can be played.")

    def browse_install_path(self):
        exename = "Heist"
        if sys.platform == "win32":
            exename += ".exe"
        filename = filedialog.askopenfilename(initialdir=self.__install_path.get(), initialfile=exename, filetypes=[("Executable", exename)])
        if filename is None:
            return
        self.__install_path.set(os.path.dirname(filename))

    def random_seed(self):
        self.__seed.set(base64.b64encode(random.randbytes(9), b"@*"))


if __name__ == '__main__':
    import sys

    if sys.platform == "win32":
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    MainUI().run()
