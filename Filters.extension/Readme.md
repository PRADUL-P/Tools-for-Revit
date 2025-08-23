# Filters Toolkit – PyRevit Extension


## Overview

The **Filters Toolkit** provides tools to manage, copy, and reset graphic filter overrides in Revit views. This extension helps improve workflow efficiency, maintain consistency across views, and reduce manual override errors.

**Key Features:**
- Copy overrides between filters within a view.
- Copy selected filters and their overrides between views.
- Reset filters to default Revit display settings.
- Flexible selection of override properties.

---

## Included Tools

| Button | Script | Function |
|--------|--------|---------|
| **Manage Filters** | script.py | Multi-purpose tool: copy overrides in the same view, between views, or reset filters. |
| **Copy Filters Between Views** | copy_between.py | Copies selected filters and overrides from a source view to one or more target views. |
| **Copy Selected Filter Overrides** | copy_selected_filter_overrides.py | Copy specific override properties from a source filter to multiple target filters in the same view. |
| **Copy All Filter Overrides** | all_filters.py | Copy all overrides from a source filter to multiple target filters in the same view. |
| **Reset Filters** | reset.py | Resets selected filters to default Revit display settings in the active view. |

---

## Usage Instructions

### Manage Filters
- Multi-action tool to manage filters in a view or across views:
  1. **Copy Overrides (Same View):** Copy overrides from one filter to one or more filters in the current view.  
  2. **Copy From Template:** Copy selected filters and overrides from the current view to other views.  
  3. **Copy From Another Template:** Select a source view and copy filters + overrides to target views.  
  4. **Reset Filters:** Reset overrides for selected filters in the active view.  
  5. **Close:** Exit the tool.  
- Follow prompts to select filters and target views. A confirmation popup appears when done.

### Copy Filters Between Views
1. Pick a source view.  
2. Select one or more target views.  
3. Choose filters to copy.  
4. Filters and overrides are copied to all selected target views.  
5. A confirmation popup appears after completion.

### Copy Selected Filter Overrides
1. Select the source filter.  
2. Select one or more target filters.  
3. Choose specific override properties (lines, fills, transparency, halftone, detail level, or all).  
4. Specify foreground/background for fills if needed.  
5. Overrides are applied. Confirmation appears.

### Copy All Filter Overrides
1. Select the source filter.  
2. Select one or more target filters.  
3. All overrides are applied. Confirmation appears.

### Reset Filters
1. Select filters in the active view.  
2. Overrides are reset to default Revit display settings.  
3. A confirmation popup appears when done.

---

## Installation Instructions

1. Place the **Filters.extension** folder in:  %AppData%\pyRevit-Master\extensions\

2. Ensure scripts and `bundle.yaml` files are inside each button folder.  
3. (Optional) Add icons (32x32 px) for each button.  
4. Restart Revit. The **FilterOverrides** tab will appear with your toolkit.

---

## Recommended Folder Structure
Filters.extension
├─ FilterOverrides.tab
│ └─ Tools.panel
│ ├─ ManageFilters.pushbutton
│ │ ├─ script.py
│ │ └─ bundle.yaml
│ ├─ CopyBetween.pushbutton
│ │ ├─ copy_between.py
│ │ └─ bundle.yaml
│ ├─ CopySame.pushbutton
│ │ ├─ copy_selected_filter_overrides.py
│ │ └─ bundle.yaml
│ ├─ AllFilters.pushbutton
│ │ ├─ all_filters.py
│ │ └─ bundle.yaml
│ └─ Reset.pushbutton
│ ├─ reset.py
│ └─ bundle.yaml
└─ (Optional) icons/
