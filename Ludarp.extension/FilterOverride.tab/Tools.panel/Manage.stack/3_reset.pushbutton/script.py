# -*- coding: utf-8 -*-
__title__ = "Reset\nFilters"
__doc__ = """Remove Filter Overrides:
Step 1: Pick the View or Template to clean.
Step 2: Select the Filter(s) you want to reset.
---
This will clear all colors, lines, and patterns, returning the filter to its default appearance.

_____________________________________________________________________
Version: 1.1 | Author: PRADUL P"""
__author__ = "PRADUL P"
__version__ = "1.1"

from Autodesk.Revit.DB import *
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document

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

# Step 2: Pick Filter(s) to Reset
filters = target_view.GetFilters()
filter_elems = [doc.GetElement(fid) for fid in filters]
filter_names = [f.Name for f in filter_elems]

if not filter_names:
    forms.alert("No filters applied in the selected view/template.")
    script.exit()

target_names = forms.SelectFromList.show(
    filter_names,
    title="Step 2: Pick Filter(s) to RESET",
    multiselect=True
)
if not target_names:
    script.exit()

# ---------------------------
# Helper functions
# ---------------------------
def reset_filter_overrides(view, filter_ids):
    """Reset overrides for selected filters in a view"""
    default_ogs = OverrideGraphicSettings()
    t = Transaction(doc, "Reset Filter Overrides")
    t.Start()
    for fid in filter_ids:
        try:
            view.SetFilterOverrides(fid, default_ogs)
        except:
            pass
    t.Commit()

def pick_filters(view, msg="Pick Filters to Reset"):
    """Helper function: Pick filters from a view"""
    filters_in_view = [doc.GetElement(fid) for fid in view.GetFilters()]
    if not filters_in_view:
        forms.alert("No filters found in the selected view/template.", exitscript=True)
    return forms.SelectFromList.show(filters_in_view, name_attr="Name", multiselect=True, title=msg)

# ---------------- MAIN ---------------- #
filters_to_reset = pick_filters(target_view, msg="Pick Filters to Reset")
if filters_to_reset:
    reset_filter_overrides(target_view, [f.Id for f in filters_to_reset])
    forms.alert("Reset overrides for {} filter(s) in '{}'.".format(
        len(filters_to_reset), target_view.Name
    ))
