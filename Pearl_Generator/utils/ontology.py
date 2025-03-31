import tkinter as tk
import tkinter.ttk as t
from owlready2 import *

# Load the ontology file
onto = get_ontology("extended_mara_with_poi.owl").load()

# Function to expand or collapse the subclasses
def expand_collapse(event):
    item_id = tree.focus()
    children = tree.get_children(item_id)
    if children:
        tree.delete(children)
    else:
        class_name = tree.item(item_id)['text']
        cls = onto[class_name]
        for subclass in cls.subclasses():
            tree.insert(item_id, 'end', text=subclass.name)

# Create the GUI window
window = tk.Tk()
window.title("Ontology Navigator")

# Create the treeview widget
tree = t.Treeview(window)
tree.pack()

# Add the root classes to the treeview
for cls in onto.classes():
    if not cls.is_a:
        tree.insert('', 'end', text=cls.name)

# Bind the expand_collapse function to the double-click event
tree.bind("<Double-1>", expand_collapse)

# Start the GUI event loop
window.mainloop()