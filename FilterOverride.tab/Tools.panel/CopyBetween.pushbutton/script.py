# -*- coding: utf-8 -*-
__title__ = "Copy Between\nViews"
__doc__ = """Copy Filters and Overrides:
Step 1: Pick the SOURCE View or Template.
Step 2: Select one or more TARGET Views or Templates.
Step 3: Choose exactly which filters to copy.
---
Features:
- Adds missing filters to targets.
- Synchronizes colors, lines, and patterns.
- Retains visibility states.

_____________________________________________________________________
Version: 1.1 | Author: PRADUL P"""
__author__ = "PRADUL P"
__version__ = "1.1"

from Autodesk.Revit.DB import *
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document


def copy_filters_between_views(source_view, target_views, filter_ids):
    """Copy selected filters with overrides from one view/template to others"""
    t = Transaction(doc, "Copy Filters with Overrides")
    t.Start()
    for target_view in target_views:
        for fid in filter_ids:
            # Add filter if target view doesn't already have it
            if not target_view.GetFilters().Contains(fid):
                target_view.AddFilter(fid)
            # Copy overrides
            overrides = source_view.GetFilterOverrides(fid)
            target_view.SetFilterOverrides(fid, overrides)

            # Try to copy visibility state if available
            if hasattr(source_view, "GetFilterVisibility") and hasattr(target_view, "SetFilterVisibility"):
                try:
                    vis_state = source_view.GetFilterVisibility(fid)
                    target_view.SetFilterVisibility(fid, vis_state)
                except Exception:
                    pass
    t.Commit()


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
        # Creates a visually distinct header row
        self.Name = "💠 " + title.upper() + " 💠"
        self.view = None
        self.Id = None

def build_view_dict(all_views, exclude_id=None):
    all_valid = []
    templates = []
    by_type = {}
    
    for v in all_views:
        if exclude_id and v.Id == exclude_id:
            continue
        if v.IsTemplate:
            item = ViewItem(v)
            templates.append(item)
        elif v.ViewType in valid_types:
            item = ViewItem(v)
            cat_name = "📁 " + str(v.ViewType).replace("ViewType.", "").replace("ThreeD", "3D") + "s"
            if cat_name not in by_type:
                by_type[cat_name] = []
            by_type[cat_name].append(item)
            
    # Sort everything alphabetically
    templates.sort(key=lambda x: x.Name)
    for cat in by_type:
        by_type[cat].sort(key=lambda x: x.Name)
        
    # Build the "All Views" list with separators!
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
    for cat in sorted(by_type.keys()):
        d[cat] = by_type[cat]
    return d

# ---------------- MAIN ---------------- #
# collect all views (normal + templates)
all_views = FilteredElementCollector(doc).OfClass(View)

# Step 1: Pick Source View/Template
source_option = forms.SelectFromList.show(
    build_view_dict(all_views), 
    name_attr="Name", 
    multiselect=False, 
    title="Step 1: Pick SOURCE View/Template"
)
if not source_option or source_option.view is None:
    forms.alert("Operation cancelled.")
    script.exit()
source_view = source_option.view

# Step 2: Pick Target View(s)/Template(s)
target_options = forms.SelectFromList.show(
    build_view_dict(all_views, exclude_id=source_view.Id),
    name_attr="Name",
    multiselect=True,
    title="Step 2: Pick TARGET View(s)/Template(s)"
)
if not target_options:
    forms.alert("Operation cancelled.")
    script.exit()
target_views = [opt.view for opt in target_options if opt.view is not None]

if not target_views:
    forms.alert("No valid target view/template selected.")
    script.exit()

# Step 3: Pick Filters to Copy
filters_in_source = [doc.GetElement(fid) for fid in source_view.GetFilters()]
if not filters_in_source:
    forms.alert("No filters found in source view/template.")
    script.exit()

filters_to_copy = forms.SelectFromList.show(
    filters_in_source, 
    name_attr="Name", 
    multiselect=True, 
    title="Step 3: Pick Filters to Copy"
)
if not filters_to_copy:
    forms.alert("No filters selected.")
    script.exit()

# Run Copy Operation
copy_filters_between_views(source_view, target_views, [f.Id for f in filters_to_copy])

forms.alert("Success! Copied {} filter(s) from '{}' to {} target(s).".format(
    len(filters_to_copy), source_view.Name, len(target_views)))
