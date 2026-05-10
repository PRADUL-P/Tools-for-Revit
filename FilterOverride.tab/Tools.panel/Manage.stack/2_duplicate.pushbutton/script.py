# -*- coding: utf-8 -*-
__title__ = "Duplicate\nFilter"
__doc__ = """Duplicate Parameter Filters:
Step 1: Pick the View/Template containing the filter.
Step 2: Pick the Filter you want to duplicate.
Step 3: Enter the New Name for the duplicate.
---
Automatically preserves all graphic overrides from the source!

_____________________________________________________________________
Version: 1.1 | Author: PRADUL P"""
__author__ = "PRADUL P"
__version__ = "1.1"

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

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

# Step 1: Select target view/template
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

# Step 2: Pick Source Filter
all_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
source_filter = forms.SelectFromList.show(
    all_filters,
    name_attr="Name",
    multiselect=False,
    title="Step 2: Pick Filter to DUPLICATE"
)
if not source_filter:
    forms.alert("Operation cancelled.")
    script.exit()

source_name = source_filter.Name

# Step 3: Name the New Filter
new_name = forms.ask_for_string(
    default=source_name + " (Copy)",
    prompt="Step 3: Enter NEW Name for the Filter:",
    title="Name Duplicate"
)
if not new_name:
    forms.alert("Operation cancelled.")
    script.exit()

# Run Operation
try:
    current_override = target_view.GetFilterOverrides(source_filter.Id)
except:
    current_override = OverrideGraphicSettings()  # fallback

t = Transaction(doc, "Duplicate Filter")
t.Start()
try:
    # Create Duplicate
    cats = source_filter.GetCategories()
    elem_filter = source_filter.GetElementFilter()
    new_filter = ParameterFilterElement.Create(doc, new_name, cats, elem_filter)

    # Apply same overrides in the current view
    target_view.SetFilterOverrides(new_filter.Id, current_override)

    # Ensure it's added to the view
    if not target_view.GetFilters().Contains(new_filter.Id):
        target_view.AddFilter(new_filter.Id)

    t.Commit()
    forms.alert("✅ Filter '{}' duplicated successfully as '{}'.".format(source_name, new_name))
except Exception as e:
    t.RollBack()
    forms.alert("❌ Error: {}".format(e))
