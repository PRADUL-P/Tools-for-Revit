# 🎨 LUDARP Filter Override & Calculator Tools
A powerful pyRevit extension designed to streamline the management of **View Filters**, **Graphic Overrides**, and **Numeric Calculations**. This toolkit provides a standardized workflow for duplicating, synchronizing, and bulk-editing Revit data.

---

## ✨ Key Features

- **📂 Smart Categorization**: All view selection menus are automatically grouped by category (e.g., Floor Plans, Elevations, 3D Views) for rapid navigation.
- **🏷️ Clean Naming**: Automatically converts technical `ThreeD` labels to clean `3D` tags in the UI.
- **🎭 Emoji-Enhanced UI**: Uses intuitive icons and emojis to help you distinguish between views, folders, and actions at a glance.
- **⚡ Bulk Operations**: Update multiple filters and multiple views simultaneously, saving hours of manual work.

---

## 🛠️ Tool Guide

### 📂 Primary Tools

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

### ⚙️ Management Stack

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
- **Features:** Supports Levels, Dimensions, Spot Dimensions, and Pick-Points. Includes unit conversion and clipboard support.

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
- **Version:** 1.5
- **Platform:** pyRevit / Revit API

---
*Developed with ❤️ for BIM Efficiency.*
