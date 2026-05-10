# -*- coding: utf-8 -*-
"""
📐 LUDARP Elevation Calculator v1.5
Robust extraction + Unit Conversion + Math Operations.
Handles Levels, Spot Dimensions, Dimensions, and Point-based elements.
"""
__title__ = "Elevation\nCalculator"
__author__ = "PRADUL P / Antigravity"

import math
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import (
    Level, LocationPoint, SpotDimension, Dimension, BuiltInParameter,
    SpecTypeId, UnitTypeId, UnitFormatUtils
)
from Autodesk.Revit.Exceptions import OperationCanceledException
from Autodesk.Revit.UI.Selection import ObjectType

# ---------- Configuration ----------
UNITS = {
    "m": {"label": "Meters", "id": UnitTypeId.Meters},
    "cm": {"label": "Centimeters", "id": UnitTypeId.Centimeters},
    "mm": {"label": "Millimeters", "id": UnitTypeId.Millimeters},
    "ft": {"label": "Feet", "id": UnitTypeId.Feet},
    "fi": {"label": "Fractional Inches", "id": UnitTypeId.FeetFractionalInches}
}

# ---------- Helpers ----------
def detect_project_unit(doc):
    try:
        units = doc.GetUnits()
        fmt = units.GetFormatOptions(SpecTypeId.Length)
        uid = fmt.GetUnitTypeId()
        
        if uid == UnitTypeId.Meters: return "m"
        if uid == UnitTypeId.Centimeters: return "cm"
        if uid == UnitTypeId.Millimeters: return "mm"
        if uid == UnitTypeId.Feet: return "ft"
        if uid == UnitTypeId.FeetFractionalInches: return "fi"
    except:
        pass
    return "m"

def convert_units(value_feet, target_unit):
    """Convert value from Internal Feet to target unit string."""
    if target_unit == "ft": return value_feet
    if target_unit == "m": return value_feet * 0.3048
    if target_unit == "cm": return value_feet * 30.48
    if target_unit == "mm": return value_feet * 304.8
    if target_unit == "fi": return value_feet # Formatting handles this
    return value_feet

def format_value(doc, value_feet, unit_key):
    """Format numeric value with Revit's unit formatter."""
    try:
        units = doc.GetUnits()
        uid = UNITS.get(unit_key, {}).get("id", UnitTypeId.Meters)
        return UnitFormatUtils.Format(units, SpecTypeId.Length, value_feet, False)
    except:
        return "{:.3f}".format(convert_units(value_feet, unit_key))

def safe_pick_object(uidoc, prompt="🖱️ Pick element"):
    try:
        return uidoc.Selection.PickObject(ObjectType.Element, prompt)
    except OperationCanceledException:
        return None
    except Exception as e:
        forms.alert("Selection error:\n{}".format(e), title="Selection Error")
        return None

def safe_pick_point(uidoc, prompt="📍 Pick point"):
    try:
        return uidoc.Selection.PickPoint(prompt)
    except OperationCanceledException:
        return None
    except Exception as e:
        forms.alert("Point pick error:\n{}".format(e), title="Selection Error")
        return None

# ---------- Extraction Logic ----------
def extract_elevation(doc, reference):
    try:
        el = doc.GetElement(reference)
    except:
        return None

    # 1. Levels
    if isinstance(el, Level):
        return el.Elevation

    # 2. Spot Dimensions
    if isinstance(el, SpotDimension):
        try:
            # Try to get the origin Z coordinate
            if hasattr(el, "Origin"):
                return el.Origin.Z
        except:
            pass
        # Fallback to parameter
        p = el.get_Parameter(BuiltInParameter.DIM_VALUE_LENGTH)
        if p: return p.AsDouble()

    # 3. Dimensions
    if isinstance(el, Dimension):
        try:
            if el.Value is not None:
                return el.Value
            # Try segments for multi-segment dimensions
            if hasattr(el, "Segments") and el.Segments.Size > 0:
                return el.Segments.get_Item(0).Value
        except:
            pass

    # 4. Elements with LocationPoint (Family Instances, etc.)
    loc = getattr(el, "Location", None)
    if isinstance(loc, LocationPoint):
        return loc.Point.Z

    # 5. Parameter Search (Common Elevation Params)
    params = ["Elevation", "Elevation from Level", "ELEVATION", "Offset"]
    for p_name in params:
        p = el.LookupParameter(p_name)
        if p and p.StorageType.ToString() == "Double":
            return p.AsDouble()

    # 6. Fallback: User Pick Point
    choice = forms.alert(
        "Could not auto-extract elevation from '{}'.\nWould you like to pick a manual point?".format(el.Name),
        options=["Yes, pick point", "No, cancel"],
        title="Extraction Fallback"
    )
    if choice == "Yes, pick point":
        pt = safe_pick_point(revit.uidoc, "📍 Pick a point to define elevation")
        if pt: return pt.Z

    return None

