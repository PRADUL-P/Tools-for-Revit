# 🎨 LUDARP PyRevit Toolkit
A powerful pyRevit extension designed to streamline the management of **View Filters**, **Graphic Overrides**, **Numeric Calculations**, **Levels & Grids**, and **Multi-Discipline Views**. This toolkit provides standardized workflows for duplicating, synchronizing, and bulk-editing Revit data, complete with ISO 19650 naming standards and calculation history logging.

---

## ✨ Key Features

- **📂 Smart Categorization**: All view selection menus are automatically grouped by category (e.g., Floor Plans, Elevations, 3D Views) for rapid navigation.
- **🏷️ Clean Naming**: Automatically converts technical `ThreeD` labels to clean `3D` tags in the UI.
- **🔢 Natural Alphanumeric Sorting**: Intelligent view sorting handles numerical sequences properly (Level 1, Level 2 ... Level 9, Level 10) instead of alphabetical sorting.
- **🌐 ISO 19650 Compliance**: Standardized naming presets for automated project-, discipline-, level-, and type-coded views.
- **📏 Automated Level & Grid Generation**: Create multiple building levels with uniform or custom elevation offsets, and rename grids based on physical geometry (X/Y coordinates).
- **⚡ Bulk Operations**: Update multiple filters, views, levels, and grids simultaneously, saving hours of manual work.
- **📊 Calculation Logging**: Automatically logs all calculations to a temporary file for fast review, clipboard copies, and CSV exporting.

---

## 🛠️ Tool Guide

### 📂 FilterOverride Panel

#### 🔄 Copy Between Views
*Copy Filters and Overrides effortlessly.*
- **Step 1:** Pick the **SOURCE** View or Template.
- **Step 2:** Select one or more **TARGET** Views or Templates (using the categorized picker).
- **Step 3:** Choose exactly which filters to copy.
- **Features:** Adds missing filters, synchronizes colors/lines/patterns, and retains visibility states.

#### 🎯 Copy Specific Overrides
*Granular control over filter properties.*
- **Step 1:** Pick the **TARGET** View/Template.
- **Step 2:** Pick the **SOURCE** Filter (the style you want to copy).
- **Step 3:** Select one or more **TARGET** Filters to receive those styles.
- **Step 4:** Choose what to copy (Lines, Fills, Transparency, etc.).

---

### ⚙️ Management Stack (FilterOverride)

#### 🎨 Change Colors
*Bulk update filter graphics in seconds.*
- **Step 1:** Pick the **TARGET** View or Template.
- **Step 2:** Select the Filter(s) to modify.
- **Step 3:** Choose properties to override (Fills or Lines).
- **Step 4:** Pick a new color and fill pattern.

#### 📋 Duplicate Filter
*Clone parameter filters with a single click.*
- **Step 1:** Pick the View/Template containing the filter.
- **Step 2:** Pick the Filter to duplicate.
- **Step 3:** Enter the new name.
- **Result:** Automatically preserves all graphic overrides from the original!

#### 🧹 Reset Filters
*Clean up your views.*
- **Step 1:** Pick the View or Template to clean.
- **Step 2:** Select the Filter(s) to reset.
- **Result:** Clears all overrides, returning filters to default appearance.

---

### 🧮 Calculator Panel

#### 📐 Calculator
*Extract and convert numeric data in seconds.*
- **Features:** Supports Levels, Dimensions, Spot Dimensions, and Pick-Points. Includes unit conversion, automatic calculation logging, and clipboard support.

#### 📊 Calc History
*Review previous calculation logs and export data.*
- **Features:** Accesses the temporary log (`%TEMP%\calculator_history.json`) to display past calculations. Includes copying previous results to the clipboard, wiping the history, and exporting the calculation log to a structured CSV file with separate element and value columns.

---

### 📏 Levels & Grids Panel (New in v2.0)

#### 📐 Level Creator
*Batch create multiple levels from a reference base level.*
- **Features:** Uniform spacing or custom elevation offsets per level, interactive elevation preview in millimeters, auto-naming with customizable prefix/suffix, and elevation sorting.

#### 🔤 Grid Rename
*Renumber and rename structural/architectural grids automatically.*
- **Features:** Geometric directional sorting (Left to Right, Top to Bottom, Auto-detect), custom prefix/starting number, and 2-pass transactions to avoid Revit duplicate grid name errors.

---

### 👁️ Views Panel (New in v2.0)

#### 🏗️ Views Generator
*Generate multi-discipline floor and ceiling plans simultaneously.*
- **Features:** Select levels and view types for Architecture, Structure, Mechanical, Electrical, Plumbing, and Coordination. Includes 6 naming presets, including ISO 19650 compliant format (`[Project]-[Role]-[Level]-[Type]-[Seq]`).

#### ✏️ Views Renamer
*Interactive control center for batch renaming views.*
- **Features:** Live filtering by discipline and view type, human natural alphanumeric sorting (Level 1, 2, 3... 10), ISO 19650 automated and custom overrides, pattern matching, and search filtering.

---

## 🔹 Installation Steps

1. Download and extract the repository into your pyRevit extensions folder:
   `C:\Users\username\AppData\Roaming\pyRevit-Master\extensions`
2. Open Revit and go to **pyRevit > Reload**.
3. You should now see the **LUDARP** tab in your ribbon.

---

## 📖 Documentation
Detailed documentation and video guides are available here: [Google Docs](https://docs.google.com/document/d/1nRQzLRm3OhiO2Sk9U9_LbsX1GeMMbyRr5TSLWfxd8Bk/edit?usp=sharing)

---

## 👤 Author Information
- **Author:** PRADUL P
- **Version:** 2.0
- **Platform:** pyRevit / Revit API
- **Last Updated:** 2026-11-02

---
*Developed with ❤️ for BIM Efficiency.*
