# -*- coding: utf-8 -*-
"""
📋 LUDARP Filter Override: Duplicate Filter
Version: 1.2 | Author: PRADUL P

This script allows users to create a clone of an existing parameter filter, 
automatically preserving its categories, rules, and graphic overrides 
within the current view.
"""
__title__ = "Duplicate\nFilter"
__author__ = "PRADUL P"
__version__ = "1.2"

from Autodesk.Revit.DB import *
from pyrevit import forms, script
from collections import OrderedDict

# Initialize the document
doc = __revit__.ActiveUIDocument.Document

# ---------------------------------------------------------------------------------
# UI HELPERS: CATEGORIZED VIEW PICKER
# ---------------------------------------------------------------------------------

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
    """Builds a categorized and searchable dictionary of views."""
    all_valid = []
    templates = []
    by_type = {}
    for v in all_views:
        if exclude_id and v.Id == exclude_id: continue
        if v.IsTemplate:
            templates.append(ViewItem(v))
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

# ---------------------------------------------------------------------------------
# MAIN SCRIPT EXECUTION
# ---------------------------------------------------------------------------------

def main():
    # 🟦 STEP 1: Select Target View or Template (to read overrides from)
    all_views = FilteredElementCollector(doc).OfClass(View)
    target_option = forms.SelectFromList.show(
        build_view_dict(all_views),
        name_attr="Name",
        multiselect=False,
        title="1. Pick View/Template containing the Source Filter"
    )
    if not target_option or target_option.view is None:
        script.exit()
    target_view = target_option.view

    # 🟦 STEP 2: Pick Source Filter to Duplicate
    all_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
    all_filters = sorted(all_filters, key=lambda f: f.Name)
    
    source_filter = forms.SelectFromList.show(
        all_filters,
        name_attr="Name",
        multiselect=False,
        title="2. Pick Filter to DUPLICATE"
    )
    if not source_filter:
        script.exit()

    # 🟦 STEP 3: Enter Name for the New Filter
    new_name = forms.ask_for_string(
        default=source_filter.Name + " (Copy)",
        prompt="3. Enter NEW Name for the Duplicate Filter:",
        title="LUDARP: Name Duplicate"
    )
    if not new_name:
        script.exit()

    # 🟩 EXECUTE: Create and configure the duplicate
    # Store current overrides from the selected view
    try:
        current_override = target_view.GetFilterOverrides(source_filter.Id)
    except:
        current_override = OverrideGraphicSettings()

    t = Transaction(doc, "LUDARP: Duplicate Filter")
    t.Start()
    try:
        # Clone properties
        cats = source_filter.GetCategories()
        elem_filter = source_filter.GetElementFilter()
        
        # Create the new ParameterFilterElement
        new_filter = ParameterFilterElement.Create(doc, new_name, cats, elem_filter)

        # Apply same overrides and add to the selected view/template
        if not target_view.GetFilters().Contains(new_filter.Id):
            target_view.AddFilter(new_filter.Id)
        target_view.SetFilterOverrides(new_filter.Id, current_override)

        t.Commit()
        forms.toast("Filter duplicated successfully!")
        forms.alert("Filter '{}' duplicated as '{}'.".format(source_filter.Name, new_name), 
                    title="LUDARP: Success")
    except Exception as e:
        t.RollBack()
        forms.alert("Error during duplication:\n{}".format(e), title="LUDARP: Error")

if __name__ == "__main__":
    main()
