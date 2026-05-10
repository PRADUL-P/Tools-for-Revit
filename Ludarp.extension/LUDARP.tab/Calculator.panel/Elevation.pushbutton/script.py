# -*- coding: utf-8 -*-
"""
Elevation Calculator — robust extraction + Convert / Copy / Go Back UI
Copies numeric only. Handles Levels, SpotDimensions, Dimensions, elements with LocationPoint,
and fallback to pick-point. After Convert shows: Copy | Go Back | Close.
"""
import math
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import (
    Level, LocationPoint, SpotDimension, Dimension, BuiltInParameter,
    SpecTypeId, UnitTypeId
)
from Autodesk.Revit.Exceptions import OperationCanceledException
from Autodesk.Revit.UI.Selection import ObjectType

# ---------- helpers ----------
def detect_project_unit(doc):
    try:
        fmt = doc.GetUnits().GetFormatOptions(SpecTypeId.Length)
        uid = fmt.GetUnitTypeId()
        if uid == UnitTypeId.Meters: return "m"
        if uid == UnitTypeId.Centimeters: return "cm"
        if uid == UnitTypeId.Millimeters: return "mm"
        if uid in (UnitTypeId.Feet, UnitTypeId.FeetFractionalInches): return "ft"
    except:
        pass
    return "cm"

def from_feet(value_feet, unit):
    if unit == "ft": return value_feet
    if unit == "m": return value_feet * 0.3048
    if unit == "cm": return value_feet * 30.48
    if unit == "mm": return value_feet * 304.8
    return value_feet

def safe_pick_object(uidoc, prompt="Pick element"):
    try:
        return uidoc.Selection.PickObject(ObjectType.Element, prompt)
    except OperationCanceledException:
        return None
    except Exception as e:
        forms.alert("Selection error:\n{}".format(e), title="Selection error")
        return None

def safe_pick_point(uidoc, prompt="Pick point"):
    try:
        return uidoc.Selection.PickPoint(prompt)
    except OperationCanceledException:
        return None
    except Exception as e:
        forms.alert("Point pick error:\n{}".format(e), title="Selection error")
        return None

def format_num(v, dec=6):
    s = ("{:.%df}" % dec).format(v)
    return s.rstrip("0").rstrip(".") if "." in s else s

# Robust extraction: try many sensible fallbacks
def extract_elevation(doc, reference):
    try:
        el = doc.GetElement(reference)
    except Exception:
        return None

    # Level
    if isinstance(el, Level):
        return el.Elevation

    # SpotDimension (origin)
    if isinstance(el, SpotDimension):
        try:
            if hasattr(el, "Origin"):
                return el.Origin.Z
        except:
            pass
        # some SpotDimension expose value parameter
        try:
            p = el.get_Parameter(BuiltInParameter.DIM_VALUE_LENGTH)
            if p: return p.AsDouble()
        except:
            pass

    # Dimension (text/linear dimension): try segment value(s)
    if isinstance(el, Dimension):
        try:
            if el.Value is not None:
                return el.Value
            segs = getattr(el, "Segments", None)
            if segs and segs.Size > 0:
                first = segs.get_Item(0)
                if first and getattr(first, "Value", None) is not None:
                    return first.Value
        except:
            pass

    # Any element with LocationPoint
    loc = getattr(el, "Location", None)
    if isinstance(loc, LocationPoint):
        try:
            return loc.Point.Z
        except:
            pass

    # Some annotations: try common elevation param names (best-effort)
    try:
        for pname in ("Elevation", "ELEVATION", "Level", "Elevation Value"):
            p = el.LookupParameter(pname) if hasattr(el, "LookupParameter") else None
            if p and p.StorageType.ToString() in ("Double","Double"):  # best-effort
                try:
                    val = p.AsDouble()
                    if val is not None:
                        return val
                except:
                    pass
    except:
        pass

    # Last fallback: ask user to pick a point
    pt = safe_pick_point(revit.uidoc, "Could not read element elevation. Pick a 3D point for fallback.")
    if pt:
        return pt.Z

    return None

