# -*- coding: utf-8 -*-
"""
🧹 LUDARP Filter Override: Reset Filters
Version: 1.2 | Author: PRADUL P

This script clears all graphic overrides for selected filters in a view, 
returning them to their default project appearance.
"""
__title__ = "Reset\nFilters"
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
        title="1. Pick View/Template to Reset"
    )
    if not target_option or target_option.view is None:
        script.exit()
    target_view = target_option.view

    # 🟦 STEP 2: Pick Filter(s) to Reset
    filters_in_view = [doc.GetElement(fid) for fid in target_view.GetFilters()]
    if not filters_in_view:
        forms.alert("No filters found in the selected view/template.")
        script.exit()

    selected_filters = forms.SelectFromList.show(
        filters_in_view,
        name_attr="Name",
        multiselect=True,
        title="2. Pick Filter(s) to RESET"
    )
    if not selected_filters:
        script.exit()

    # 🟩 EXECUTE: Reset overrides via Transaction
    t = Transaction(doc, "LUDARP: Reset Filter Overrides")
    t.Start()
    
    # Create a default (blank) override object
    default_ogs = OverrideGraphicSettings()
    
    for f in selected_filters:
        try:
            target_view.SetFilterOverrides(f.Id, default_ogs)
        except Exception:
            pass
            
    t.Commit()

    # 🎉 SUCCESS
    forms.toast("Filter overrides reset successfully!")
    forms.alert("Reset overrides for {} filter(s) in '{}'.".format(len(selected_filters), target_view.Name), 
                title="LUDARP: Reset Complete")

if __name__ == "__main__":
    main()
