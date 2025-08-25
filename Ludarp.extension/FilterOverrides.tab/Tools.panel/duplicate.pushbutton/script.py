# -*- coding: utf-8 -*-
# pyRevit Script: Duplicate Parameter Filter with Same Overrides
# Author: PRADUL + ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc
view = doc.ActiveView

# -------------------------
# Collect all parameter filters
# -------------------------
collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
all_filters = list(collector)
filter_names = [f.Name for f in all_filters]

if not filter_names:
    forms.alert("No filters found in project.")
    script.exit()

# -------------------------
# Select source filter
# -------------------------
source_name = forms.SelectFromList.show(
    filter_names, title="Pick Filter to Duplicate", multiselect=False
)
if not source_name:
    forms.alert("No filter selected")
    script.exit()

source_filter = [f for f in all_filters if f.Name == source_name][0]

# -------------------------
# Ask new filter name
# -------------------------
new_name = forms.ask_for_string(
    prompt="Enter name for duplicated filter",
    default=source_name + "_Copy"
)
if not new_name:
    forms.alert("No name entered")
    script.exit()

# -------------------------
# Get overrides from current view
# -------------------------
try:
    current_override = view.GetFilterOverrides(source_filter.Id)
except:
    current_override = OverrideGraphicSettings()  # fallback empty override

# -------------------------
# Duplicate filter and apply overrides
# -------------------------
t = Transaction(doc, "Duplicate Filter with Overrides")
t.Start()
try:
    # Duplicate filter
    cats = source_filter.GetCategories()
    elem_filter = source_filter.GetElementFilter()
    new_filter = ParameterFilterElement.Create(doc, new_name, cats, elem_filter)

    # Apply the same override as source filter
    view.SetFilterOverrides(new_filter.Id, current_override)

    # Apply to current view
    if not view.IsFilterApplied(new_filter.Id):
        view.AddFilter(new_filter.Id)

    t.Commit()
    forms.alert("✅ Filter '{}' duplicated as '{}' with same overrides.".format(source_name, new_name))

except Exception as e:
    t.RollBack()
    forms.alert("❌ Failed to duplicate filter: {}".format(e))




#### works fine with coping the same filters 