# -*- coding: utf-8 -*-
# pyRevit Script: Select Elements -> Pick Parameters -> Export HTML (Search + Sort + CSV/PDF)
# Works on IronPython (pyRevit). No f-strings used.
# Author: You + ChatGPT

import os
import tempfile
import webbrowser

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import Selection
from pyrevit import revit, forms, script

doc  = revit.doc
uidoc = revit.uidoc

# ---------------------------
# Helpers
# ---------------------------
def html_escape(val):
    """Minimal HTML escape for text."""
    if val is None:
        return ""
    s = unicode(val) if not isinstance(val, basestring) else val
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def get_param_value(doc, param):
    """Return a readable string value from a Parameter."""
    if not param:
        return ""
    st = param.StorageType
    try:
        # Prefer Revit's formatted value when available (units-aware)
        if st == StorageType.Double:
            v = param.AsValueString()
            if v:
                return v
            # fallback to raw double
            return "{:.3f}".format(float(param.AsDouble()))
        elif st == StorageType.Integer:
            # Some Ints are Yes/No in Revit
            v = param.AsValueString()
            if v:
                return v
            return str(param.AsInteger())
        elif st == StorageType.String:
            v = param.AsString()
            if v:
                return v
            v2 = param.AsValueString()
            return v2 if v2 else ""
        elif st == StorageType.ElementId:
            eid = param.AsElementId()
            if eid and eid.IntegerValue > 0:
                el = doc.GetElement(eid)
                if el:
                    # Prefer element Name if present
                    n = getattr(el, "Name", None)
                    return n if n else str(eid.IntegerValue)
            return ""
        else:
            # Unknown storage type
            v = param.AsValueString()
            return v if v else ""
    except:
        try:
            v = param.AsValueString()
            return v if v else ""
        except:
            return ""

def collect_param_names(elements):
    """Union of parameter names across the selected elements."""
    names = set()
    for el in elements:
        try:
            for p in el.Parameters:
                try:
                    nm = p.Definition.Name
                    if nm:
                        names.add(nm)
                except:
                    pass
        except:
            pass
    return sorted(list(names))

# ---------------------------
# 1) Let user select elements
# ---------------------------
try:
    refs = uidoc.Selection.PickObjects(Selection.ObjectType.Element, "Select elements (e.g. piles) to report")
except:
    forms.alert("No elements selected. Exiting.", exitscript=True)

elements = [doc.GetElement(r) for r in refs if doc.GetElement(r) is not None]
if not elements:
    forms.alert("No elements found from selection.", exitscript=True)

# ---------------------------
# 2) Ask which parameters to include
# ---------------------------
all_param_names = collect_param_names(elements)
if not all_param_names:
    forms.alert("No readable parameters found on the selected elements.", exitscript=True)

chosen_params = forms.SelectFromList.show(
    all_param_names,
    title="Select Parameters to Include",
    multiselect=True
)
if not chosen_params:
    forms.alert("No parameters chosen. Exiting.", exitscript=True)

# ---------------------------
# 3) Collect data (ID, X,Y,Z, chosen params)
# ---------------------------
rows = []  # each row: (id, x, y, z, [param values...])
for el in elements:
    # Coordinates (if element has a point location)
    x = y = z = None
    try:
        loc = el.Location
        if hasattr(loc, "Point") and loc.Point:
            pt = loc.Point
            x, y, z = float(pt.X), float(pt.Y), float(pt.Z)
    except:
        pass

    # Parameter values
    vals = []
    for pname in chosen_params:
        pv = ""
        try:
            p = el.LookupParameter(pname)
            pv = get_param_value(doc, p)
        except:
            pv = ""
        vals.append(pv)

    rows.append((el.Id.IntegerValue, x, y, z, vals))

# ---------------------------
# 4) Build HTML (search, sort, CSV/PDF)
# ---------------------------
# Dynamic column headers for the chosen parameters
param_header_cells = ""
# Sort indexes: 0:ID, 1:X, 2:Y, 3:Z, then params start at 4
for idx, pname in enumerate(chosen_params):
    sort_index = 4 + idx
    # Make param columns sortable too
    param_header_cells += "<th onclick=\"sortTable({0})\">{1}</th>".format(sort_index, html_escape(pname))

# Build table rows
html_rows = ""
for eid, x, y, z, vals in rows:
    # coords displayed as 3-decimals (blank if None)
    x_txt = "{:.3f}".format(float(x)) if x is not None else ""
    y_txt = "{:.3f}".format(float(y)) if y is not None else ""
    z_txt = "{:.3f}".format(float(z)) if z is not None else ""

    html_rows += "<tr>"
    html_rows += "<td>{}</td><td>{}</td><td>{}</td><td>{}</td>".format(eid, x_txt, y_txt, z_txt)
    for v in vals:
        html_rows += "<td>{}</td>".format(html_escape(v))
    html_rows += "</tr>\n"

