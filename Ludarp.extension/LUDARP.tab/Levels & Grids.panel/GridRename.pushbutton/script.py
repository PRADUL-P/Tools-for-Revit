# -*- coding: utf-8 -*-
"""
Grid Rename (TCOUNT) - BIMToolkit
Sequentially rename grids based on directional sorting (Left->Right, Bottom->Top, etc.)
with Numeric or Alphabetic sequences.
"""
__title__ = "Grid Rename"
__author__ = "PRADUL P"

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import os
from pyrevit import revit, DB, forms, script

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def int_to_alpha(n):
    """Convert 1->A, 2->B, ..., 26->Z, 27->AA, 28->AB..."""
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + (n % 26)) + result
        n //= 26
    return result


def alpha_to_int(s):
    """Convert A->1, B->2, ..., Z->26, AA->27..."""
    result = 0
    clean = (s or "A").strip().upper()
    for char in clean:
        if 'A' <= char <= 'Z':
            result = result * 26 + (ord(char) - ord('A') + 1)
        else:
            break
    return max(1, result)


class GridPreviewItem(object):
    def __init__(self, order, grid, new_name, coord_val):
        self.Order = str(order)
        self.grid = grid
        self.CurrentName = grid.Name
        self.NewName = new_name
        self.Coordinate = "{0:,.2f}".format(coord_val)


class GridRenameWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.active_grids = []
        self.preview_items = []

        # Collect selection vs all
        sel_ids = uidoc.Selection.GetElementIds()
        self.selected_grids = []
        for eid in sel_ids:
            elem = doc.GetElement(eid)
            if isinstance(elem, DB.Grid):
                self.selected_grids.append(elem)

        all_grids_collector = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Grids)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        self.all_grids = [g for g in all_grids_collector if isinstance(g, DB.Grid)]

        # Set initial radio button state
        if not self.selected_grids:
            self.SelectedOnlyRadio.IsEnabled = False
            self.AllGridsRadio.IsChecked = True
        else:
            self.SelectedOnlyRadio.IsChecked = True

        # Bind events
        self.SelectedOnlyRadio.Checked += self.on_scope_changed
        self.AllGridsRadio.Checked += self.on_scope_changed
        self.NumericModeRadio.Checked += self.on_mode_changed
        self.AlphaModeRadio.Checked += self.on_mode_changed

        self.DirLRRadio.Checked += self.on_rule_changed
        self.DirRLRadio.Checked += self.on_rule_changed
        self.DirBTRadio.Checked += self.on_rule_changed
        self.DirTBRadio.Checked += self.on_rule_changed

        self.RefreshPreviewBtn.Click += self.on_rule_changed
        self.RenameBtn.Click += self.on_rename
        self.CancelBtn.Click += self.on_cancel

        self.update_active_grids()
        self.update_preview()

    def on_scope_changed(self, sender, e):
        self.update_active_grids()
        self.update_preview()

    def on_mode_changed(self, sender, e):
        is_num = bool(self.NumericModeRadio.IsChecked)
        if is_num:
            self.StartInput.Text = "1"
            self.IncrementInput.IsEnabled = True
        else:
            self.StartInput.Text = "A"
            self.IncrementInput.IsEnabled = False
        self.update_preview()

    def on_rule_changed(self, sender, e):
        self.update_preview()

    def update_active_grids(self):
        if bool(self.SelectedOnlyRadio.IsChecked) and self.selected_grids:
            self.active_grids = list(self.selected_grids)
        else:
            self.active_grids = list(self.all_grids)

        self.GridCountLabel.Text = "{0} grid(s) found".format(len(self.active_grids))

    def get_grid_midpoint(self, grid):
        curve = grid.Curve
        if curve:
            return curve.Evaluate(0.5, True)
        return DB.XYZ(0, 0, 0)

    def sort_grids(self):
        is_lr = bool(self.DirLRRadio.IsChecked)
        is_rl = bool(self.DirRLRadio.IsChecked)
        is_bt = bool(self.DirBTRadio.IsChecked)
        is_tb = bool(self.DirTBRadio.IsChecked)

        def sort_key(g):
            pt = self.get_grid_midpoint(g)
            if is_lr:
                return (pt.X, pt.Y)
            elif is_rl:
                return (-pt.X, pt.Y)
            elif is_bt:
                return (pt.Y, pt.X)
            elif is_tb:
                return (-pt.Y, pt.X)
            return (pt.X, pt.Y)

        return sorted(self.active_grids, key=sort_key)

    def update_preview(self):
        if not self.active_grids:
            self.PreviewList.ItemsSource = None
            return

        sorted_grids = self.sort_grids()
        prefix = (self.PrefixInput.Text or "")
        suffix = (self.SuffixInput.Text or "")
        is_num = bool(self.NumericModeRadio.IsChecked)

        self.preview_items = []

        if is_num:
            try:
                start_val = int(self.StartInput.Text or "1")
                inc_val = int(self.IncrementInput.Text or "1")
            except ValueError:
                return
            for idx, g in enumerate(sorted_grids):
                seq_val = start_val + (idx * inc_val)
                new_name = "{0}{1}{2}".format(prefix, seq_val, suffix)
                pt = self.get_grid_midpoint(g)
                coord = pt.X if (bool(self.DirLRRadio.IsChecked) or bool(self.DirRLRadio.IsChecked)) else pt.Y
                self.preview_items.append(GridPreviewItem(idx + 1, g, new_name, coord))
        else:
            start_str = (self.StartInput.Text or "A").strip()
            start_val = alpha_to_int(start_str)
            for idx, g in enumerate(sorted_grids):
                alpha_str = int_to_alpha(start_val + idx)
                new_name = "{0}{1}{2}".format(prefix, alpha_str, suffix)
                pt = self.get_grid_midpoint(g)
                coord = pt.X if (bool(self.DirLRRadio.IsChecked) or bool(self.DirRLRadio.IsChecked)) else pt.Y
                self.preview_items.append(GridPreviewItem(idx + 1, g, new_name, coord))

        self.PreviewList.ItemsSource = None
        self.PreviewList.ItemsSource = self.preview_items

    def on_cancel(self, sender, e):
        self.Close()

    def on_rename(self, sender, e):
        self.update_preview()
        if not self.preview_items:
            forms.alert("No grids to rename.", title="Grid Rename")
            return

        results = []
        renamed_count = 0
        error_count = 0

        # Execute 2-pass renaming inside a single Transaction
        with revit.Transaction("BIMToolkit: Grid Rename"):
            # Pass 1: Assign temporary names to avoid conflict
            for item in self.preview_items:
                try:
                    temp_name = "__TEMP_G_{0}__".format(item.grid.Id.IntegerValue)
                    item.grid.Name = temp_name
                except Exception:
                    pass

            # Pass 2: Assign target new names
            for item in self.preview_items:
                orig_name = item.CurrentName
                target_name = item.NewName
                try:
                    item.grid.Name = target_name
                    results.append([item.Order, orig_name, target_name, "✅ Success"])
                    renamed_count += 1
                except Exception as ex:
                    # Restore original name if failed
                    try:
                        item.grid.Name = orig_name
                    except Exception:
                        pass
                    results.append([item.Order, orig_name, target_name, "❌ {0}".format(ex)])
                    error_count += 1

        self.Close()

        output.print_md("# 🔢 Grid Rename (TCOUNT) Results")
        output.print_md(
            "**Total Processed:** {0} | ✅ Renamed: {1} | ❌ Failed: {2}".format(
                len(self.preview_items), renamed_count, error_count
            )
        )
        output.print_md("---")
        output.print_table(
            table_data=results,
            title="Grid Renaming Log",
            columns=["#", "Original Name", "New Name", "Status"],
            formats=["{}", "{}", "{}", "{}"]
        )


def main():
    xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = GridRenameWindow(xaml_path)
    win.show_dialog()


if __name__ == "__main__":
    main()
