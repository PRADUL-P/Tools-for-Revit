# -*- coding: utf-8 -*-
# pyRevit script: Reset Filters (Select View/Template)
# Author: ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document

# ---------------------------
# Ask user to select the target view or template
# ---------------------------
views_and_templates = [v for v in FilteredElementCollector(doc).OfClass(View)]
target_view = forms.SelectFromList.show(
    views_and_templates,
    name_attr="Name",
    multiselect=False,
    title="Pick Target View or Template to Reset Filters"
)
if not target_view:
    forms.alert("No view/template selected.")
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
