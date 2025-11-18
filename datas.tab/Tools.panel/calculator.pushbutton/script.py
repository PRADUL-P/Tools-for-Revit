# -*- coding: utf-8 -*-
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType

import re

# ----------------------------------------------------------
# Unit helpers
# ----------------------------------------------------------
def detect_project_unit(doc):
    """Return 'm', 'cm', 'mm' or 'ft' based on project length units."""
    fmt = doc.GetUnits().GetFormatOptions(SpecTypeId.Length)
    unit_id = fmt.GetUnitTypeId()

    if unit_id == UnitTypeId.Meters:
        return "m"
    if unit_id == UnitTypeId.Centimeters:
        return "cm"
    if unit_id == UnitTypeId.Millimeters:
        return "mm"
    if unit_id in (UnitTypeId.Feet, UnitTypeId.FeetFractionalInches):
        return "ft"
    return "cm"


def from_feet(value_feet, unit):
    if unit == "ft":
        return value_feet
    if unit == "m":
        return value_feet * 0.3048
    if unit == "cm":
        return value_feet * 30.48
    if unit == "mm":
        return value_feet * 304.8
    return value_feet


def to_feet(value, unit):
    if unit == "ft":
        return value
    if unit == "m":
        return value / 0.3048
    if unit == "cm":
        return value / 30.48
    if unit == "mm":
        return value / 304.8
    return value


# ----------------------------------------------------------
# Mode selection
# ----------------------------------------------------------
def pick_value_mode():
    options = [
        "Elevation (Level / Spot Elevation)",
        "Coordinate (Spot XYZ)",
        "Dimension",
        "Pick 3D Point (Z only)",
    ]
    return forms.CommandSwitchWindow.show(
        options, message="What do you want to measure?"
    )


# ----------------------------------------------------------
# Extraction functions
# ----------------------------------------------------------
def extract_elevation(doc, ref):
    el = doc.GetElement(ref)

    # Level
    if isinstance(el, Level):
        return el.Elevation  # in feet

    # Spot Elevation (spot dimension used as elevation)
    from Autodesk.Revit.DB import SpotDimension
    if isinstance(el, SpotDimension):
        p = el.get_Parameter(BuiltInParameter.DIM_VALUE_LENGTH)
        if p:
            return p.AsDouble()

    # Any element with LocationPoint
    loc = getattr(el, "Location", None)
    if isinstance(loc, LocationPoint):
        return loc.Point.Z

    # Fallback: ask user for 3D point
    pt = revit.uidoc.Selection.PickPoint("No elevation found. Pick a 3D point.")
    return pt.Z


def extract_coordinate_point(doc, ref):
    """Return XYZ of a spot / element in feet."""
    el = doc.GetElement(ref)

    from Autodesk.Revit.DB import SpotDimension

    # True spot coordinate / spot dimension: use Origin
    if isinstance(el, SpotDimension):
        try:
            return el.Origin
        except:
            pass

    # Any element with LocationPoint
    loc = getattr(el, "Location", None)
    if isinstance(loc, LocationPoint):
        return loc.Point

    # Fallback: pick point
    pt = revit.uidoc.Selection.PickPoint("Pick 3D point for coordinate.")
    return pt


def extract_dimension(doc, ref):
    """Return dimension value in feet – robust for different dim types."""
    el = doc.GetElement(ref)

    if isinstance(el, Dimension):
        # Normal dimensions
        if el.Value is not None:
            return el.Value
        # Chained / segmented dimensions
        segs = el.Segments
        try:
            if segs and segs.Size > 0:
                first_seg = segs.get_Item(0)
                if first_seg and first_seg.Value is not None:
                    return first_seg.Value
        except:
            pass

    # Fallback: bounding box diagonal as some kind of length
    bbox = el.get_BoundingBox(None)
    if bbox:
        return bbox.Max.DistanceTo(bbox.Min)

    # Last fallback: point Z
    pt = revit.uidoc.Selection.PickPoint("No dimension value. Pick 3D point.")
    return pt.Z


def extract_point_z():
    pt = revit.uidoc.Selection.PickPoint("Pick 3D point")
    return pt.Z


