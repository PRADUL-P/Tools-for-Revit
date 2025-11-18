# -*- coding: utf-8 -*-
# Slope & Level Tool (Click points & place text)
# Works in any view where you can pick points.
# Modes:
#   1) Slope between A & C
#   2) Level at B along line A–C

from pyrevit import revit, DB, UI, forms, script

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()
output.close_others()

# ---------- Helpers ----------

FT_TO_M = 0.3048


def ft_to_m(v):
    return v * FT_TO_M


def get_xy_vector(a, b):
    """Return XY-only vector from A to B (Z = 0)."""
    return DB.XYZ(b.X - a.X, b.Y - a.Y, 0.0)


def get_length_xy(a, b):
    """Horizontal distance in feet between A and B."""
    v = get_xy_vector(a, b)
    return v.GetLength()


def format_m(v):
    return "{:.3f}".format(ft_to_m(v))


def format_level_m(z_ft):
    return "{:.3f}".format(ft_to_m(z_ft))


def create_text_note(view, point, text):
    """Create a text note in the active view."""
    tntype_id = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType)
    # Reuse Z from view point
    return DB.TextNote.Create(doc, view.Id, point, text, tntype_id)


# ---------- UI: Mode selection ----------

mode = forms.SelectFromList.show(
    ["Slope between A & C", "Level at B (A–B–C)"],
    title="Slope & Level Tool",
    button_name="OK",
    multiselect=False
)

if not mode:
    script.exit()

view = doc.ActiveView

# ---------- Main Logic ----------

# Ask user for points depending on mode
try:
    if mode == "Slope between A & C":
        forms.alert("Pick Point A", title="Step 1", warn_icon=False)
        refA = uidoc.Selection.PickPoint("Pick point A")
        forms.alert("Pick Point C", title="Step 2", warn_icon=False)
        refC = uidoc.Selection.PickPoint("Pick point C")

        A = refA
        C = refC
        B = None

    elif mode == "Level at B (A–B–C)":
        forms.alert("Pick Point A", title="Step 1", warn_icon=False)
        refA = uidoc.Selection.PickPoint("Pick point A")
        forms.alert("Pick Point C", title="Step 2", warn_icon=False)
        refC = uidoc.Selection.PickPoint("Pick point C")
        forms.alert("Pick Point B (location where you need level)", title="Step 3", warn_icon=False)
        refB = uidoc.Selection.PickPoint("Pick point B")

        A = refA
        C = refC
        B = refB

    else:
        script.exit()

except Exception:
    forms.alert("Selection cancelled.", title="Cancelled")
    script.exit()

# ---------- Calculations common: slope A–C ----------

# Distances (horizontal) in feet
DAC_ft = get_length_xy(A, C)
if DAC_ft == 0:
    forms.alert("Points A and C are at the same location (distance = 0).", title="Error")
    script.exit()

# Height difference (in feet)
dZ_ft = C.Z - A.Z

slope = dZ_ft / DAC_ft              # in ft/ft (same as m/m)
slope_percent = slope * 100.0

# Slope ratio 1 in X
slope_ratio = None
if abs(slope) > 1e-9:
    slope_ratio = abs(1.0 / slope)

# ---------- Mode 1: Slope between A & C ----------