html_head = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Selected Elements Report</title>
<style>
  body { font-family: Arial, sans-serif; padding: 20px; }
  h2 { color: #2c3e50; margin-top: 0; }
  #searchInput { margin: 6px 0 12px 0; padding: 6px; width: 50%; }
  button { margin: 6px 6px 12px 0; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; }
  .btn-csv { background: #2e7d32; color: #fff; }
  .btn-pdf { background: #1565c0; color: #fff; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
  th { cursor: pointer; background-color: #f2f2f2; }
  tr:nth-child(even) { background-color: #fafafa; }
</style>
</head>
<body>
<h2>Selected Elements Report</h2>
<input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search by ID, coordinates, or parameter values...">
<br>
<button class="btn-csv" onclick="downloadCSV()">Download CSV (Excel)</button>
<button class="btn-pdf" onclick="downloadPDF()">Download PDF</button>

<table id="coordTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Element ID</th>
      <th onclick="sortTable(1)">X</th>
      <th onclick="sortTable(2)">Y</th>
      <th onclick="sortTable(3)">Y</th>
    </tr>
  </thead>
  <tbody>
"""

# OOPS typo in header (Y twice). Fix: below we will replace the second header with Z via an update.
# Let's correct it immediately:
html_head = html_head.replace('>Y</th>\n    </tr>', '>Z</th>\n    </tr>')

# Insert parameter headers
# We need to add them into the header row; rebuild header properly to include params.
html_head = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Selected Elements Report</title>
<style>
  body { font-family: Arial, sans-serif; padding: 20px; }
  h2 { color: #2c3e50; margin-top: 0; }
  #searchInput { margin: 6px 0 12px 0; padding: 6px; width: 50%; }
  button { margin: 6px 6px 12px 0; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; }
  .btn-csv { background: #2e7d32; color: #fff; }
  .btn-pdf { background: #1565c0; color: #fff; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
  th { cursor: pointer; background-color: #f2f2f2; }
  tr:nth-child(even) { background-color: #fafafa; }
</style>
</head>
<body>
<h2>Selected Elements Report</h2>
<input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search by ID, coordinates, or parameter values...">
<br>
<button class="btn-csv" onclick="downloadCSV()">Download CSV (Excel)</button>
<button class="btn-pdf" onclick="downloadPDF()">Download PDF</button>

<table id="coordTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Element ID</th>
      <th onclick="sortTable(1)">X</th>
      <th onclick="sortTable(2)">Y</th>
      <th onclick="sortTable(3)">Z</th>"""

# append param headers
html_head += param_header_cells
html_head += """
    </tr>
  </thead>
  <tbody>
"""

html_tail = """
  </tbody>
</table>

<script>
  // Robust sorter: numeric if possible, else string
  function sortTable(n) {
    var table = document.getElementById("coordTable");
    var switching = true, dir = "asc", switchcount = 0, rows, i, x, y, shouldSwitch;
    while (switching) {
      switching = false;
      rows = table.rows;
      for (i = 1; i < (rows.length - 1); i++) {
        shouldSwitch = false;
        x = rows[i].getElementsByTagName("TD")[n];
        y = rows[i + 1].getElementsByTagName("TD")[n];
        var xv = x.innerHTML.trim();
        var yv = y.innerHTML.trim();
        var xn = parseFloat(xv.replace(/,/g,''));
        var yn = parseFloat(yv.replace(/,/g,''));
        var cmp;
        if (!isNaN(xn) && !isNaN(yn)) {
          cmp = (xn > yn) ? 1 : (xn < yn) ? -1 : 0;
        } else {
          cmp = xv.toLowerCase() > yv.toLowerCase() ? 1 : (xv.toLowerCase() < yv.toLowerCase() ? -1 : 0);
        }
        if ((dir === "asc" && cmp > 0) || (dir === "desc" && cmp < 0)) {
          shouldSwitch = true;
          break;
        }
      }
      if (shouldSwitch) {
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
        switchcount++;
      } else {
        if (switchcount === 0 && dir === "asc") { dir = "desc"; switching = true; }
      }
    }
  }

  function searchTable() {
    var input = document.getElementById("searchInput").value.toLowerCase();
    var rows = document.getElementById("coordTable").rows;
    for (var i = 1; i < rows.length; i++) {
      var text = rows[i].innerText.toLowerCase();
      rows[i].style.display = text.indexOf(input) > -1 ? "" : "none";
    }
  }

  function downloadCSV() {
    var table = document.getElementById("coordTable");
    var rows = table.querySelectorAll("tr");
    var csv = [];
    for (var i = 0; i < rows.length; i++) {
      var cols = rows[i].querySelectorAll("td, th");
      var row = [];
      for (var j = 0; j < cols.length; j++) {
        // Escape quotes for CSV
        var cell = cols[j].innerText.replace(/"/g, '""');
        row.push('"' + cell + '"');
      }
      csv.push(row.join(","));
    }
    var blob = new Blob([csv.join("\\n")], { type: "text/csv" });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "SelectedElementsReport.csv";
    link.click();
  }

  function downloadPDF() {
    // Simple: print dialog (user can save as PDF)
    var w = window.open("", "", "height=700,width=900");
    w.document.write("<html><head><title>Selected Elements Report</title>");
    w.document.write("<style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:6px;text-align:center}</style>");
    w.document.write("</head><body>");
    w.document.write(document.getElementById("coordTable").outerHTML);
    w.document.write("</body></html>");
    w.document.close();
    w.print();
  }
</script>

</body>
</html>
"""

# Combine final HTML
html_full = html_head + html_rows + html_tail

# ---------------------------
# 5) Save to temp & open
# ---------------------------
temp_dir = tempfile.gettempdir()
html_path = os.path.join(temp_dir, "SelectedElements_Report.html")
with open(html_path, "w") as f:
    f.write(html_full)

script.get_output().print_md("✅ Report created: `{}`".format(html_path))
webbrowser.open("file://" + html_path)
