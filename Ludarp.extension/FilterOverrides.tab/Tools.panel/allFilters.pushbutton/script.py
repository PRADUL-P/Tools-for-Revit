# -*- coding: utf-8 -*-
# pyRevit script: Manage Filters (Optimized + Reset)
# Author: ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document
active_view = doc.ActiveView


# ---------------- FUNCTIONS ---------------- #

def copy_filter_overrides(source_filter, target_filters, view):
    """Copy graphics overrides from one filter to other filters in the same view"""
    ogs = view.GetFilterOverrides(source_filter)
    t = Transaction(doc, "Copy Filter Overrides")
    t.Start()
    for tf in target_filters:
        try:
            view.SetFilterOverrides(tf, ogs)
        except:
            pass
    t.Commit()


def copy_filters_between_views(source_view, target_views, filter_ids):
    """Copy selected filters (with overrides) from one view to other views"""
    t = Transaction(doc, "Copy Filters Between Views")
    t.Start()
    for target_view in target_views:
        for fid in filter_ids:
            if not target_view.GetFilters().Contains(fid):
                target_view.AddFilter(fid)
            overrides = source_view.GetFilterOverrides(fid)
            target_view.SetFilterOverrides(fid, overrides)
    t.Commit()


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


def pick_filters(view, msg="Pick Filters"):
    """Helper function: Pick filters from a view"""
    filters_in_view = [doc.GetElement(fid) for fid in view.GetFilters()]
    if not filters_in_view:
        forms.alert("No filters found in this view.", exitscript=True)
    return forms.SelectFromList.show(filters_in_view, name_attr="Name", multiselect=True, title=msg)


def pick_views(exclude_view=None, msg="Pick Target View(s)", multi=True):
    """Helper function: Pick views (excluding templates and optionally a source view)"""
    views = [v for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate]
    if exclude_view:
        views = [v for v in views if v.Id != exclude_view.Id]
    return forms.SelectFromList.show(views, name_attr="Name", multiselect=multi, title=msg)


# ---------------- UI MENU ---------------- #

action = forms.CommandSwitchWindow.show(
    [
        "Copy Overrides (Same View)",
        "Copy From Template",
        "Copy From Another Template",
        "Reset Filters",
        "Close"
    ],
    message="Select Filter Action"
)

if action == "Copy Overrides (Same View)":
    source = forms.SelectFromList.show(
        [doc.GetElement(fid) for fid in active_view.GetFilters()],
        multiselect=False, name_attr="Name", title="Pick Source Filter"
    )
    targets = pick_filters(active_view, msg="Pick Target Filter(s)")
    if source and targets:
        copy_filter_overrides(source.Id, [t.Id for t in targets], active_view)
        forms.alert("Overrides copied successfully!")

elif action == "Copy From Template":
    target_views = pick_views(exclude_view=active_view, msg="Pick Target View(s)", multi=True)
    if not target_views:
        script.exit()
    filters_to_copy = pick_filters(active_view, msg="Pick Filters to Copy")
    if filters_to_copy:
        copy_filters_between_views(active_view, target_views, [f.Id for f in filters_to_copy])
        forms.alert("Copied {} filter(s) from '{}' to {} target view(s).".format(
            len(filters_to_copy), active_view.Name, len(target_views)
        ))

elif action == "Copy From Another Template":
    source_view = pick_views(msg="Pick Source (Template) View", multi=False)
    if not source_view:
        script.exit()
    target_views = pick_views(exclude_view=source_view, msg="Pick Target View(s)", multi=True)
    if not target_views:
        script.exit()
    filters_to_copy = pick_filters(source_view, msg="Pick Filters to Copy")
    if filters_to_copy:
        copy_filters_between_views(source_view, target_views, [f.Id for f in filters_to_copy])
        forms.alert("Copied {} filter(s) from '{}' to {} target view(s).".format(
            len(filters_to_copy), source_view.Name, len(target_views)
        ))

elif action == "Reset Filters":
    filters_to_reset = pick_filters(active_view, msg="Pick Filters to Reset")
    if filters_to_reset:
        reset_filter_overrides(active_view, [f.Id for f in filters_to_reset])
        forms.alert("Reset overrides for {} filter(s) in '{}'.".format(
            len(filters_to_reset), active_view.Name
        ))

elif action == "Close":
    script.exit()
