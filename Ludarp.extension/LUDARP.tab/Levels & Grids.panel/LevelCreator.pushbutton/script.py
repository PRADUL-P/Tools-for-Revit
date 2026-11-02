# -*- coding: utf-8 -*-
"""
Level Creator - BIMToolkit
Batch create multiple levels from a reference level with uniform or custom offsets.
"""
__title__ = "Level Creator"
__author__ = "PRADUL P"

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import os
from pyrevit import revit, DB, forms, script

doc = revit.doc
output = script.get_output()

FEET_TO_MM = 304.8


class LevelOption(object):
    def __init__(self, level):
        self.level = level
        self.name = level.Name
        self.elevation_ft = level.Elevation
        self.elevation_mm = level.Elevation * FEET_TO_MM
        self.display = "{0} ({1:,.0f} mm)".format(self.name, self.elevation_mm)

    def ToString(self):
        return self.display

    def __str__(self):
        return self.display


class CustomLevelRow(object):
    def __init__(self, name, offset_mm):
        self.Name = name
        self.OffsetMm = "{0:,.0f}".format(offset_mm)
        self.raw_offset_mm = offset_mm


class PreviewRow(object):
    def __init__(self, index, name, elev_mm, rel_offset_mm):
        self.Index = str(index)
        self.Name = name
        self.ElevMm = "{0:,.1f}".format(elev_mm)
        self.RelOffsetMm = "{0:+,.1f}".format(rel_offset_mm)
        self.raw_elev_ft = elev_mm / FEET_TO_MM
        self.raw_name = name


class LevelCreatorWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.custom_items = []
        self.preview_items = []

        # 1. Collect levels
        levels_collector = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.Level)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        self.existing_levels = sorted(levels_collector, key=lambda l: l.Elevation)
        self.level_options = [LevelOption(lvl) for lvl in self.existing_levels]

        if not self.level_options:
            forms.alert("No existing levels found in the project.", title="Level Creator")
            self.Close()
            return

        for opt in self.level_options:
            self.RefLevelCombo.Items.Add(str(opt.display))
        self.RefLevelCombo.SelectedIndex = 0

        # Bind events
        self.RefLevelCombo.SelectionChanged += self.on_refresh_preview
        self.UniformRadio.Checked += self.on_mode_changed
        self.CustomRadio.Checked += self.on_mode_changed
        self.AddCustomRowBtn.Click += self.on_add_custom_row
        self.RemoveCustomRowBtn.Click += self.on_remove_custom_row
        self.ClearCustomRowsBtn.Click += self.on_clear_custom_rows
        self.PreviewBtn.Click += self.on_refresh_preview
        self.CreateBtn.Click += self.on_create_levels
        self.CancelBtn.Click += self.on_cancel

        # Initial preview
        self.update_preview()

    def on_mode_changed(self, sender, e):
        is_uniform = bool(self.UniformRadio.IsChecked)
        from System.Windows import Visibility
        self.UniformPanel.Visibility = Visibility.Visible if is_uniform else Visibility.Collapsed
        self.CustomPanel.Visibility = Visibility.Collapsed if is_uniform else Visibility.Visible
        self.update_preview()

    def on_add_custom_row(self, sender, e):
        name = (self.CustomNameInput.Text or "").strip()
        offset_text = (self.CustomOffsetInput.Text or "").strip()

        if not name:
            forms.alert("Please enter a Level Name.", title="Input Required")
            return

        try:
            offset_val = float(offset_text)
        except ValueError:
            forms.alert("Offset must be a valid number in millimeters.", title="Invalid Number")
            return

        row = CustomLevelRow(name, offset_val)
        self.custom_items.append(row)
        self.CustomLevelsList.ItemsSource = None
        self.CustomLevelsList.ItemsSource = self.custom_items

        # Auto-suggest next name
        self.CustomNameInput.Text = ""
        self.update_preview()

    def on_remove_custom_row(self, sender, e):
        selected = self.CustomLevelsList.SelectedItem
        if selected and selected in self.custom_items:
            self.custom_items.remove(selected)
            self.CustomLevelsList.ItemsSource = None
            self.CustomLevelsList.ItemsSource = self.custom_items
            self.update_preview()

    def on_clear_custom_rows(self, sender, e):
        self.custom_items = []
        self.CustomLevelsList.ItemsSource = None
        self.update_preview()

    def on_refresh_preview(self, sender, e):
        self.update_preview()

    def update_preview(self):
        idx = self.RefLevelCombo.SelectedIndex
        if idx < 0 or idx >= len(self.level_options):
            return

        selected_opt = self.level_options[idx]
        ref_elev_mm = selected_opt.elevation_mm
        self.preview_items = []

        if bool(self.UniformRadio.IsChecked):
            try:
                offset_mm = float(self.OffsetInput.Text or "0")
                count = int(self.CountInput.Text or "0")
            except ValueError:
                return

            if count <= 0:
                self.PreviewList.ItemsSource = None
                return

            prefix = (self.PrefixInput.Text or "Level ")
            is_above = bool(self.AboveRadio.IsChecked)
            direction = 1.0 if is_above else -1.0

            # Determine starting index from existing names
            start_num = len(self.existing_levels) + 1

            for i in range(1, count + 1):
                rel_offset = direction * offset_mm * i
                target_elev = ref_elev_mm + rel_offset
                lvl_name = "{0}{1}".format(prefix, start_num + (i - 1))
                self.preview_items.append(
                    PreviewRow(i, lvl_name, target_elev, rel_offset)
                )
        else:
            for idx, item in enumerate(self.custom_items, 1):
                rel_offset = item.raw_offset_mm
                target_elev = ref_elev_mm + rel_offset
                self.preview_items.append(
                    PreviewRow(idx, item.Name, target_elev, rel_offset)
                )

        self.PreviewList.ItemsSource = None
        self.PreviewList.ItemsSource = self.preview_items

    def on_cancel(self, sender, e):
        self.Close()

    def on_create_levels(self, sender, e):
        self.update_preview()
        if not self.preview_items:
            forms.alert("No levels to create. Please configure levels and refresh preview.", title="Level Creator")
            return

        existing_names = set(l.Name for l in self.existing_levels)
        created_levels = []
        errors = []

        with revit.Transaction("BIMToolkit: Create Levels"):
            for item in self.preview_items:
                try:
                    # Create level at elevation (in feet)
                    elev_ft = item.raw_elev_ft
                    new_level = DB.Level.Create(doc, elev_ft)

                    # Ensure unique name
                    candidate_name = item.raw_name
                    unique_name = candidate_name
                    counter = 2
                    while unique_name in existing_names:
                        unique_name = "{0} ({1})".format(candidate_name, counter)
                        counter += 1

                    new_level.Name = unique_name
                    existing_names.add(unique_name)
                    created_levels.append([
                        item.Index,
                        unique_name,
                        "{0:,.1f} mm".format(item.raw_elev_ft * FEET_TO_MM),
                        "✅ Created"
                    ])
                except Exception as ex:
                    errors.append([
                        item.Index,
                        item.raw_name,
                        "-",
                        "❌ {0}".format(ex)
                    ])

        self.Close()

        # Print report
        output.print_md("# 📏 Level Creator Results")
        output.print_md(
            "**Total Created:** {0} | **Failed:** {1}".format(len(created_levels), len(errors))
        )
        output.print_md("---")
        all_results = created_levels + errors
        output.print_table(
            table_data=all_results,
            title="Created Levels",
            columns=["#", "Level Name", "Elevation (mm)", "Status"],
            formats=["{}", "{}", "{}", "{}"]
        )


def main():
    xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = LevelCreatorWindow(xaml_path)
    win.show_dialog()


if __name__ == "__main__":
    main()
