# -*- coding: utf-8 -*-
"""
🎯 LUDARP Filter Override: Copy Specific Overrides
Version: 1.2 | Author: PRADUL P

This script provides granular control over copying graphic properties. Users can
choose specific components (e.g., only Projection Fills or just Transparency) 
to transfer from a source filter to one or more target filters.
"""
__title__ = "Copy Specific\nOverrides"
__author__ = "PRADUL P"
__version__ = "1.2"

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
from collections import OrderedDict

# Initialize the document
doc = revit.doc

# ---------------------------------------------------------------------------------
# UI HELPERS: CATEGORIZED VIEW PICKER
# ---------------------------------------------------------------------------------

valid_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation, 
    ViewType.ThreeD, ViewType.Section, ViewType.Detail, 
    ViewType.EngineeringPlan, ViewType.AreaPlan
]

class ViewItem:
    """Wrapper for Revit View elements to display with custom labels/emojis."""
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
    """Builds a categorized dictionary of views for selection."""
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
# DATA EXTRACTION HELPERS
# ---------------------------------------------------------------------------------

def _is_valid_id(eid):
    """Check if an ElementId is valid and not null."""
    return isinstance(eid, ElementId) and eid != ElementId.InvalidElementId

def _getattr_safe(obj, name, default=None):
    """Safely get an attribute from an object with a fallback value."""
    try:
        return getattr(obj, name, default)
    except:
        return default

# ---------------------------------------------------------------------------------
# MAIN SCRIPT EXECUTION
# ---------------------------------------------------------------------------------

def main():
    # 🟦 STEP 1: Select the TARGET View or Template
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

    # 🟦 STEP 2: Select the SOURCE Filter (Copy Graphics FROM)
    filters_in_view = [doc.GetElement(fid) for fid in target_view.GetFilters()]
    if not filters_in_view:
        forms.alert("No filters found in the selected view.")
        script.exit()

    source_elem = forms.SelectFromList.show(
        filters_in_view,
        name_attr="Name",
        multiselect=False,
        title="2. Pick SOURCE Filter (Copy FROM)"
    )
    if not source_elem:
        script.exit()

    # 🟦 STEP 3: Select the TARGET Filters (Copy Graphics TO)
    target_elems = forms.SelectFromList.show(
        [f for f in filters_in_view if f.Id != source_elem.Id],
        name_attr="Name",
        multiselect=True,
        title="3. Pick TARGET Filters (Copy TO)"
    )
    if not target_elems:
        script.exit()

    # 🟦 STEP 4: Choose specific Override Properties to copy
    copy_options = forms.SelectFromList.show(
        [
            "Projection Lines", "Projection Fills",
            "Cut Lines", "Cut Fills",
            "Transparency", "Halftone",
            "Detail Level", "Copy ALL"
        ],
        title="4. Select Properties to Copy",
        multiselect=True
    )
    if not copy_options:
        script.exit()

    # Special handling for Fills (Foreground vs Background)
    choice_map = {"Foreground": "fg", "Background": "bg", "Both": "both"}
    proj_fill_part = "both"
    cut_fill_part = "both"

    if "Projection Fills" in copy_options and "Copy ALL" not in copy_options:
        _pick = forms.SelectFromList.show(
            ["Foreground", "Background", "Both"],
            title="Projection Fill: Which part to copy?",
            multiselect=False
        )
        if _pick: proj_fill_part = choice_map[_pick]

    if "Cut Fills" in copy_options and "Copy ALL" not in copy_options:
        _pick = forms.SelectFromList.show(
            ["Foreground", "Background", "Both"],
            title="Cut Fill: Which part to copy?",
            multiselect=False
        )
        if _pick: cut_fill_part = choice_map[_pick]

    # 🟩 EXECUTE: Apply overrides per target
    t = Transaction(doc, "LUDARP: Copy Specific Overrides")
    t.Start()

    src_ogs = target_view.GetFilterOverrides(source_elem.Id)

    for f in target_elems:
        if "Copy ALL" in copy_options:
            target_view.SetFilterOverrides(f.Id, src_ogs)
            # Copy visibility state
            if hasattr(target_view, "GetFilterVisibility"):
                target_view.SetFilterVisibility(f.Id, target_view.GetFilterVisibility(source_elem.Id))
        else:
            # Preserve existing overrides that weren't selected for change
            target_ogs = target_view.GetFilterOverrides(f.Id)

            # ---- Lines Synchronization ----
            if "Projection Lines" in copy_options:
                target_ogs.SetProjectionLineColor(_getattr_safe(src_ogs, "ProjectionLineColor"))
                target_ogs.SetProjectionLinePatternId(_getattr_safe(src_ogs, "ProjectionLinePatternId"))
                target_ogs.SetProjectionLineWeight(_getattr_safe(src_ogs, "ProjectionLineWeight"))

            if "Cut Lines" in copy_options:
                target_ogs.SetCutLineColor(_getattr_safe(src_ogs, "CutLineColor"))
                target_ogs.SetCutLinePatternId(_getattr_safe(src_ogs, "CutLinePatternId"))
                target_ogs.SetCutLineWeight(_getattr_safe(src_ogs, "CutLineWeight"))

            # ---- Fills Synchronization ----
            if "Projection Fills" in copy_options:
                if proj_fill_part in ("fg", "both"):
                    target_ogs.SetSurfaceForegroundPatternId(_getattr_safe(src_ogs, "SurfaceForegroundPatternId"))
                    target_ogs.SetSurfaceForegroundPatternColor(_getattr_safe(src_ogs, "SurfaceForegroundPatternColor"))
                if proj_fill_part in ("bg", "both"):
                    target_ogs.SetSurfaceBackgroundPatternId(_getattr_safe(src_ogs, "SurfaceBackgroundPatternId"))
                    target_ogs.SetSurfaceBackgroundPatternColor(_getattr_safe(src_ogs, "SurfaceBackgroundPatternColor"))

            if "Cut Fills" in copy_options:
                if cut_fill_part in ("fg", "both"):
                    target_ogs.SetCutForegroundPatternId(_getattr_safe(src_ogs, "CutForegroundPatternId"))
                    target_ogs.SetCutForegroundPatternColor(_getattr_safe(src_ogs, "CutForegroundPatternColor"))
                if cut_fill_part in ("bg", "both"):
                    target_ogs.SetCutBackgroundPatternId(_getattr_safe(src_ogs, "CutBackgroundPatternId"))
                    target_ogs.SetCutBackgroundPatternColor(_getattr_safe(src_ogs, "CutBackgroundPatternColor"))

            # ---- Misc Properties ----
            if "Transparency" in copy_options:
                target_ogs.SetSurfaceTransparency(_getattr_safe(src_ogs, "SurfaceTransparency"))
            if "Halftone" in copy_options:
                target_ogs.SetHalftone(_getattr_safe(src_ogs, "Halftone"))
            if "Detail Level" in copy_options:
                target_ogs.SetDetailLevel(_getattr_safe(src_ogs, "DetailLevel"))

            target_view.SetFilterOverrides(f.Id, target_ogs)

    t.Commit()

    # 🎉 SUCCESS: Toast and Alert
    forms.toast("Overrides copied successfully!")
    forms.alert("Overrides copied from '{}' → {} filter(s) in '{}'.".format(
        source_elem.Name, len(target_elems), target_view.Name), 
        title="LUDARP: Sync Complete")

if __name__ == "__main__":
    main()
