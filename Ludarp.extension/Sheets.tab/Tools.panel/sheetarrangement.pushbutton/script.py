from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script

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
# Collect all viewports on the sheet
# --------------------------
viewport_ids = sheet.GetAllViewports()
viewports = [doc.GetElement(vp_id) for vp_id in viewport_ids]

# Sort viewports by view name
viewports.sort(key=lambda vp: doc.GetElement(vp.ViewId).Name)

# --------------------------
# Define arrangement parameters
# --------------------------
x_start = 0.5
y_start = 0.5
x_spacing = 5
y_spacing = 5
max_per_row = 3

# --------------------------
# Start transaction and arrange views
# --------------------------
t = None
try:
    t = Transaction(doc, "Arrange Views on Sheet")
    t.Start()

    for idx, vp in enumerate(viewports):
        row = idx // max_per_row
        col = idx % max_per_row

        # Calculate target position
        x = x_start + col * x_spacing
        y = y_start + row * y_spacing

        target_position = XYZ(x, y, 0)

        # Move viewport using ElementTransformUtils
        ElementTransformUtils.MoveElement(doc, vp.Id, target_position - vp.GetBoxCenter())

    t.Commit()
    forms.alert("Views have been arranged automatically!", title="Success")

except Exception as e:
    if t and t.HasStarted():
        t.RollBack()
    forms.alert("Error: " + str(e), title="Failed")
