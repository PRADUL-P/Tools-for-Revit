# -*- coding: utf-8 -*-
# pyRevit script: Copy Selected Filter Overrides (Pick Template/View)
# Author: PRADUL

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc

# ---------------------------
# Ask user to select target view/template first
# ---------------------------
views_and_templates = [v for v in FilteredElementCollector(doc).OfClass(View)]
target_view = forms.SelectFromList.show(
    views_and_templates,
    name_attr="Name",
    multiselect=False,
    title="Pick Target View or Template"
)
if not target_view:
    forms.alert("No view/template selected.")
    script.exit()

# ---------------------------
# Collect filters in the chosen view/template
# ---------------------------
filters = target_view.GetFilters()
filter_elems = [doc.GetElement(fid) for fid in filters]
filter_names = [f.Name for f in filter_elems]

if not filter_names:
    forms.alert("No filters applied in the selected view/template.")
    script.exit()

# ---------------------------
# Pick source & target filters
# ---------------------------
source_name = forms.SelectFromList.show(filter_names, title="Pick Source Filter", multiselect=False)
if not source_name:
    script.exit()

target_names = forms.SelectFromList.show(
    [n for n in filter_names if n != source_name],
    title="Pick Target Filters",
    multiselect=True
)
if not target_names:
    script.exit()

source_elem = next(f for f in filter_elems if f.Name == source_name)
target_elems = [f for f in filter_elems if f.Name in target_names]

# ---------------------------
# Choose properties to copy
# ---------------------------
copy_options = forms.SelectFromList.show(
    [
        "Projection Lines",
        "Projection Fills",
        "Cut Lines",
        "Cut Fills",
        "Transparency",
        "Halftone",
        "Detail Level",
        "Copy ALL"
    ],
    title="Select Override Properties to Copy",
    multiselect=True
)
if not copy_options:
    script.exit()

# ---------------------------
# Ask FG/BG for fills separately
# ---------------------------
choice_map = {
    "Foreground only": "fg",
    "Background only": "bg",
    "Both (All)": "both"
}

proj_fill_part = None
cut_fill_part = None

if "Projection Fills" in copy_options and "Copy ALL" not in copy_options:
    _pick = forms.SelectFromList.show(
        ["Foreground only", "Background only", "Both (All)"],
        title="Projection Fill Pattern: Which part to copy?",
        multiselect=False
    )
    if not _pick:
        script.exit()
    proj_fill_part = choice_map[_pick]

if "Cut Fills" in copy_options and "Copy ALL" not in copy_options:
    _pick = forms.SelectFromList.show(
        ["Foreground only", "Background only", "Both (All)"],
        title="Cut Fill Pattern: Which part to copy?",
        multiselect=False
    )
    if not _pick:
        script.exit()
    cut_fill_part = choice_map[_pick]

# ---------------------------
# Helper functions
# ---------------------------
def _is_valid_id(eid):
    return isinstance(eid, ElementId) and eid != ElementId.InvalidElementId

def _getattr_safe(obj, name, default=None):
    try:
        return getattr(obj, name, default)
    except:
        return default

# ---------------------------
# Apply overrides per target (preserve unselected properties)
# ---------------------------
t = Transaction(doc, "Copy Filter Overrides")
t.Start()

src_ogs = target_view.GetFilterOverrides(source_elem.Id)

for f in target_elems:
    # Start from target's current overrides
    target_ogs = target_view.GetFilterOverrides(f.Id)

    # ---- Projection Lines ----
    if "Projection Lines" in copy_options:
        col = _getattr_safe(src_ogs, "ProjectionLineColor", None)
        if col: target_ogs.SetProjectionLineColor(col)
        pid = _getattr_safe(src_ogs, "ProjectionLinePatternId", ElementId.InvalidElementId)
        if _is_valid_id(pid): target_ogs.SetProjectionLinePatternId(pid)
        w = _getattr_safe(src_ogs, "ProjectionLineWeight", None)
        if w is not None: target_ogs.SetProjectionLineWeight(w)

    # ---- Cut Lines ----
    if "Cut Lines" in copy_options:
        col = _getattr_safe(src_ogs, "CutLineColor", None)
        if col: target_ogs.SetCutLineColor(col)
        pid = _getattr_safe(src_ogs, "CutLinePatternId", ElementId.InvalidElementId)
        if _is_valid_id(pid): target_ogs.SetCutLinePatternId(pid)
        w = _getattr_safe(src_ogs, "CutLineWeight", None)
        if w is not None: target_ogs.SetCutLineWeight(w)

    # ---- Projection Fills ----
    if "Projection Fills" in copy_options:
        if proj_fill_part in ("fg", "both"):
            pid = _getattr_safe(src_ogs, "SurfaceForegroundPatternId", None)
            if _is_valid_id(pid): target_ogs.SetSurfaceForegroundPatternId(pid)
            col = _getattr_safe(src_ogs, "SurfaceForegroundPatternColor", None)
            if col: target_ogs.SetSurfaceForegroundPatternColor(col)
        if proj_fill_part in ("bg", "both"):
            pid = _getattr_safe(src_ogs, "SurfaceBackgroundPatternId", None)
            if _is_valid_id(pid): target_ogs.SetSurfaceBackgroundPatternId(pid)
            col = _getattr_safe(src_ogs, "SurfaceBackgroundPatternColor", None)
            if col: target_ogs.SetSurfaceBackgroundPatternColor(col)

    # ---- Cut Fills ----
    if "Cut Fills" in copy_options:
        if cut_fill_part in ("fg", "both"):
            pid = _getattr_safe(src_ogs, "CutForegroundPatternId", None)
            if _is_valid_id(pid): target_ogs.SetCutForegroundPatternId(pid)
            col = _getattr_safe(src_ogs, "CutForegroundPatternColor", None)
            if col: target_ogs.SetCutForegroundPatternColor(col)
        if cut_fill_part in ("bg", "both"):
            pid = _getattr_safe(src_ogs, "CutBackgroundPatternId", None)
            if _is_valid_id(pid): target_ogs.SetCutBackgroundPatternId(pid)
            col = _getattr_safe(src_ogs, "CutBackgroundPatternColor", None)
            if col: target_ogs.SetCutBackgroundPatternColor(col)

    # ---- Transparency ----
    if "Transparency" in copy_options:
        tr = _getattr_safe(src_ogs, "SurfaceTransparency", None)
        if tr is not None:
            target_ogs.SetSurfaceTransparency(tr)

    # ---- Halftone ----
    if "Halftone" in copy_options:
        target_ogs.SetHalftone(_getattr_safe(src_ogs, "Halftone", False))

    # ---- Detail Level ----
    if "Detail Level" in copy_options:
        dl = _getattr_safe(src_ogs, "DetailLevel", None)
        if dl is not None:
            target_ogs.SetDetailLevel(dl)

    # Apply updated overrides to target filter
    target_view.SetFilterOverrides(f.Id, target_ogs)

t.Commit()

forms.alert(
    "Overrides copied from '{}' → {} filter(s) in '{}'.".format(
        source_name, len(target_elems), target_view.Name
    ),
    title="Done"
)
