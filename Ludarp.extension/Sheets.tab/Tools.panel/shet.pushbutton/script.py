from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
import re

doc = revit.doc

# --------------------------
# Select the sheet
# --------------------------
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
sheet_names = [s.Name for s in sheets]

selected_sheet_name = forms.SelectFromList.show(
    sheet_names, title="Select a Sheet", multiselect=False
)

if not selected_sheet_name:
    forms.alert("No sheet selected. Exiting script.", title="Cancelled")
    script.exit()

sheet = next(s for s in sheets if s.Name == selected_sheet_name)

# --------------------------
# Collect viewports
# --------------------------
viewport_ids = sheet.GetAllViewports()
viewports = [doc.GetElement(vp_id) for vp_id in viewport_ids]

if not viewports:
    forms.alert("No views on this sheet.", title="Error")
    script.exit()

# --------------------------
# Ask user to pick rectangle boundary
# --------------------------
forms.alert("Pick the bottom-left corner of the boundary rectangle.", title="Instruction")
bottom_left = revit.uidoc.Selection.PickPoint("Pick bottom-left corner")

forms.alert("Pick the top-right corner of the boundary rectangle.", title="Instruction")
top_right = revit.uidoc.Selection.PickPoint("Pick top-right corner")

rect_width = top_right.X - bottom_left.X
rect_height = top_right.Y - bottom_left.Y
x_start = bottom_left.X
y_start_top = top_right.Y  # top Y for top-down arrangement

# --------------------------
# Ask user for spacing between views
# --------------------------
h_spacing_cm = forms.ask_for_string("Enter horizontal spacing between views (cm):", "5")
v_spacing_cm = forms.ask_for_string("Enter vertical spacing between views (cm):", "5")

try:
    h_spacing = float(h_spacing_cm) / 30.48
    v_spacing = float(v_spacing_cm) / 30.48
except:
    forms.alert("Invalid spacing input.", title="Error")
    script.exit()

# --------------------------
# Sort viewports by section number in name
# --------------------------
def get_sort_key(vp):
    name = doc.GetElement(vp.ViewId).Name
    match = re.search(r'(\d+)', name)
    return int(match.group(1)) if match else float('inf')

viewports.sort(key=get_sort_key)

# --------------------------
# Compute view sizes
# --------------------------
view_sizes = []
for vp in viewports:
    bb = vp.GetBoxOutline()
    dx = bb.MaximumPoint.X - bb.MinimumPoint.X
    dy = bb.MaximumPoint.Y - bb.MinimumPoint.Y
    view_sizes.append((dx, dy))

max_view_width = max(dx for dx, dy in view_sizes)
max_view_height = max(dy for dx, dy in view_sizes)

# --------------------------
# Determine columns and rows for grid
# --------------------------
x_spacing = max_view_width + h_spacing
y_spacing = max_view_height + v_spacing

cols = int(rect_width // x_spacing)
cols = max(1, cols)

rows_needed = (len(viewports) + cols - 1) // cols  # ceiling division

# --------------------------
# Arrange views in grid
# --------------------------
t = None
try:
    t = Transaction(doc, "Arrange Views in Grid with Spacing")
    t.Start()

    for idx, vp in enumerate(viewports):
        row = idx // cols
        col = idx % cols

        x = x_start + col * x_spacing
        y = y_start_top - row * y_spacing  # top-down

        target_position = XYZ(x, y, 0)
        translation = target_position - vp.GetBoxCenter()

        ElementTransformUtils.MoveElement(doc, vp.Id, translation)

    t.Commit()
    forms.alert("Views arranged in grid with specified spacing!", title="Success")

except Exception as e:
    if t and t.HasStarted():
        t.RollBack()
    forms.alert("Error: " + str(e), title="Failed")