if mode == "Slope between A & C":
    # Mid point for note
    mid = DB.XYZ(
        (A.X + C.X) / 2.0,
        (A.Y + C.Y) / 2.0,
        (A.Z + C.Z) / 2.0
    )

    text_lines = []
    text_lines.append("Slope A–C")
    text_lines.append("ZA = {} m".format(format_level_m(A.Z)))
    text_lines.append("ZC = {} m".format(format_level_m(C.Z)))
    text_lines.append("AC = {} m".format(format_m(DAC_ft)))
    text_lines.append("Slope = {:.3f} %".format(slope_percent))
    if slope_ratio:
        text_lines.append("Slope = 1 in {:.2f}".format(slope_ratio))
    if slope > 0:
        text_lines.append("(Rising A → C)")
    elif slope < 0:
        text_lines.append("(Falling A → C)")
    else:
        text_lines.append("(Flat)")

    note_text = "\n".join(text_lines)

    # Create text note
    t = DB.Transaction(doc, "Create Slope Text")
    t.Start()
    create_text_note(view, mid, note_text)
    t.Commit()

    # Also show in pyRevit output
    output.print_md("## Slope between A & C")
    output.print_md("- ZA: `{}` m".format(format_level_m(A.Z)))
    output.print_md("- ZC: `{}` m".format(format_level_m(C.Z)))
    output.print_md("- AC: `{}` m".format(format_m(DAC_ft)))
    output.print_md("- Slope: `{:.5f}` m/m".format(slope))
    output.print_md("- Slope: `{:.3f}` %".format(slope_percent))
    if slope_ratio:
        output.print_md("- Slope: `1 in {:.2f}`".format(slope_ratio))


# ---------- Mode 2: Level at B along A–C ----------

elif mode == "Level at B (A–B–C)":
    # Vector AC and AB in XY
    AC_xy = get_xy_vector(A, C)
    AB_xy = get_xy_vector(A, B)

    AC_len = AC_xy.GetLength()
    if AC_len == 0:
        forms.alert("Points A and C are at the same location (distance = 0).", title="Error")
        script.exit()

    # Unit vector along AC
    AC_unit = DB.XYZ(AC_xy.X / AC_len, AC_xy.Y / AC_len, 0.0)

    # Projection of AB on AC -> distance along AC (DAB) in feet
    DAB_ft = AB_xy.X * AC_unit.X + AB_xy.Y * AC_unit.Y

    # Clamp or warn if B is outside segment A–C
    if DAB_ft < 0 or DAB_ft > AC_len:
        forms.alert(
            "Point B is not between A and C along the line.\n"
            "Calculation will still use projected distance.",
            title="Warning",
            warn_icon=True
        )

    # Level at B (design level along AC)
    ZB_ft = A.Z + slope * DAB_ft
    DBC_ft = AC_len - DAB_ft

    text_lines = []
    text_lines.append("Level at B (along A–C)")
    text_lines.append("ZA = {} m".format(format_level_m(A.Z)))
    text_lines.append("ZC = {} m".format(format_level_m(C.Z)))
    text_lines.append("AC = {} m".format(format_m(AC_len)))
    text_lines.append("AB = {} m".format(format_m(DAB_ft)))
    text_lines.append("BC = {} m".format(format_m(DBC_ft)))
    text_lines.append("ZB = {} m".format(format_level_m(ZB_ft)))
    text_lines.append("Slope A–C = {:.3f} %".format(slope_percent))
    if slope_ratio:
        text_lines.append("Slope = 1 in {:.2f}".format(slope_ratio))

    note_text = "\n".join(text_lines)

    # Place note at B point
    t = DB.Transaction(doc, "Create Level at B Text")
    t.Start()
    create_text_note(view, B, note_text)
    t.Commit()

    # Also show in pyRevit output
    output.print_md("## Level at B (along A–C)")
    output.print_md("- ZA (A): `{}` m".format(format_level_m(A.Z)))
    output.print_md("- ZC (C): `{}` m".format(format_level_m(C.Z)))
    output.print_md("- AC: `{}` m".format(format_m(AC_len)))
    output.print_md("- AB (proj): `{}` m".format(format_m(DAB_ft)))
    output.print_md("- BC: `{}` m".format(format_m(DBC_ft)))
    output.print_md("- ZB (design): `{}` m".format(format_level_m(ZB_ft)))
    output.print_md("- Slope A–C: `{:.5f}` m/m".format(slope))
    output.print_md("- Slope A–C: `{:.3f}` %".format(slope_percent))
    if slope_ratio:
        output.print_md("- Slope: `1 in {:.2f}`".format(slope_ratio))