# ----------------------------------------------------------
# Scalar result (elevation / dimension / 3D point)
# ----------------------------------------------------------
def show_scalar_result(A_ft, B_ft, result_ft, unit, mode_label):
    A_u = from_feet(A_ft, unit)
    B_u = from_feet(B_ft, unit)
    R_u = from_feet(result_ft, unit)
    R_cm = from_feet(result_ft, "cm")

    msg = (
        "Mode: {mode}\n"
        "Detected Project Unit: {unit}\n\n"
        "Value A: {a:.4f} {unit}\n"
        "Value B: {b:.4f} {unit}\n\n"
        "Result: {r:.4f} {unit}"
    ).format(mode=mode_label, unit=unit, a=A_u, b=B_u, r=R_u)

    if unit != "cm":
        msg += "\nResult: {0:.2f} cm".format(R_cm)

    choice = forms.alert(
        msg + "\n\nChoose action:",
        title="Value Calculator",
        options=["Convert", "Copy Result", "Close"],
    )

    if choice == "Copy Result":
        # Copy only the core result line, not the whole block
        result_text = "{mode} -> {val:.4f} {unit}".format(
            mode=mode_label, val=R_u, unit=unit
        )
        if unit != "cm":
            result_text += " ({cm:.2f} cm)".format(cm=R_cm)
        script.clipboard_copy(result_text)
    elif choice == "Convert":
        scalar_conversion_dialog(A_ft, B_ft, result_ft, unit, mode_label)


def scalar_conversion_dialog(A_ft, B_ft, result_ft, unit, mode_label):
    units = ["ft", "m", "cm", "mm"]
    target = forms.CommandSwitchWindow.show(units, message="Convert result to:")
    if not target:
        return

    orig_val = from_feet(result_ft, unit)
    new_val = from_feet(result_ft, target)

    conv_msg = (
        "Mode: {mode}\n\n"
        "Original Result: {orig:.4f} {unit}\n"
        "Converted: {conv:.4f} {tgt}"
    ).format(mode=mode_label, orig=orig_val, unit=unit, conv=new_val, tgt=target)

    choice = forms.alert(
        conv_msg + "\n\nChoose action:",
        title="Converted Result",
        options=["Copy & Close", "Back", "Close"],
    )

    if choice == "Copy & Close":
        short = "Converted {mode} -> {val:.4f} {tgt}".format(
            mode=mode_label, val=new_val, tgt=target
        )
        script.clipboard_copy(short)
        return
    elif choice == "Back":
        show_scalar_result(A_ft, B_ft, result_ft, unit, mode_label)
    else:
        return


