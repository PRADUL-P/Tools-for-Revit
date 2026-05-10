# -*- coding: utf-8 -*-
"""
🎨 LUDARP Filter Override: Change Colors
Version: 1.2 | Author: PRADUL P

This script allows users to bulk-update graphic overrides (colors and patterns) 
for multiple filters within a selected view or template.
"""
__title__ = "Change Colors"
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
    # 🟦 STEP 1: Select Target View or Template
    all_views = FilteredElementCollector(doc).OfClass(View)
    target_option = forms.SelectFromList.show(
        build_view_dict(all_views),
        name_attr="Name",
        multiselect=False,
        title="1. Pick TARGET View or Template"
    )
    if not target_option or target_option.view is None:
        script.exit()
    target_view = target_option.view

    # 🟦 STEP 2: Pick Filters to Modify
    filters_in_view = [doc.GetElement(fid) for fid in target_view.GetFilters()]
    if not filters_in_view:
        forms.alert("No filters found in the selected view/template.")
        script.exit()

    selected_filters = forms.SelectFromList.show(
        filters_in_view,
        name_attr="Name",
        multiselect=True,
        title="2. Pick Filters to Modify"
    )
    if not selected_filters:
        script.exit()

    # 🟦 STEP 3: Choose Override Mode (Projection vs Cut)
    mode = forms.CommandSwitchWindow.show(
        ["Projection", "Cut"],
        message="3. Which part of the filter graphics would you like to override?"
    )
    if not mode:
        script.exit()

    # 🟦 STEP 4: Pick New Color
    new_color = forms.ask_for_color()
    if not new_color:
        script.exit()

    # 🟦 STEP 5: Pick New Pattern
    all_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    all_patterns = sorted(all_patterns, key=lambda p: p.Name)
    
    new_pattern = forms.SelectFromList.show(
        all_patterns,
        name_attr="Name",
        multiselect=False,
        title="4. Select New Fill Pattern"
    )
    if not new_pattern:
        script.exit()

    # 🟩 EXECUTE: Apply changes via Transaction
    t = Transaction(doc, "LUDARP: Bulk Change Filter Colors")
    t.Start()
    
    for f in selected_filters:
        # Get current overrides to preserve other properties (halftone, etc.)
        ogs = target_view.GetFilterOverrides(f.Id)
        
        if mode == "Projection":
            ogs.SetSurfaceForegroundPatternId(new_pattern.Id)
            ogs.SetSurfaceForegroundPatternColor(new_color)
        else:
            ogs.SetCutForegroundPatternId(new_pattern.Id)
            ogs.SetCutForegroundPatternColor(new_color)
            
        target_view.SetFilterOverrides(f.Id, ogs)
        
    t.Commit()

    # 🎉 SUCCESS
    forms.toast("Filter colors updated successfully!")
    forms.alert("Updated {} filter(s) in '{}'.".format(len(selected_filters), target_view.Name), 
                title="LUDARP: Change Colors")

if __name__ == "__main__":
    main()
