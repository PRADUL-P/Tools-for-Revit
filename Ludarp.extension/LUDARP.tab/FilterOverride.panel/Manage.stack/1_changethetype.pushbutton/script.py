# -*- coding: utf-8 -*-
__title__ = "Change\nColors"
__doc__ = """Bulk Update Filter Graphics:
Step 1: Pick the TARGET View or Template.
Step 2: Select the Filter(s) you want to change.
Step 3: Choose which properties to override (Fills or Lines).
Step 4: Pick a New Color (Windows Color Picker).
Step 5: Pick a New Fill Pattern (if Fills were selected).

_____________________________________________________________________
Version: 1.1 | Author: PRADUL P"""
__author__ = "PRADUL P"
__version__ = "1.1"

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

# Import .NET color dialog
import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import ColorDialog, DialogResult

doc = revit.doc

from collections import OrderedDict

# ---------------------------
# UI Helpers for View Selection
# ---------------------------
valid_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation, 
    ViewType.ThreeD, ViewType.Section, ViewType.Detail, 
    ViewType.EngineeringPlan, ViewType.AreaPlan
]

class ViewItem:
    def __init__(self, view):
        self.view = view
        self.Id = view.Id
        if view.IsTemplate:
            self.Name = "   🎨 [Template] " + view.Name
        else:
            self.Name = "   📄 [" + str(view.ViewType).replace("ViewType.", "").replace("ThreeD", "3D") + "] " + view.Name

class SeparatorItem:
    def __init__(self, title):
        self.Name = "💠 " + title.upper() + " 💠"
        self.view = None
        self.Id = None

def build_view_dict(all_views, exclude_id=None):
    all_valid = []
    templates = []
    by_type = {}
    for v in all_views:
        if exclude_id and v.Id == exclude_id: continue
        if v.IsTemplate:
            item = ViewItem(v)
            templates.append(item)
        elif v.ViewType in valid_types:
            item = ViewItem(v)
            cat_name = "📁 " + str(v.ViewType).replace("ViewType.", "").replace("ThreeD", "3D") + "s"
            if cat_name not in by_type: by_type[cat_name] = []
            by_type[cat_name].append(item)
    templates.sort(key=lambda x: x.Name)
    for cat in by_type: by_type[cat].sort(key=lambda x: x.Name)
    if templates:
        all_valid.append(SeparatorItem("VIEW TEMPLATES"))
        all_valid.extend(templates)
    for cat in sorted(by_type.keys()):
        if by_type[cat]:
            all_valid.append(SeparatorItem(cat.replace("📁 ", "")))
            all_valid.extend(by_type[cat])
    d = OrderedDict()
    d[" 🌍 ALL VIEWS & TEMPLATES"] = all_valid
    d["⭐ VIEW TEMPLATES"] = templates
    for cat in sorted(by_type.keys()): d[cat] = by_type[cat]
    return d

# ---------------- MAIN ---------------- #

# Step 1: Pick Target View/Template
all_views = FilteredElementCollector(doc).OfClass(View)
target_option = forms.SelectFromList.show(
    build_view_dict(all_views),
    name_attr="Name",
    multiselect=False,
    title="Step 1: Pick TARGET View or Template"
)
if not target_option or target_option.view is None:
    forms.alert("Operation cancelled.")
    script.exit()
target_view = target_option.view

# Step 2: Pick Filters to Modify
filters = target_view.GetFilters()
filter_elems = [doc.GetElement(fid) for fid in filters]
filter_names = [f.Name for f in filter_elems]

if not filter_names:
    forms.alert("No filters applied in the selected view/template.")
    script.exit()

target_names = forms.SelectFromList.show(
    filter_names,
    title="Step 2: Pick Filter(s) to Modify",
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
    ogs = target_view.GetFilterOverrides(f.Id)

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

    target_view.SetFilterOverrides(f.Id, ogs)

t.Commit()
forms.alert("Updated {} filter(s) in '{}' with new color/pattern.".format(len(target_elems), target_view.Name), title="Done")
