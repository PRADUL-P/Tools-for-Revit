# -*- coding: utf-8 -*-
# pyRevit script: Copy Selected Filter Overrides (Final Version)
# Author: PRADUL

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc
view = doc.ActiveView

# ---------------------------
# Collect filters in this view
# ---------------------------
filters = view.GetFilters()
filter_elems = [doc.GetElement(fid) for fid in filters]
filter_names = [f.Name for f in filter_elems]

if not filter_names:
    forms.alert("No filters applied in this view.")
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

def build_override_from_selection(src_ogs, options, proj_part, cut_part):
    """Build a fresh OverrideGraphicSettings per target filter."""
    if "Copy ALL" in options:
        return src_ogs

    ogs = OverrideGraphicSettings()

    # ---- Projection Lines ----
    if "Projection Lines" in options:
        col = _getattr_safe(src_ogs, "ProjectionLineColor", None)
        if col: ogs.SetProjectionLineColor(col)
        pid = _getattr_safe(src_ogs, "ProjectionLinePatternId", ElementId.InvalidElementId)
        if _is_valid_id(pid): ogs.SetProjectionLinePatternId(pid)
        w = _getattr_safe(src_ogs, "ProjectionLineWeight", None)
        if w is not None: ogs.SetProjectionLineWeight(w)

    # ---- Cut Lines ----
    if "Cut Lines" in options:
        col = _getattr_safe(src_ogs, "CutLineColor", None)
        if col: ogs.SetCutLineColor(col)
        pid = _getattr_safe(src_ogs, "CutLinePatternId", ElementId.InvalidElementId)
        if _is_valid_id(pid): ogs.SetCutLinePatternId(pid)
        w = _getattr_safe(src_ogs, "CutLineWeight", None)
        if w is not None: ogs.SetCutLineWeight(w)

    # ---- Projection Fills / Surface ----
    if "Projection Fills" in options:
        if proj_part in ("fg", "both"):
            pid = _getattr_safe(src_ogs, "SurfaceForegroundPatternId", ElementId.InvalidElementId)
            if _is_valid_id(pid): ogs.SetSurfaceForegroundPatternId(pid)
            col = _getattr_safe(src_ogs, "SurfaceForegroundPatternColor", None)
            if col: ogs.SetSurfaceForegroundPatternColor(col)
        if proj_part in ("bg", "both"):
            pid = _getattr_safe(src_ogs, "SurfaceBackgroundPatternId", ElementId.InvalidElementId)
            if _is_valid_id(pid): ogs.SetSurfaceBackgroundPatternId(pid)
            col = _getattr_safe(src_ogs, "SurfaceBackgroundPatternColor", None)
            if col: ogs.SetSurfaceBackgroundPatternColor(col)

    # ---- Cut Fills ----
    if "Cut Fills" in options:
        if cut_part in ("fg", "both"):
            pid = _getattr_safe(src_ogs, "CutForegroundPatternId", ElementId.InvalidElementId)
            if _is_valid_id(pid): ogs.SetCutForegroundPatternId(pid)
            col = _getattr_safe(src_ogs, "CutForegroundPatternColor", None)
            if col: ogs.SetCutForegroundPatternColor(col)
        if cut_part in ("bg", "both"):
            pid = _getattr_safe(src_ogs, "CutBackgroundPatternId", ElementId.InvalidElementId)
            if _is_valid_id(pid): ogs.SetCutBackgroundPatternId(pid)
            col = _getattr_safe(src_ogs, "CutBackgroundPatternColor", None)
            if col: ogs.SetCutBackgroundPatternColor(col)

    # ---- Transparency ----
    if "Transparency" in options:
        tr = _getattr_safe(src_ogs, "SurfaceTransparency", None)
        if tr is not None:
            ogs.SetSurfaceTransparency(tr)

    # ---- Halftone ----
    if "Halftone" in options:
        ogs.SetHalftone(_getattr_safe(src_ogs, "Halftone", False))

    # ---- Detail Level ----
    if "Detail Level" in options:
        dl = _getattr_safe(src_ogs, "DetailLevel", None)
        if dl is not None:
            ogs.SetDetailLevel(dl)

    return ogs

# ---------------------------
# Apply overrides per target
# ---------------------------
src_ogs = view.GetFilterOverrides(source_elem.Id)

t = Transaction(doc, "Copy Filter Overrides")
t.Start()
for f in target_elems:
    new_ogs = build_override_from_selection(src_ogs, copy_options, proj_fill_part, cut_fill_part)
    view.SetFilterOverrides(f.Id, new_ogs)
t.Commit()

forms.alert("Overrides copied from '{}' → {} filter(s).".format(source_name, len(target_elems)), title="Done")
