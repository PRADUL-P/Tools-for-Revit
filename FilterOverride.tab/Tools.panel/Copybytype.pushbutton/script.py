# -*- coding: utf-8 -*-
__title__ = "Copy Specific\nOverrides"
__doc__ = """Copy Specific Filter Properties:
Step 1: Pick the TARGET View/Template where you want to apply changes.
Step 2: Pick the SOURCE Filter (the one with the colors you like).
Step 3: Select one or more TARGET Filters to receive those colors.
Step 4: Choose exactly what to copy (Lines, Fills, Transparency, etc.).

_____________________________________________________________________
Version: 1.1 | Author: PRADUL P"""
__author__ = "PRADUL P"
__version__ = "1.1"

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc

from collections import OrderedDict

# ---------------------------
# UI Helpers for View Selection
# ---------------------------
valid_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation, 
    ViewType.ThreeD, ViewType.Section, ViewType.Detail, 
    ViewType.EngineeringPlan, ViewType.AreaPlan
]

class ViewItem:
    def __init__(self, view):
        self.view = view
        self.Id = view.Id
        if view.IsTemplate:
            self.Name = "   🎨 [Template] " + view.Name
        else:
            self.Name = "   📄 [" + str(view.ViewType).replace("ViewType.", "").replace("ThreeD", "3D") + "] " + view.Name

class SeparatorItem:
    def __init__(self, title):
        self.Name = "💠 " + title.upper() + " 💠"
        self.view = None
        self.Id = None

def build_view_dict(all_views, exclude_id=None):
    all_valid = []
    templates = []
    by_type = {}
    for v in all_views:
        if exclude_id and v.Id == exclude_id: continue
        if v.IsTemplate:
            item = ViewItem(v)
            templates.append(item)
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


def _getattr_safe(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except Exception:
        return default


# ---------------- MAIN ---------------- #

# Step 1: Pick Target View/Template
all_views = FilteredElementCollector(doc).OfClass(View)
target_option = forms.SelectFromList.show(
    build_view_dict(all_views),
    name_attr="Name",
    multiselect=False,
    title="Step 1: Pick TARGET View or Template"
)
if not target_option or target_option.view is None:
    forms.alert("Operation cancelled.")
    script.exit()
target_view = target_option.view

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
    if "Copy ALL" in copy_options:
        # Just use the exact same overrides from the source
        target_ogs = src_ogs
        # Copy visibility state if available
        if hasattr(target_view, "GetFilterVisibility") and hasattr(target_view, "SetFilterVisibility"):
            try:
                vis_state = target_view.GetFilterVisibility(source_elem.Id)
                target_view.SetFilterVisibility(f.Id, vis_state)
            except Exception:
                pass
    else:
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
