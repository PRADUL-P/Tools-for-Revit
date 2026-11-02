# 📘 LUDARP PyRevit Toolkit

**Author:** PRADUL P  
**Date:** 2026-11-02  
**Version:** 2.0  

---

## 1. Introduction
This toolkit provides a professional suite of pyRevit tools to manage, synchronize, duplicate, and reset Revit filter overrides efficiently. It features a versatile Calculator panel for extracting, calculating, logging, and converting numeric data, alongside powerful automation panels for Levels & Grids generation and Multi-Discipline Views management following international BIM standards (ISO 19650). It empowers users to maintain rigorous graphic standards, optimize view workflows, and ensure model quality across complex project environments.

---

## 2. Toolbar Overview
The tools are organized under the **LUDARP** tab in the pyRevit ribbon across four primary panels: **FilterOverride**, **Calculator**, **Levels & Grids**, and **Views**.

| Tool Name | Panel / Stack | Description |
| :--- | :--- | :--- |
| **Copy Between** | FilterOverride | Synchronize filters/overrides between source and multiple target views. |
| **Copy Overrides** | FilterOverride | Granularly copy specific properties (Lines, Fills, etc.) from one filter to another. |
| **Change Colors** | FilterOverride (Manage) | Bulk update colors and fill patterns for multiple filters. |
| **Duplicate** | FilterOverride (Manage) | Clone parameter filters along with their categories and rules. |
| **Reset** | FilterOverride (Manage) | Clear all overrides to return filters to project default settings. |
| **Calculator** | Calculator | Extract and convert numeric data from levels, dimensions, or points. |
| **Calc History** | Calculator | View recent calculation history, copy previous results, and export to CSV. |
| **Level Creator** | Levels & Grids | Batch create building levels with uniform or custom offsets and live elevation preview. |
| **Grid Rename** | Levels & Grids | Renumber structural/architectural grids based on geometric coordinates (X/Y). |
| **Views Generator** | Views | Generate floor and ceiling plans for Architecture, Structure, MEP, and Coordination. |
| **Views Renamer** | Views | Interactive view rename center with natural sorting, pattern rules, and ISO 19650. |

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
**Purpose:** Extract numeric data from Revit elements (Levels, Spot Dimensions, Dimensions, etc.) or pick-points, with built-in unit conversion and automatic history logging.  
**Procedure:**
1. Pick a **Level**, **Dimension**, **Spot Dimension**, or **Physical Point** in the model.
2. View the extracted value in the popup.
3. Select **Copy** to save the value to clipboard or **Convert** to change units.  
**Example:** Extract a dimension value or a top-of-footing elevation and copy it directly into a coordination spreadsheet.

### 3.7 Calc History
**Purpose:** View the history of recent calculations, copy previous results, clear the history log, or export the log to a CSV file.  
**Procedure:**
1. Click the **Calc History** button on the ribbon.
2. Review past calculation logs (stored in the system `%TEMP%` directory).
3. Select an entry and click **📋 Copy Result** to copy the result to your clipboard.
4. Click **📤 Export CSV** to export the calculation history to a CSV file with separate columns for element name and values.
5. Click **🧹 Clear All** to wipe the local log.  
**Example:** Export a list of all operations performed today to a CSV spreadsheet for logging or coordination documentation.

### 3.8 Level Creator
**Purpose:** Batch create multiple levels with uniform height intervals or custom elevations from a reference datum level.  
**Procedure:**
1. Select the **Reference Base Level** from the dropdown.
2. Choose between **Uniform Spacing** (specifying offset distance, count, and direction above/below) or **Custom per Level** (defining names and relative offsets).
3. Preview target elevations dynamically in millimeters.
4. Click **Create Levels** to generate all levels in a single transaction.  
**Example:** Generate Levels 02 through 15 with 3,500 mm floor-to-floor height above Level 01.

### 3.9 Grid Rename
**Purpose:** Directionally sort and rename structural and architectural grid lines in one pass.  
**Procedure:**
1. Pick the sorting direction: **Left to Right (X-axis)**, **Top to Bottom (Y-axis)**, or **Auto-Detect**.
2. Specify the **Prefix**, **Starting Index** (e.g. 1 or A), and optional padding.
3. Review the renumbering table in the live preview.
4. Click **Rename Grids** to execute a safe 2-pass transaction (preventing Revit duplicate grid name errors).  
**Example:** Renumber all horizontal grids from top to bottom as Grids A, B, C, D...

### 3.10 Views Generator
**Purpose:** Rapidly generate floor and ceiling plans for selected building levels across any combination of disciplines.  
**Procedure:**
1. Select target levels and plan types (Floor Plan, Ceiling Plan).
2. Choose target disciplines: **Architecture**, **Structure**, **Mechanical**, **Electrical**, **Plumbing**, **Coordination**.
3. Choose a naming convention preset (including **ISO 19650**: `[Project]-[Role]-[Level]-[Type]-[Seq]`).
4. Optionally customize prefixes, suffixes, or casing (UPPERCASE).
5. Click **Generate Views** to create all plans instantly.  
**Example:** Create Electrical and Mechanical ceiling plans for Levels 01 to 05 named per ISO 19650 standards.

### 3.11 Views Renamer
**Purpose:** Interactive control center for filtering, searching, natural-sorting, and batch-renaming project views.  
**Procedure:**
1. Filter views by discipline (Arch, Struct, MEP) or view type.
2. Select views with natural human sorting (ensuring Level 1, Level 2 ... Level 10 appear in numerical sequence).
3. Choose renaming mode: **ISO 19650** format (with auto-detected or custom level, type, role, and sequence codes), **Prefix/Suffix**, or **Find and Replace**.
4. Review changes in the live rename preview table before committing.
5. Click **Apply Renaming** to batch update view names.  
**Example:** Standardize all existing MEP views to ISO 19650 naming conventions with auto-detected roles and levels.

---

## 4. Installation Steps
1. Download and extract the repository into your pyRevit extensions folder:  
   `C:\Users\username\AppData\Roaming\pyRevit-Master\extensions`
2. Open Revit and go to **pyRevit > Reload**.
3. You should now see the **LUDARP** tab in your ribbon.

---

## 5. Usage Tips
- **Template Focus:** Always perform bulk updates on **View Templates** to ensure changes propagate throughout the project.
- **Selective Overrides:** Use *Copy Specific Overrides* to update styles without overwriting existing transparency or halftone settings.
- **Natural Sorting:** Use *Views Renamer* to organize views logically in numerical sequence rather than default alphabetical order.
- **Reloading:** After updating the extension, click **pyRevit > Reload** to refresh the ribbon icons and titles.

---

## 6. Revision History
- **1.0 (2025-08-17):** Initial documentation.
- **1.1 (2025-09-07):** Added detailed step-by-step procedures and examples.
- **1.2 (2026-05-10):** Renamed tab to **FilterOverride** and restructured tools into the **Manage** stack.
- **1.5 (2026-05-10):** Major Update: Renamed Tab to **LUDARP**, added the **Calculator** tool, and added detailed internal code documentation.
- **1.6 (2026-06-21):** Added the **Calc History** tool to log recent calculations and export them to CSV.
- **2.0 (2026-11-02):** Major Release: Added **Levels & Grids** panel (`Level Creator`, `Grid Rename`) and **Views** panel (`Views Generator`, `Views Renamer` with natural sorting and ISO 19650 naming standards).

---
*Developed with ❤️ for BIM Efficiency.*
