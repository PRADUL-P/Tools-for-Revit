# 📘 pyRevit Filter Override Toolkit

**Author:** PRADUL P  
**Date:** 2026-05-10  
**Version:** 1.2  

---

## Index
1. [Introduction](#chapter-1-introduction)
2. [Toolbar Overview](#chapter-2-toolbar-overview)
3. [Scripts and Procedures](#chapter-3-scripts-and-procedures)
   - 3.1 [Change Colors](#31-change-colors)
   - 3.2 [Copy Between Views](#32-copy-between-views)
   - 3.3 [Copy Specific Overrides](#33-copy-specific-overrides)
   - 3.4 [Duplicate Filter](#34-duplicate-filter)
   - 3.5 [Reset Filters](#35-reset-filters)
4. [Usage Tips](#chapter-4-usage-tips)
5. [Examples](#chapter-5-examples)
6. [Revision History](#chapter-6-revision-history)

---

## Chapter 1: Introduction
This toolkit provides a professional suite of pyRevit scripts to manage, synchronize, duplicate, and reset Revit filter overrides efficiently. It empowers users to maintain rigorous graphic standards, optimize view management, and ensure template accuracy across complex project environments.

---

## Chapter 2: Toolbar Overview
The scripts are organized under the **FilterOverride** tab in the pyRevit ribbon. The toolbar is divided into primary tools and a specialized **Manage** stack.

| Tool Name | Description |
| :--- | :--- |
| **Copy Between** | Synchronize filters/overrides between source and multiple target views. |
| **Copy Overrides** | Granularly copy specific properties from one filter to another. |
| **Manage: Change Colors** | Bulk update colors and fill patterns for multiple filters. |
| **Manage: Duplicate** | Clone parameter filters along with their categories and rules. |
| **Manage: Reset** | Clear all overrides to return filters to project default settings. |

---

## Chapter 3: Scripts and Procedures

### 3.1 Change Colors
**Purpose:** Bulk update colors and fill patterns of filters in a view or template.
**Procedure:**
1. Select the target view or template.
2. Pick filters to modify.
3. Choose properties to override: **Fills** or **Lines**.
4. Select a new color via the Windows Color Picker.
5. Pick a new fill pattern (if modifying fills).
**Example:** Update all "Wall" filters to a specific corporate red foreground fill.

### 3.2 Copy Between Views
**Purpose:** Transfer selected filters and their overrides from a source view to multiple targets.
**Procedure:**
1. Select the **Source** view or template.
2. Select one or more **Target** views/templates.
3. Choose exactly which filters to copy.
**Features:** Automatically adds missing filters to targets and synchronizes all graphic properties.

### 3.3 Copy Specific Overrides
**Purpose:** Transfer specific graphic properties (Lines, Fills, Transparency) from a "Source" filter to one or more "Target" filters.
**Procedure:**
1. Pick the **Target View**.
2. Select the **Source Filter** (the reference style).
3. Select **Target Filters** (the receivers).
4. Select properties to copy: *Projection Lines/Fills, Cut Lines/Fills, Transparency, Halftone, etc.*
**Example:** Copy only the projection fill pattern from the "Fire Wall" filter to the "Smoke Wall" filter.

### 3.4 Duplicate Filter
**Purpose:** Create a perfect clone of an existing parameter filter, preserving all categories and rules.
**Procedure:**
1. Pick the view containing the source filter.
2. Select the **Source Filter**.
3. Enter a **New Name** for the duplicate.
**Result:** The script clones the filter and automatically preserves its graphic overrides.

### 3.5 Reset Filters
**Purpose:** Clean up views by removing all graphic overrides from selected filters.
**Procedure:**
1. Select the target view or template.
2. Pick the filters to be cleared.
**Result:** Filters return to their default appearance while remaining in the view.

---

## Chapter 4: Usage Tips
- **Template Focus:** Always perform bulk updates on **View Templates** to ensure changes propagate throughout the project.
- **Selective Overrides:** Use *Copy Specific Overrides* to update styles without overwriting existing transparency or halftone settings.
- **Version Control:** Ensure you are using version 1.1+ of the scripts for the most stable performance.

---

## Chapter 5: Examples
- **Standardization:** Copy all overrides from a "Window Master" filter to all other window-related filters in a plan view.
- **Coordination:** Use *Change Colors* to highlight all "MEP Clash" filters in bright yellow during a coordination meeting.
- **Cleanup:** Reset all overrides in a "Drafting View" before exporting to DWG.

---

## Chapter 6: Revision History
| Version | Date | Author | Description |
| :--- | :--- | :--- | :--- |
| 1.0 | 2025-08-17 | PRADUL P | Initial documentation for pyRevit Filter Overrides Toolkit. |
| 1.1 | 2025-09-07 | PRADUL P | Added detailed step-by-step procedures and examples. |
| 1.2 | 2026-05-10 | PRADUL P | **Major Update**: Renamed tab to `FilterOverride`, restructured tools into the `Manage` stack, and optimized tool workflows. |

---
*Developed with ❤️ for BIM Efficiency.*
