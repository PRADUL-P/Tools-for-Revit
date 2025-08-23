# -*- coding: utf-8 -*-
# pyRevit script: Copy Filters from one View to others
# Author: ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import forms, script   # <-- added script

doc = __revit__.ActiveUIDocument.Document


def copy_filters_between_views(source_view, target_views, filter_ids):
    """Copy selected filters with overrides from one view to other views"""
    t = Transaction(doc, "Copy Filters")
    t.Start()
    for target_view in target_views:
        for fid in filter_ids:
            # Add filter if target view doesn't already have it
            if not target_view.GetFilters().Contains(fid):
                target_view.AddFilter(fid)
            # Copy overrides
            overrides = source_view.GetFilterOverrides(fid)
            target_view.SetFilterOverrides(fid, overrides)
    t.Commit()


# ---------------- MAIN ---------------- #
# collect all non-template views
views = [v for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate]

# pick source view
source_view = forms.SelectFromList.show(
    views, name_attr="Name", multiselect=False, title="Pick Source (Template) View"
)
if not source_view:
    forms.alert("No source view selected.")
    script.exit()

# pick target views
target_views = forms.SelectFromList.show(
    [v for v in views if v.Id != source_view.Id],
    name_attr="Name",
    multiselect=True,
    title="Pick Target View(s)"
)
if not target_views:
    forms.alert("No target views selected.")
    script.exit()

# pick filters to copy (or all)
filters_in_source = [doc.GetElement(fid) for fid in source_view.GetFilters()]
filters_to_copy = forms.SelectFromList.show(
    filters_in_source, name_attr="Name", multiselect=True, title="Pick Filters to Copy"
)
if not filters_to_copy:
    forms.alert("No filters selected.")
    script.exit()

# run copy
copy_filters_between_views(source_view, target_views, [f.Id for f in filters_to_copy])
forms.alert("Copied {} filter(s) from '{}' to {} target view(s).".format(
    len(filters_to_copy), source_view.Name, len(target_views)))