# Conversion UI loop: after converting, show Copy | Go Back | Close
def conversion_and_copy_loop(result_ft):
    while True:
        tgt = forms.CommandSwitchWindow.show(["ft","m","cm","mm"], message="Convert result to:")
        if not tgt:
            return  # user cancelled conversion

        converted = from_feet(result_ft, tgt)
        conv_str = format_num(converted)

        # show converted and offer choices: Copy, Go Back (choose another unit), Close
        choice = forms.alert(
            "Converted: {val} {u}\n\nChoose:".format(val=conv_str, u=tgt),
            title="Converted",
            options=["Copy", "Go Back", "Close"]
        )

        if choice == "Copy":
            try:
                script.clipboard_copy(conv_str)
                forms.alert("Copied: {} {}".format(conv_str, tgt), title="Copied")
            except Exception:
                forms.alert("Could not copy value:\n{}".format(conv_str), title="Copy failed")
            return
        if choice == "Close":
            return
        # else "Go Back" -> loop again to choose new target unit

# ---------- main ----------
def main():
    doc = revit.doc
    uidoc = revit.uidoc

    # pick A and B robustly
    refA = safe_pick_object(uidoc, "Pick first elevation (Level / Spot / Dimension / element)")
    if not refA:
        return
    refB = safe_pick_object(uidoc, "Pick second elevation (Level / Spot / Dimension / element)")
    if not refB:
        return

    A_ft = extract_elevation(doc, refA)
    B_ft = extract_elevation(doc, refB)

    if A_ft is None or B_ft is None:
        forms.alert("Could not extract elevation from one or both picks.\nTry picking the actual element or use pick-point fallback.", title="Extraction failed")
        return

    # ask operation
    op = forms.CommandSwitchWindow.show(["A - B","A + B","A * B","A / B"], message="Choose operation:")
    if not op:
        return

    op_names = {"A - B":"Subtraction", "A + B":"Addition", "A * B":"Multiplication", "A / B":"Division"}
    opname = op_names.get(op, "")

    # compute safely
    try:
        if op == "A - B":
            res_ft = A_ft - B_ft
        elif op == "A + B":
            res_ft = A_ft + B_ft
        elif op == "A * B":
            res_ft = A_ft * B_ft
        else:
            if abs(B_ft) < 1e-9:
                forms.alert("Cannot divide by zero.", title="Error")
                return
            res_ft = A_ft / B_ft
    except Exception as e:
        forms.alert("Math error:\n{}".format(e), title="Error")
        return

    # display with unit and operation text and show Convert / Copy / Close
    unit = detect_project_unit(doc)
    A_u = from_feet(A_ft, unit); B_u = from_feet(B_ft, unit); R_u = from_feet(res_ft, unit)
    msg = (
        "Mode: Elevation\n"
        "Operation: {op} ({opname})\n"
        "Detected Unit: {u}\n\n"
        "A: {a:.4f} {u}\n"
        "B: {b:.4f} {u}\n\n"
        "Result: {r:.4f} {u}"
    ).format(op=op, opname=opname, u=unit, a=A_u, b=B_u, r=R_u)

    choice = forms.alert(msg + "\n\nChoose action:", title="Elevation Result", options=["Convert", "Copy Result", "Close"])

    if choice == "Copy Result":
        # copy numeric only
        num = format_num(R_u)
        try:
            script.clipboard_copy(num)
            forms.alert("Copied: {} {}".format(num, unit), title="Copied")
        except Exception:
            forms.alert("Could not copy value:\n{}".format(num), title="Copy failed")
        return

    if choice == "Convert":
        conversion_and_copy_loop(res_ft)
        return

    # Close -> do nothing
    return

if __name__ == "__main__":
    main()