# ----------------------------------------------------------
# Coordinate result (XYZ format)
# ----------------------------------------------------------
def show_coordinate_result(A_xyz, B_xyz, unit):
    Ax = from_feet(A_xyz.X, unit)
    Ay = from_feet(A_xyz.Y, unit)
    Az = from_feet(A_xyz.Z, unit)
    Bx = from_feet(B_xyz.X, unit)
    By = from_feet(B_xyz.Y, unit)
    Bz = from_feet(B_xyz.Z, unit)

    dx_ft = B_xyz.X - A_xyz.X
    dy_ft = B_xyz.Y - A_xyz.Y
    dz_ft = B_xyz.Z - A_xyz.Z

    dx = from_feet(dx_ft, unit)
    dy = from_feet(dy_ft, unit)
    dz = from_feet(dz_ft, unit)

    dist2d_ft = (dx_ft ** 2 + dy_ft ** 2) ** 0.5
    dist3d_ft = (dx_ft ** 2 + dy_ft ** 2 + dz_ft ** 2) ** 0.5
    dist2d_u = from_feet(dist2d_ft, unit)
    dist3d_u = from_feet(dist3d_ft, unit)
    dist2d_cm = from_feet(dist2d_ft, "cm")
    dist3d_cm = from_feet(dist3d_ft, "cm")

    msg = (
        "Mode: Coordinate (Spot XYZ)\n"
        "Detected Project Unit: {unit}\n\n"
        "Point A (X,Y,Z): ({Ax:.3f}, {Ay:.3f}, {Az:.3f}) {unit}\n"
        "Point B (X,Y,Z): ({Bx:.3f}, {By:.3f}, {Bz:.3f}) {unit}\n\n"
        "Δ(B - A):\n"
        "  dX: {dx:.3f} {unit}\n"
        "  dY: {dy:.3f} {unit}\n"
        "  dZ: {dz:.3f} {unit}\n\n"
        "Plan distance (2D): {d2:.3f} {unit}\n"
        "3D distance:        {d3:.3f} {unit}"
    ).format(
        unit=unit,
        Ax=Ax,
        Ay=Ay,
        Az=Az,
        Bx=Bx,
        By=By,
        Bz=Bz,
        dx=dx,
        dy=dy,
        dz=dz,
        d2=dist2d_u,
        d3=dist3d_u,
    )

    if unit != "cm":
        msg += "\n\nPlan distance: {0:.1f} cm\n3D distance:   {1:.1f} cm".format(
            dist2d_cm, dist3d_cm
        )

    choice = forms.alert(
        msg + "\n\nChoose action:",
        title="Coordinate Calculator",
        options=["Copy Summary", "Convert Unit", "Close"],
    )

    if choice == "Copy Summary":
        short = (
            "A({Ax:.3f},{Ay:.3f},{Az:.3f}) {u},  "
            "B({Bx:.3f},{By:.3f},{Bz:.3f}) {u},  "
            "dX={dx:.3f}, dY={dy:.3f}, dZ={dz:.3f},  "
            "2D={d2:.3f}{u}, 3D={d3:.3f}{u}"
        ).format(
            Ax=Ax,
            Ay=Ay,
            Az=Az,
            Bx=Bx,
            By=By,
            Bz=Bz,
            dx=dx,
            dy=dy,
            dz=dz,
            d2=dist2d_u,
            d3=dist3d_u,
            u=unit,
        )
        script.clipboard_copy(short)
    elif choice == "Convert Unit":
        coord_conversion_dialog(A_xyz, B_xyz, unit)


def coord_conversion_dialog(A_xyz, B_xyz, current_unit):
    units = ["ft", "m", "cm", "mm"]
    target = forms.CommandSwitchWindow.show(units, message="Convert coordinates to:")
    if not target:
        return
    show_coordinate_result(A_xyz, B_xyz, target)


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    doc = revit.doc
    uidoc = revit.uidoc

    mode = pick_value_mode()
    if not mode:
        return

    unit = detect_project_unit(doc)

    # Coordinate mode – only ΔXYZ and distances
    if "Coordinate" in mode:
        refA = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick first coordinate (Spot / element)"
        )
        refB = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick second coordinate (Spot / element)"
        )
        A_xyz = extract_coordinate_point(doc, refA)
        B_xyz = extract_coordinate_point(doc, refB)
        show_coordinate_result(A_xyz, B_xyz, unit)
        return

    # Scalar modes
    if "Elevation" in mode:
        refA = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick first elevation source"
        )
        A_ft = extract_elevation(doc, refA)
        refB = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick second elevation source"
        )
        B_ft = extract_elevation(doc, refB)
        mode_label = "Elevation"
    elif "Dimension" in mode:
        refA = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick first dimension element"
        )
        A_ft = extract_dimension(doc, refA)
        refB = uidoc.Selection.PickObject(
            ObjectType.Element, "Pick second dimension element"
        )
        B_ft = extract_dimension(doc, refB)
        mode_label = "Dimension"
    else:  # Pick 3D Point Z mode
        A_ft = extract_point_z()
        B_ft = extract_point_z()
        mode_label = "3D Point Z"

    op = forms.CommandSwitchWindow.show(
        ["A - B", "A + B", "A × B", "A ÷ B"], message="Choose operation:"
    )
    if not op:
        return

    if op == "A - B":
        result_ft = A_ft - B_ft
        mode_label += " | A - B"
    elif op == "A + B":
        result_ft = A_ft + B_ft
        mode_label += " | A + B"
    elif op == "A × B":
        result_ft = A_ft * B_ft
        mode_label += " | A × B"
    else:
        if abs(B_ft) < 1e-9:
            forms.alert("Cannot divide by zero.", title="Error")
            return
        result_ft = A_ft / B_ft
        mode_label += " | A ÷ B"

    show_scalar_result(A_ft, B_ft, result_ft, unit, mode_label)


if __name__ == "__main__":
    main()
