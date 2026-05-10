# -*- coding: utf-8 -*-
"""
🔄 LUDARP Filter Override: Copy Between Views
Version: 1.2 | Author: PRADUL P

This script allows users to synchronize Revit Filter Overrides between multiple 
views and templates. It handles the identification of filters, copying of graphic 
overrides (colors, lines, patterns), and preservation of visibility states.
"""
__title__ = "Copy Between\nViews"
__author__ = "PRADUL P"
__version__ = "1.2"

from Autodesk.Revit.DB import *
from pyrevit import forms, script
from collections import OrderedDict

# Initialize the document
doc = __revit__.ActiveUIDocument.Document

# ---------------------------------------------------------------------------------
# CORE LOGIC: COPY OPERATION
# ---------------------------------------------------------------------------------

def copy_filters_between_views(source_view, target_views, filter_ids):
    """
    Core function to transfer filters and their overrides.
    
    Args:
        source_view (DB.View): The view/template to copy graphics FROM.
        target_views (list[DB.View]): The views/templates to copy graphics TO.
        filter_ids (list[DB.ElementId]): The specific filters to be synchronized.
    """
    # Start a transaction to modify the database
    t = Transaction(doc, "LUDARP: Copy Filters Between Views")
    t.Start()
    
    for target_view in target_views:
        for fid in filter_ids:
            # 🟢 Check if the filter exists in the target view; if not, add it.
            if not target_view.GetFilters().Contains(fid):
                target_view.AddFilter(fid)
            
            # 🎨 Copy Overrides (Colors, Lines, Fills, Transparency)
            overrides = source_view.GetFilterOverrides(fid)
            target_view.SetFilterOverrides(fid, overrides)

            # 👁️ Synchronize Visibility State (On/Off)
            if hasattr(source_view, "GetFilterVisibility") and hasattr(target_view, "SetFilterVisibility"):
                try:
                    vis_state = source_view.GetFilterVisibility(fid)
                    target_view.SetFilterVisibility(fid, vis_state)
                except Exception:
                    # Fallback for older Revit versions or specific view types
                    pass
    
    t.Commit()

# ---------------------------------------------------------------------------------
# UI HELPERS: CATEGORIZED PICKER
# ---------------------------------------------------------------------------------

# Define which view types are supported for processing
valid_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation, 
    ViewType.ThreeD, ViewType.Section, ViewType.Detail, 
    ViewType.EngineeringPlan, ViewType.AreaPlan
]

class ViewItem:
    """Wrapper class for Revit View elements to display with custom labels/emojis."""
    def __init__(self, view):
        self.view = view
        self.Id = view.Id
        # Premium labeling based on whether it's a template or a specific view type
        if view.IsTemplate:
            self.Name = "   🎨 [Template] " + view.Name
        else:
            v_type_str = str(view.ViewType).replace("ViewType.", "").replace("ThreeD", "3D")
            self.Name = "   📄 [" + v_type_str + "] " + view.Name

class SeparatorItem:
    """Used to create non-clickable category headers in the selection list."""
    def __init__(self, title):
        self.Name = "💠 " + title.upper() + " 💠"
        self.view = None
        self.Id = None

def build_view_dict(all_views, exclude_id=None):
    """
    Builds a categorized and searchable dictionary of views for pyRevit's UI.
    
    Returns:
        OrderedDict: Categorized views (Templates, Plans, Sections, etc.)
    """
    all_valid = []
    templates = []
    by_type = {}
    
    for v in all_views:
        # Exclude the source view if we are picking targets
        if exclude_id and v.Id == exclude_id:
            continue
            
        if v.IsTemplate:
            templates.append(ViewItem(v))
        elif v.ViewType in valid_types:
            item = ViewItem(v)
            # Create a category name (e.g., "📁 Floor Plans")
            cat_name = "📁 " + str(v.ViewType).replace("ViewType.", "").replace("ThreeD", "3D") + "s"
            if cat_name not in by_type:
                by_type[cat_name] = []
            by_type[cat_name].append(item)
            
    # Sort templates and each category alphabetically
    templates.sort(key=lambda x: x.Name)
    for cat in by_type:
        by_type[cat].sort(key=lambda x: x.Name)
        
    # Construct the master list with visual separators
    if templates:
        all_valid.append(SeparatorItem("VIEW TEMPLATES"))
        all_valid.extend(templates)
        
    for cat in sorted(by_type.keys()):
        if by_type[cat]:
            all_valid.append(SeparatorItem(cat.replace("📁 ", "")))
            all_valid.extend(by_type[cat])
        
    # Map data to the pyRevit SelectFromList tabs
    d = OrderedDict()
    d[" 🌍 ALL VIEWS & TEMPLATES"] = all_valid
    d["⭐ VIEW TEMPLATES"] = templates
    for cat in sorted(by_type.keys()):
        d[cat] = by_type[cat]
    return d

# ---------------------------------------------------------------------------------
# MAIN SCRIPT EXECUTION
# ---------------------------------------------------------------------------------

def main():
    # Collect all views in the current project
    all_views = FilteredElementCollector(doc).OfClass(View)

    # 🟦 STEP 1: Select the SOURCE View or Template
    source_option = forms.SelectFromList.show(
        build_view_dict(all_views), 
        name_attr="Name", 
        multiselect=False, 
        title="1. Pick SOURCE (Copy Graphics FROM)"
    )
    if not source_option or source_option.view is None:
        script.exit()
    source_view = source_option.view

    # 🟦 STEP 2: Select the TARGET View(s) or Template(s)
    target_options = forms.SelectFromList.show(
        build_view_dict(all_views, exclude_id=source_view.Id),
        name_attr="Name",
        multiselect=True,
        title="2. Pick TARGETS (Copy Graphics TO)"
    )
    if not target_options:
        script.exit()
    target_views = [opt.view for opt in target_options if opt.view is not None]

    if not target_views:
        forms.alert("No valid target selected.")
        script.exit()

    # 🟦 STEP 3: Select which Filters to synchronize
    filters_in_source = [doc.GetElement(fid) for fid in source_view.GetFilters()]
    if not filters_in_source:
        forms.alert("No filters found in source view/template.")
        script.exit()

    filters_to_copy = forms.SelectFromList.show(
        filters_in_source, 
        name_attr="Name", 
        multiselect=True, 
        title="3. Pick Filters to Sync"
    )
    if not filters_to_copy:
        script.exit()

    # 🟩 EXECUTE: Run the copy operation
    copy_filters_between_views(source_view, target_views, [f.Id for f in filters_to_copy])

    # 🎉 SUCCESS: Report results to user
    forms.toast("Filters synchronized successfully!")
    forms.alert("Success! Copied {} filter(s) from '{}' to {} target(s).".format(
        len(filters_to_copy), source_view.Name, len(target_views)), 
        title="LUDARP: Sync Complete")

if __name__ == "__main__":
    main()
