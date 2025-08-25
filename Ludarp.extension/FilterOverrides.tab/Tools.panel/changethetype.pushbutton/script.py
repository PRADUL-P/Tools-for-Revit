# -*- coding: utf-8 -*-
# pyRevit script: Change Filter Pattern Colors & Patterns
# Author: PRADUL

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

# Import .NET color dialog
import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import ColorDialog, DialogResult

doc = revit.doc
view = doc.ActiveView

# ---------------------------
# Collect filters in this view
# ---------------------------
filters = view.GetFilters()
filter_elems = [doc.GetElement(fid) for fid in filters]
filter_names = [f.Name for f in filter_elems]

if not filter_names:
    forms.alert("No filters applied in this view.")
    script.exit()

# ---------------------------
# Pick filters to modify
# ---------------------------
target_names = forms.SelectFromList.show(
    filter_names,
    title="Pick Filters to Modify",
    multiselect=True
)
if not target_names:
    script.exit()

target_elems = [f for f in filter_elems if f.Name in target_names]

# ---------------------------
# Choose which part(s) to change
# ---------------------------
prop_choices = forms.SelectFromList.show(
    [
        "Projection Fill Foreground",
        "Projection Fill Background",
        "Cut Fill Foreground",
        "Cut Fill Background",
        "Projection Line Color",
        "Cut Line Color"
    ],
    title="Select Override Property(ies) to Change",
    multiselect=True
)
if not prop_choices:
    script.exit()

# ---------------------------
# Use Windows Color Picker
# ---------------------------
cd = ColorDialog()
cd.AllowFullOpen = True
cd.FullOpen = True

if cd.ShowDialog() != DialogResult.OK:
    script.exit()

win_color = cd.Color
new_color = Color(win_color.R, win_color.G, win_color.B)

# ---------------------------
# Collect Fill Patterns (if needed)
# ---------------------------
pattern_map = {}
if any("Fill" in pc for pc in prop_choices):
    fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    pattern_names = [fp.Name for fp in fill_patterns]
    selected_pattern = forms.SelectFromList.show(
        pattern_names,
        title="Pick Fill Pattern",
        multiselect=False
    )
    if not selected_pattern:
        script.exit()
    pattern_elem = next(fp for fp in fill_patterns if fp.Name == selected_pattern)
    pattern_map["id"] = pattern_elem.Id

# ---------------------------
# Apply changes
# ---------------------------
t = Transaction(doc, "Change Filter Color & Pattern")
t.Start()
for f in target_elems:
    ogs = view.GetFilterOverrides(f.Id)

    # Projection fills
    if "Projection Fill Foreground" in prop_choices:
        ogs.SetSurfaceForegroundPatternColor(new_color)
        if "id" in pattern_map: 
            ogs.SetSurfaceForegroundPatternId(pattern_map["id"])

    if "Projection Fill Background" in prop_choices:
        ogs.SetSurfaceBackgroundPatternColor(new_color)
        if "id" in pattern_map: 
            ogs.SetSurfaceBackgroundPatternId(pattern_map["id"])

    # Cut fills
    if "Cut Fill Foreground" in prop_choices:
        ogs.SetCutForegroundPatternColor(new_color)
        if "id" in pattern_map: 
            ogs.SetCutForegroundPatternId(pattern_map["id"])

    if "Cut Fill Background" in prop_choices:
        ogs.SetCutBackgroundPatternColor(new_color)
        if "id" in pattern_map: 
            ogs.SetCutBackgroundPatternId(pattern_map["id"])

    # Line colors
    if "Projection Line Color" in prop_choices:
        ogs.SetProjectionLineColor(new_color)
    if "Cut Line Color" in prop_choices:
        ogs.SetCutLineColor(new_color)

    view.SetFilterOverrides(f.Id, ogs)

t.Commit()

forms.alert("Updated {} filter(s) with new color/pattern.".format(len(target_elems)), title="Done")






#### works fine with  changing the   pattern or line  at a time same colour or one by one as selcted

## can be add   differnt colur for  pattern and  lines