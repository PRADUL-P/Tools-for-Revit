# -*- coding: utf-8 -*-
# pyRevit script: Reset Filters
# Author: ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document
active_view = doc.ActiveView


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
        forms.alert("No filters found in this view.", exitscript=True)
    return forms.SelectFromList.show(filters_in_view, name_attr="Name", multiselect=True, title=msg)


# ---------------- MAIN ---------------- #

filters_to_reset = pick_filters(active_view, msg="Pick Filters to Reset")
if filters_to_reset:
    reset_filter_overrides(active_view, [f.Id for f in filters_to_reset])
    forms.alert("Reset overrides for {} filter(s) in '{}'.".format(
        len(filters_to_reset), active_view.Name
    ))
