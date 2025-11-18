# -*- coding: utf-8 -*-
# pyRevit Script: Duplicate Parameter Filter with Same Overrides (View/Template Aware)
# Author: PRADUL + ChatGPT

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

doc = revit.doc

# -------------------------
# Select target view/template first
# -------------------------
views_and_templates = [v for v in FilteredElementCollector(doc).OfClass(View)]
target_view = forms.SelectFromList.show(
    views_and_templates, name_attr="Name", multiselect=False, title="Pick Target View/Template"
)
if not target_view:
    forms.alert("No target view/template selected")
    script.exit()

# -------------------------
# Collect all parameter filters in project
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
# Try to get overrides from target (if filter exists there)
# -------------------------
try:
    current_override = target_view.GetFilterOverrides(source_filter.Id)
except:
    current_override = OverrideGraphicSettings()  # empty fallback

# -------------------------
# Duplicate filter and apply overrides
# -------------------------
t = Transaction(doc, "Duplicate Filter with Overrides")
t.Start()
try:
    # Duplicate filter definition
    cats = source_filter.GetCategories()
    elem_filter = source_filter.GetElementFilter()
    new_filter = ParameterFilterElement.Create(doc, new_name, cats, elem_filter)

    # Apply override
    target_view.SetFilterOverrides(new_filter.Id, current_override)

    # Add filter if not already applied
    if not target_view.GetFilters().Contains(new_filter.Id):
        target_view.AddFilter(new_filter.Id)

    t.Commit()
    forms.alert("✅ Filter '{}' duplicated as '{}' with same overrides in '{}'.".format(
        source_name, new_name, target_view.Name))

except Exception as e:
    t.RollBack()
    forms.alert("❌ Failed to duplicate filter: {}".format(e))
