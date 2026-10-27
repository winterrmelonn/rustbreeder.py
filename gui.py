# ============================================================================
# gui.py — THE WINDOW
#
# The top layer. It owns no breeding or planning logic at all; it collects
# genomes from you, hands them to layout.py, and draws whatever comes back.
# If you ever find yourself writing genetics rules in this file, they belong
# in rustbreeder.py instead.
#
# Project map:
#   rustbreeder.py  <- breeding rules + scoring
#   layout.py       <- where to plant / multi-generation plans
#   gui.py          <- you are here (the window)
#
# tkinter crash course (Python's built-in GUI toolkit, no install needed):
#   - A "widget" is any UI piece: a window, button, label, text box.
#   - Every widget is created with its PARENT as the first argument, which
#     builds a tree: window -> frame -> button.
#   - A widget doesn't appear until you call a geometry manager on it. We use
#     two: .pack() stacks things in order, .grid(row=, column=) places things
#     in a table. Never mix the two inside the SAME parent frame.
#   - ttk widgets are the themed/modern versions of the plain tk ones.
# ============================================================================

import tkinter as tk
from tkinter import ttk

from rustbreeder import score
from layout import best_layout

VALID_GENES = set("GYHXW")  # a set, because `in` checks on sets are instant

# Good genes (GYH) read green, bad genes (WX) read red — same visual language the game uses.
GENE_COLORS = {
    "G": "#3d9970",  # Growth
    "Y": "#7fb800",  # Yield
    "H": "#2e8b8b",  # Hardiness
    "W": "#d64545",  # Water
    "X": "#8b3a3a",  # Empty
}

# The colour palette, named once here so the whole window stays consistent and
# a redesign means editing five lines instead of hunting through the file.
BG = "#22252a"      # window background
PANEL = "#2b2f36"   # raised surfaces: grid cells, the entry box
TEXT = "#e6e6e6"    # normal text
MUTED = "#8b929c"   # secondary text: headers, scores
ACCENT = "#3d9970"  # buttons (matches the Growth tile green)
MONO = ("Menlo", 11, "bold")  # monospace, so all six gene tiles are equal width


def gene_tiles(parent, genome, bg=BG):
    """Build a row of six small coloured squares, one per gene.

    Returns the frame WITHOUT packing it, so the caller decides where it goes.
    This is the single most reused piece of the UI — the plant list and both
    result grids all draw genomes through this one function, which is why they
    all look identical.
    """
    row = tk.Frame(parent, bg=bg)
    for gene in genome:
        tk.Label(
            row, text=gene, width=2, bg=GENE_COLORS[gene], fg="white", font=MONO,
        ).pack(side="left", padx=1)
    return row


