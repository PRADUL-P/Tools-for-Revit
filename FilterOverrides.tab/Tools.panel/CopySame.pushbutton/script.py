# -*- coding: utf-8 -*-
# pyRevit script: Copy Filter Overrides inside a View Template
from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc
active_view = doc.ActiveView

# 1) Determine template to operate on
if active_view.IsTemplate:
    template_view = active_view
else:
    all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
    templates = [v for v in all_views if v.IsTemplate]
    if not templates:
        forms.alert("No view templates found in the project.")
        script.exit()
    # present templates with ids to avoid duplicate name confusion
    template_choices = ["{} [{}]".format(t.Name, t.Id.IntegerValue) for t in templates]
    sel = forms.SelectFromList.show(template_choices, title="Select View Template", multiselect=False)
    if not sel:
        script.exit()
    template_view = templates[template_choices.index(sel)]

# 2) Get filters assigned to the template
filter_ids = list(template_view.GetFilters())
if not filter_ids:
    forms.alert("No filters assigned to template '{}'.".format(template_view.Name))
    script.exit()

# Build display list (name + id) to avoid duplicate-name issues
display_names = []
for fid in filter_ids:
    f = doc.GetElement(fid)
    fname = f.Name if f is not None else "<Unknown>"
    display_names.append("{} [{}]".format(fname, fid.IntegerValue))

# 3) Ask user for source filter (single)
source_display = forms.SelectFromList.show(display_names, title="Pick SOURCE filter (copy from)", multiselect=False)
if not source_display:
    script.exit()
source_idx = display_names.index(source_display)
source_id = filter_ids[source_idx]

# 4) Ask user for target filters (multi)
target_displays = forms.SelectFromList.show(display_names, title="Pick TARGET filter(s) (paste into)", multiselect=True)
if not target_displays:
    script.exit()
target_ids = [filter_ids[display_names.index(d)] for d in target_displays]

# 5) Read source overrides
try:
    source_override = template_view.GetFilterOverrides(source_id)
except Exception as e:
    forms.alert("Failed to read overrides from source filter: {}".format(e))
    script.exit()

# 6) Try to capture visibility state if available
source_visibility = None
if hasattr(template_view, "GetFilterVisibility"):
    try:
        source_visibility = template_view.GetFilterVisibility(source_id)
    except Exception:
        source_visibility = None

# 7) Apply overrides to targets inside a transaction
t = Transaction(doc, "Copy Filter Overrides inside template '{}'".format(template_view.Name))
t.Start()
for tid in target_ids:
    try:
        # ensure target exists in template (it will, because we listed from template)
        template_view.SetFilterOverrides(tid, source_override)
        if source_visibility is not None and hasattr(template_view, "SetFilterVisibility"):
            template_view.SetFilterVisibility(tid, source_visibility)
    except Exception as e:
        # continue with next target; print to console for debugging
        print("Failed to set overrides for {} : {}".format(tid.IntegerValue, e))
t.Commit()

forms.alert("Copied overrides from '{}' to {} target(s) in template '{}'.".format(
    doc.GetElement(source_id).Name, len(target_ids), template_view.Name))
