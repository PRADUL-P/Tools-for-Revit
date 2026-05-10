# 📘 LUDARP Filter Override & Calculator Toolkit

**Author:** PRADUL P  
**Date:** 2026-05-10  
**Version:** 1.5  

---

## 1. Introduction
This toolkit provides a professional suite of pyRevit scripts to manage, synchronize, duplicate, and reset Revit filter overrides efficiently. It also includes a versatile Calculator for extracting and converting numeric data from Revit elements. It empowers users to maintain rigorous graphic standards, optimize view management, and ensure template accuracy across complex project environments.

---

## 2. Toolbar Overview
The scripts are organized under the **LUDARP** tab in the pyRevit ribbon. The toolbar is divided into the **FilterOverride** and **Calculator** panels, with a specialized **Manage** stack.

| Tool Name | Description |
| :--- | :--- |
| **Copy Between** | Synchronize filters/overrides between source and multiple target views. |
| **Copy Overrides** | Granularly copy specific properties (Lines, Fills, etc.) from one filter to another. |
| **Manage: Change Colors** | Bulk update colors and fill patterns for multiple filters. |
| **Manage: Duplicate** | Clone parameter filters along with their categories and rules. |
| **Manage: Reset** | Clear all overrides to return filters to project default settings. |
| **Calculator: Calculator** | Extract and convert numeric data from levels, dimensions, or points. |

---

## 3. Scripts and Procedures

### 3.1 Change Colors
**Purpose:** Bulk update colors and fill patterns of filters in a view or template.  
**Procedure:**
1. Select the target view or template.
2. Pick filters to modify.
3. Choose properties to override: **Fills** or **Lines**.
4. Select a new color via the Windows Color Picker.
5. Pick a new fill pattern (if modifying fills).  
**Example:** Change Wall foreground fill to "Solid Red" and Door cut lines to "Black" in the *First Floor Plan*.

### 3.2 Copy Between Views
**Purpose:** Transfer selected filters and their overrides from a source view to multiple targets.  
**Procedure:**
1. Select the **Source** view or template.
2. Select one or more **Target** views/templates.
3. Choose exactly which filters to copy.  
**Example:** Copy the "Doors_Fire_Rating" filter overrides from the *Ground Floor* template to the *Second Floor* and *Roof Plan* views.

### 3.3 Copy Specific Overrides
**Purpose:** Transfer specific graphic properties (Lines, Fills, Transparency) from a "Source" filter to one or more "Target" filters.  
**Procedure:**
1. Pick the **Target View**.
2. Select the **Source Filter** (the reference style).
3. Select **Target Filters** (the receivers).
4. Select properties to copy: *Projection Lines/Fills, Cut Lines/Fills, Transparency, Halftone, etc.*  
**Example:** Copy only the **Projection Fill** (color and pattern) from the "Structural Walls" filter to the "Architecture Walls" filter.

### 3.4 Duplicate Filter
**Purpose:** Create a perfect clone of an existing parameter filter, preserving all categories and rules.  
**Procedure:**
1. Pick the view containing the source filter.
2. Select the **Source Filter**.
3. Enter a **New Name** for the duplicate.  
**Example:** Duplicate the "Wall Hatch_Global" filter as "Wall Hatch_Zonal_A" in the *General Arrangement* template.

### 3.5 Reset Filters
**Purpose:** Clean up views by removing all graphic overrides from selected filters.  
**Procedure:**
1. Select the target view or template.
2. Pick the filters to be cleared.  
**Example:** Reset the "Door_Highlight" and "Furniture_Override" filters in the *Presentation View*.

### 3.6 Calculator
**Purpose:** Extract numeric data from Revit elements (Levels, Spot Dimensions, Dimensions, etc.) or pick-points, with built-in unit conversion.  
**Procedure:**
1. Pick a **Level**, **Dimension**, **Spot Dimension**, or **Physical Point** in the model.
2. View the extracted value in the popup.
3. Select **Copy** to save the value to clipboard or **Convert** to change units.  
**Example:** Extract a dimension value or a top-of-footing elevation and copy it directly into a coordination spreadsheet.

---

## 4. Usage Tips
- **Template Focus:** Always perform bulk updates on **View Templates** to ensure changes propagate throughout the project.
- **Selective Overrides:** Use *Copy Specific Overrides* to update styles without overwriting existing transparency or halftone settings.
- **Reloading:** After updating the extension, click **pyRevit > Reload** to refresh the ribbon icons and titles.

---

## 5. Revision History
- **1.0 (2025-08-17):** Initial documentation.
- **1.1 (2025-09-07):** Added detailed step-by-step procedures and examples.
- **1.2 (2026-05-10):** Renamed tab to **FilterOverride** and restructured tools into the **Manage** stack.
- **1.5 (2026-05-10):** Major Update: Renamed Tab to **LUDARP**, added the **Calculator** tool, and added detailed internal code documentation.

---
*Developed with ❤️ for BIM Efficiency.*