# Subclassing tk.Tk means "this class IS the window". Anywhere you'd pass the
# window as a parent, you pass `self`.
class App(tk.Tk):
    def __init__(self):
        super().__init__()          # build the actual window first
        self.title("rustbreeder")
        self.configure(bg=BG)
        self.plants = []            # every genome you've entered; the app's only real state
        self._init_styles()
        self.cell_w, self.cell_h = self._measure_cell()

        # --- gene entry row ---
        entry_row = ttk.Frame(self, padding=(16, 14, 16, 8))
        entry_row.pack(fill="x")    # fill="x" = stretch across the window's width
        ttk.Label(entry_row, text="PLANT GENES", style="Header.TLabel").pack(side="left")
        self.gene_entry = ttk.Entry(entry_row, width=10, font=MONO, justify="center")
        self.gene_entry.pack(side="left", padx=10)
        # bind() connects an event to a function. "<Return>" is the Enter key, so
        # you can type a genome and hit Enter instead of reaching for the button.
        # The lambda swallows the event object tkinter passes, which add_plant doesn't want.
        self.gene_entry.bind("<Return>", lambda e: self.add_plant())
        # command= takes the function ITSELF (no parentheses). Writing
        # command=self.add_plant() would call it immediately at startup and pass
        # the result — a classic mistake.
        ttk.Button(entry_row, text="Add", style="Accent.TButton", command=self.add_plant).pack(side="left")
        ttk.Label(entry_row, text="6 letters · G Y H X W", style="Muted.TLabel").pack(side="left", padx=10)

        # Stays empty until something goes wrong; validation messages appear here.
        self.error_label = ttk.Label(self, style="Error.TLabel")
        self.error_label.pack(fill="x", padx=16)

        # --- the list of plants you've entered ---
        ttk.Label(self, text="YOUR PLANTS", style="Header.TLabel").pack(anchor="w", padx=16, pady=(10, 4))
        self.list_frame = tk.Frame(self, bg=BG)   # rows get built inside here by _refresh_list
        self.list_frame.pack(fill="x", padx=16)

        self.best_label = ttk.Label(self, style="Best.TLabel")
        self.best_label.pack(anchor="w", padx=16, pady=(8, 12))

        ttk.Button(self, text="Finalize layout", style="Accent.TButton", command=self.finalize).pack(padx=16)
        self.total_label = ttk.Label(self, style="Best.TLabel")
        self.total_label.pack(pady=(10, 0))

        # --- the two result grids, side by side ---
        # PLANT HERE shows what to put in each slot; RESULTS shows what it breeds.
        grids = ttk.Frame(self, padding=(16, 10, 16, 16))
        grids.pack()
        self.plant_grid = self._titled_grid(grids, "PLANT HERE")
        self.result_grid = self._titled_grid(grids, "RESULTS")

    def _init_styles(self):
        """Define every named style once, so widgets stay consistent.

        ttk styles work like CSS classes: configure a name here, then pass
        style="ThatName" when creating a widget.
        """
        style = ttk.Style()
        # THE KEY LINE. macOS's native 'aqua' theme draws buttons and entries
        # with system artwork and SILENTLY IGNORES custom colours — your
        # background setting simply does nothing. 'clam' is a plain theme that
        # honours them. Without this one line, none of the colours below apply.
        style.theme_use("clam")

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Header.TLabel", foreground=MUTED, font=("", 10, "bold"))
        style.configure("Muted.TLabel", foreground=MUTED, font=("", 10))
        style.configure("Best.TLabel", foreground=TEXT, font=("", 12, "bold"))
        style.configure("Error.TLabel", foreground="#e06c6c", font=("", 10))
        style.configure(
            "TEntry", fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT,
            borderwidth=0, padding=6,
        )
        style.configure(
            "Accent.TButton", background=ACCENT, foreground="white",
            borderwidth=0, padding=(16, 7), font=("", 11, "bold"),
        )
        # style.map sets colours for interactive STATES rather than the resting
        # look — here, hover ("active") and click ("pressed").
        style.map("Accent.TButton", background=[("active", "#4cb88d"), ("pressed", "#33805d")])
        style.configure(
            "Small.TButton", background=PANEL, foreground=MUTED,
            borderwidth=0, padding=(8, 2), font=("", 9),
        )
        style.map("Small.TButton", background=[("active", "#3a3f47")], foreground=[("active", TEXT)])

    def _measure_cell(self):
        """Work out how big a grid cell must be by MEASURING a real tile row.

        This used to be a hardcoded 150x62 and the sixth gene got clipped off,
        because six tiles actually need 176px. Rather than guess a new number
        (which would break again the moment the font changed), build a throwaway
        tile row, ask tkinter how big it wants to be, and destroy it.

        update_idletasks() forces tkinter to do its pending layout maths now, so
        winfo_reqwidth() returns a real answer instead of zero.
        """
        probe = gene_tiles(self, "GGGGGG")
        probe.update_idletasks()
        width, height = probe.winfo_reqwidth(), probe.winfo_reqheight()
        probe.destroy()
        return width + 20, height + 34  # padding, plus room for the score line

    def _titled_grid(self, parent, title):
        """A heading with an empty 3x3 area underneath.

        Returns the inner frame that cells get added to, so finalize() can fill
        PLANT HERE and RESULTS without caring how either was built.
        """
        column = ttk.Frame(parent)
        column.pack(side="left", padx=12)   # side="left" is what puts the grids side by side
        ttk.Label(column, text=title, style="Header.TLabel").pack(pady=(0, 8))
        grid = tk.Frame(column, bg=BG)
        grid.pack()
        return grid

    def add_plant(self):
        """Validate what's typed in the box and add it to the list."""
        genes = self.gene_entry.get().upper()    # .upper() so lowercase typing works
        # any() is True if ANY letter is invalid — so this rejects wrong length
        # or any letter outside G/Y/H/X/W.
        if len(genes) != 6 or any(g not in VALID_GENES for g in genes):
            self.error_label.config(text="Invalid gene: need exactly 6 letters from G/Y/H/X/W.")
            return                                # bail out, don't add it
        self.error_label.config(text="")          # clear any previous error
        self.gene_entry.delete(0, "end")          # empty the box, ready for the next one
        self.plants.append(genes)
        self._refresh_list()

    def remove_plant(self, index):
        del self.plants[index]
        self._refresh_list()

    def edit_plant(self, index):
        """Pull a plant back into the entry box to retype it.

        'Editing' is really remove-then-retype: .pop(index) removes it from the
        list AND hands it back, so it can be dropped into the entry box.
        """
        self.gene_entry.delete(0, "end")
        self.gene_entry.insert(0, self.plants.pop(index))
        self.gene_entry.focus_set()               # put the cursor there, ready to type
        self._refresh_list()

    def _refresh_list(self):
        """Destroy and rebuild the whole plant list from self.plants.

        Rebuilding everything looks wasteful, but it means there's exactly ONE
        piece of code that turns self.plants into rows. Updating rows in place
        would need index bookkeeping that drifts out of sync after every remove.
        With at most a handful of plants, the rebuild is free.
        """
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for index, genome in enumerate(self.plants):
            row = tk.Frame(self.list_frame, bg=BG)
            row.pack(anchor="w", pady=2)          # anchor="w" = left-align (west)
            gene_tiles(row, genome).pack(side="left")
            tk.Label(row, text=f"score {score(genome)}", bg=BG, fg=MUTED, font=("", 10)).pack(side="left", padx=10)

            # THE `i=index` IS NOT A TYPO — it's working around a real Python trap.
            # A lambda looks up variables when it RUNS, not when it's created. All
            # these lambdas would therefore share the final value of `index`, and
            # every button would delete the last row. Writing i=index captures the
            # value NOW, as a default argument, giving each button its own copy.
            ttk.Button(row, text="edit", style="Small.TButton",
                       command=lambda i=index: self.edit_plant(i)).pack(side="left", padx=2)
            ttk.Button(row, text="✕", style="Small.TButton",
                       command=lambda i=index: self.remove_plant(i)).pack(side="left", padx=2)

        if self.plants:
            # max(..., key=score) returns the genome with the highest score.
            best = max(self.plants, key=score)
            self.best_label.config(text=f"Best plant: {best}  ·  score {score(best)}")
        else:
            self.best_label.config(text="")       # list is empty, show nothing

    def finalize(self):
        """Hand the plants to the planner and draw the two result grids.

        This is the only place the two halves of the project meet: everything
        above is UI, everything inside best_layout() is the search in layout.py.
        """
        if not self.plants:
            self.error_label.config(text="Add at least one plant before finalizing.")
            return
        self.error_label.config(text="")

        # The whole computation, in one line. Used to take 15 seconds and freeze
        # the window; now runs in about a tenth of a second.
        assignment, offspring, fitness = best_layout(self.plants)
        self.total_label.config(text=f"Total score {fitness}")

        # Clear both grids before redrawing, or pressing Finalize twice would
        # stack new cells on top of the old ones.
        for grid in (self.plant_grid, self.result_grid):
            for widget in grid.winfo_children():
                widget.destroy()

        # Walk all 9 positions, filling the matching cell in BOTH grids so the
        # two line up square for square.
        for row in range(3):
            for col in range(3):
                plant_cell = self._cell(self.plant_grid, row, col)
                result_cell = self._cell(self.result_grid, row, col)
                if (row, col) not in assignment:
                    self._empty(plant_cell)       # you don't hold enough seeds for this slot
                    self._empty(result_cell)
                    continue
                gene_tiles(plant_cell, assignment[(row, col)], bg=PANEL).pack(expand=True)
                gene_tiles(result_cell, offspring[(row, col)], bg=PANEL).pack(pady=(8, 0))
                tk.Label(
                    result_cell, text=f"score {score(offspring[(row, col)])}",
                    bg=PANEL, fg=MUTED, font=("", 9),
                ).pack(pady=(3, 0))

    def _cell(self, grid, row, col):
        """One fixed-size square of a 3x3 grid."""
        cell = tk.Frame(grid, bg=PANEL, width=self.cell_w, height=self.cell_h)
        cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
        # By default a frame SHRINKS to fit its contents, which would make empty
        # cells tiny and leave the grid ragged. pack_propagate(False) tells it to
        # keep the width/height set above no matter what's inside.
        cell.pack_propagate(False)
        return cell

    def _empty(self, cell):
        """Placeholder for a planter slot with nothing in it."""
        tk.Label(cell, text="—", bg=PANEL, fg="#555b63", font=("", 12)).pack(expand=True)


# Same guard as the other files: only open a window when this file is RUN,
# never when it's imported.
if __name__ == "__main__":
    App().mainloop()   # mainloop() hands control to tkinter — it waits for clicks
                       # and keystrokes forever, and only returns when you close
                       # the window. Nothing after this line runs until then.
