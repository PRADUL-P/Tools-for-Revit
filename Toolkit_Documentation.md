# 📘 pyRevit Filter Overrides Toolkit - Documentation

**Version:** 1.1  
**Author:** PRADUL P  
**Platform:** Revit 2022+ / pyRevit  

---

## 📝 Overview
The **Filter Overrides Toolkit** is a professional suite of pyRevit tools designed to automate the management of View Filters. This toolkit ensures graphic consistency across complex projects by providing advanced synchronization and bulk-editing capabilities.

---

## 🛠️ Tool Catalog & Guide

### 1. Copy Between Views
**Purpose:** Synchronize filter lists and their graphic overrides between different views or view templates.
- **Workflow:**
  1. Select **Source View/Template**.
  2. Select **Target View(s)/Template(s)**.
  3. Pick specific filters to transfer.
- **Key Feature:** Automatically adds missing filters to the target views.

### 2. Copy Specific Overrides
**Purpose:** Transfer granular graphic properties from a "master" filter to other filters in the same view.
- **Workflow:**
  1. Pick the **Target View**.
  2. Select the **Source Filter** (the "Look").
  3. Select **Target Filters** (the "Receivers").
  4. Choose properties to copy: *Lines, Fills, Transparency, etc.*

### 3. Change Colors (Bulk Update)
**Purpose:** Rapidly update the color and fill patterns for multiple filters simultaneously.
- **Workflow:**
  1. Pick **View/Template**.
  2. Select **Filters** to modify.
  3. Choose **Graphic Type** (Fills or Lines).
  4. Select **New Color** via the Windows Color Picker.

### 4. Duplicate Filter
**Purpose:** Create a exact clone of an existing Parameter Filter, including its rules and overrides.
- **Workflow:**
  1. Pick **Source Filter**.
  2. Define **New Name**.
- **Benefit:** Saves time by avoiding manual rule recreation.

### 5. Reset Filters
**Purpose:** Return filters to their default project appearance by clearing all overrides.
- **Workflow:**
  1. Select **View**.
  2. Pick **Filters** to reset.

---

## 🚀 Best Practices
- **Templates First:** Use the *Copy Between Views* tool on View Templates to push changes project-wide.
- **Color Coding:** Use *Change Colors* to quickly adjust visibility for coordination meetings.
- **Standardization:** Always use *Duplicate Filter* when creating variations of existing systems to ensure graphic alignment.

---
*Generated on 2026-05-10 | For BIM Efficiency.*
