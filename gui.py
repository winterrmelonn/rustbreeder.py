import tkinter as tk
from tkinter import ttk

from rustbreeder import score

VALID_GENES = set("GYHXW")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rustbreeder")
        self.plants = []

        entry_row = ttk.Frame(self, padding=10)
        entry_row.pack(fill="x")
        ttk.Label(entry_row, text="Plant genes (6 letters, GYHXW):").pack(side="left")
        self.gene_entry = ttk.Entry(entry_row, width=10)
        self.gene_entry.pack(side="left", padx=5)
        self.gene_entry.bind("<Return>", lambda e: self.add_plant())
        ttk.Button(entry_row, text="Add", command=self.add_plant).pack(side="left")

        self.error_label = ttk.Label(self, foreground="red")
        self.error_label.pack(fill="x", padx=10)

        self.tree = ttk.Treeview(self, columns=("score",), show="headings tree", height=10)
        self.tree.heading("#0", text="Genes")
        self.tree.heading("score", text="Score")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.best_label = ttk.Label(self, font=("", 10, "bold"))
        self.best_label.pack(fill="x", padx=10, pady=(0, 10))

    def add_plant(self):
        genes = self.gene_entry.get().upper()
        if len(genes) != 6 or any(g not in VALID_GENES for g in genes):
            self.error_label.config(text="Invalid gene: need exactly 6 letters from G/Y/H/X/W.")
            return
        self.error_label.config(text="")
        self.gene_entry.delete(0, "end")
        self.plants.append(genes)
        self.tree.insert("", "end", text=genes, values=(score(genes),))
        best = max(self.plants, key=score)
        self.best_label.config(text=f"Best plant: {best} (score {score(best)})")


if __name__ == "__main__":
    App().mainloop()
