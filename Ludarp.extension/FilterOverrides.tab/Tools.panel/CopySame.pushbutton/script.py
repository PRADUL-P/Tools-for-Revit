from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script   # <-- added script here

doc = revit.doc
view = doc.ActiveView

# Collect all filters applied to the view
filters = view.GetFilters()
filter_names = [revit.doc.GetElement(fid).Name for fid in filters]

# Ask user: source filter
source_name = forms.SelectFromList.show(filter_names, title="Pick Source Filter", multiselect=False)
if not source_name:
    forms.alert("No source selected")
    script.exit()   # <-- now works correctly

# Ask user: target filters
target_names = forms.SelectFromList.show(filter_names, title="Pick Target Filters", multiselect=True)
if not target_names:
    forms.alert("No target selected")
    script.exit()

# Find filter IDs
source_id = [fid for fid in filters if doc.GetElement(fid).Name == source_name][0]
target_ids = [fid for fid in filters if doc.GetElement(fid).Name in target_names]

# Get override settings of source filter
source_override = view.GetFilterOverrides(source_id)

# Apply to targets
t = Transaction(doc, "Copy Filter Overrides")
t.Start()
for tid in target_ids:
    view.SetFilterOverrides(tid, source_override)
t.Commit()

forms.alert("Overrides copied from '{}' to selected filters!".format(source_name))
