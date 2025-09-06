# -*- coding: utf-8 -*-
# pyRevit script: Copy Filters with Overrides (Views + Templates)
# Author: PRADUL P + ChatGPT

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


# ---------------- MAIN ---------------- #
# collect all views (normal + templates)
views = list(FilteredElementCollector(doc).OfClass(View))

if not views:
    forms.alert("No views or templates found in this project.")
    script.exit()

# pick source
source_view = forms.SelectFromList.show(
    views, name_attr="Name", multiselect=False, title="Pick Source View/Template"
)
if not source_view:
    forms.alert("No source view/template selected.")
    script.exit()

# pick target(s)
target_views = forms.SelectFromList.show(
    [v for v in views if v.Id != source_view.Id],
    name_attr="Name",
    multiselect=True,
    title="Pick Target View(s)/Template(s)"
)
if not target_views:
    forms.alert("No target view/template selected.")
    script.exit()

# pick filters from source
filters_in_source = [doc.GetElement(fid) for fid in source_view.GetFilters()]
if not filters_in_source:
    forms.alert("No filters found in source view/template.")
    script.exit()

filters_to_copy = forms.SelectFromList.show(
    filters_in_source, name_attr="Name", multiselect=True, title="Pick Filters to Copy"
)
if not filters_to_copy:
    forms.alert("No filters selected.")
    script.exit()

# run copy
copy_filters_between_views(source_view, target_views, [f.Id for f in filters_to_copy])

forms.alert("Copied {} filter(s) from '{}' to {} target view/template(s).".format(
    len(filters_to_copy), source_view.Name, len(target_views)))