# ---------- UI Loops ----------
def conversion_loop(doc, value_feet):
    while True:
        options = {UNITS[k]["label"]: k for k in UNITS}
        choice = forms.SelectFromList.show(
            sorted(options.keys()), 
            title="🎯 Convert Result To", 
            multiselect=False
        )
        if not choice: return

        unit_key = options[choice]
        formatted = format_value(doc, value_feet, unit_key)
        
        res = forms.alert(
            "💎 Converted Value:\n\n{0}\n\nUnit: {1}".format(formatted, choice),
            title="Conversion Result",
            options=["📋 Copy Value", "🔄 Convert Again", "❌ Close"]
        )

        if res == "📋 Copy Value":
            script.clipboard_copy(formatted)
            forms.toast("Value copied to clipboard!")
            return
        if res == "❌ Close":
            return

# ---------- Main Execution ----------
def main():
    doc = revit.doc
    uidoc = revit.uidoc

    # Step 1: Pick Elevations
    refA = safe_pick_object(uidoc, "1️⃣ Pick First Element (Level/Spot/Dimension)")
    if not refA: return
    
    A_ft = extract_elevation(doc, refA)
    if A_ft is None: return

    refB = safe_pick_object(uidoc, "2️⃣ Pick Second Element (Level/Spot/Dimension)")
    if not refB: return
    
    B_ft = extract_elevation(doc, refB)
    if B_ft is None: return

    # Step 2: Math Operation
    ops = {
        "➕ Addition (A+B)": lambda a, b: a + b,
        "➖ Subtraction (A-B)": lambda a, b: a - b,
        "✖️ Multiplication (A*B)": lambda a, b: a * b,
        "➗ Division (A/B)": lambda a, b: a / b if abs(b) > 1e-9 else None
    }
    
    op_choice = forms.CommandSwitchWindow.show(sorted(ops.keys()), message="🛠️ Choose Operation:")
    if not op_choice: return

    res_ft = ops[op_choice](A_ft, B_ft)
    if res_ft is None:
        forms.alert("Error: Division by zero!", title="Math Error")
        return

    # Step 3: Display Results
    proj_unit = detect_project_unit(doc)
    A_fmt = format_value(doc, A_ft, proj_unit)
    B_fmt = format_value(doc, B_ft, proj_unit)
    R_fmt = format_value(doc, res_ft, proj_unit)

    msg = (
        "📊 Operation: {op}\n"
        "🏠 Detected Units: {u}\n\n"
        "🔹 A: {a}\n"
        "🔹 B: {b}\n\n"
        "✅ Result: {r}"
    ).format(op=op_choice, u=UNITS[proj_unit]["label"], a=A_fmt, b=B_fmt, r=R_fmt)

    final_choice = forms.alert(
        msg, 
        title="LUDARP Elevation Result", 
        options=["📋 Copy Result", "🎯 Convert Units", "❌ Close"]
    )

    if final_choice == "📋 Copy Result":
        script.clipboard_copy(R_fmt)
        forms.toast("Result copied!")
    elif final_choice == "🎯 Convert Units":
        conversion_loop(doc, res_ft)

if __name__ == "__main__":
    main()

