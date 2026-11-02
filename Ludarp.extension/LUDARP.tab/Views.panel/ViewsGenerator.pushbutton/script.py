# -*- coding: utf-8 -*-
"""
Views Generator - BIMToolkit
Batch create views for selected levels across Architectural, Structural,
Mechanical, Electrical, Plumbing, and Coordination disciplines with Floor Plans,
Reflected Ceiling Plans (RCP), and multiple industry-standard naming schemes.
"""
__title__ = "Views Generator"
__author__ = "PRADUL P"

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import os
import re
from pyrevit import revit, DB, forms, script

doc = revit.doc
output = script.get_output()

FEET_TO_MM = 304.8


def get_iso_role_code(discipline):
    d = (discipline or "").lower()
    if "arch" in d:
        return "A"
    elif "struct" in d:
        return "S"
    elif "mech" in d:
        return "M"
    elif "elec" in d:
        return "E"
    elif "plumb" in d:
        return "P"
    elif "coord" in d:
        return "C"
    return "Z"


def get_disc_short_code(discipline):
    d = (discipline or "").lower()
    if "arch" in d:
        return "AR"
    elif "struct" in d:
        return "ST"
    elif "mech" in d:
        return "ME"
    elif "elec" in d:
        return "EL"
    elif "plumb" in d:
        return "PL"
    elif "coord" in d:
        return "CO"
    return "GE"


def get_iso_type_code(view_type_str):
    vt = (view_type_str or "").lower()
    if "ceiling" in vt or "rcp" in vt or "soffit" in vt:
        return "CP"
    return "PL"


def get_iso_level_code(level_name):
    name = level_name or ""
    digits = re.findall(r'\d+', name)
    if digits:
        num = int(digits[0])
        if "b" in name.lower() or "basement" in name.lower():
            return "B{0}".format(num)
        return "{0:02d}".format(num)
    if any(k in name.lower() for k in ["ground", "entry", "site"]):
        return "00"
    return "ZZ"


class LevelItem(object):
    def __init__(self, level):
        self.level = level
        self.Name = level.Name
        self.elevation_mm = level.Elevation * FEET_TO_MM
        self.ElevMm = "{0:,.0f}".format(self.elevation_mm)


class ViewGenPreviewItem(object):
    def __init__(self, index, name, discipline, view_type, level_item, vft, disc_enum):
        self.Index = str(index)
        self.ProposedName = name
        self.Discipline = discipline
        self.ViewType = view_type
        self.LevelName = level_item.Name
        self.level_item = level_item
        self.vft = vft
        self.disc_enum = disc_enum


class ViewsGeneratorWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.preview_items = []

        # 1. Setup Naming Schemes
        self.schemes = [
            ("Discipline First: [discipline] - [type] - [level]", "[discipline] - [type] - [level]"),
            ("Level First (Browser Grouping): [level] - [discipline] - [type]", "[level] - [discipline] - [type]"),
            ("AIA / US National Standard: [role]-[type_code]-[level_code]", "[role]-[type_code]-[level_code]"),
            ("Short Code: [disc_short]_[type_code]_[level_code]", "[disc_short]_[type_code]_[level_code]"),
            ("ISO 19650 Standard Container", "ISO19650"),
            ("Custom Pattern Template", "[discipline] - [type] - [level]")
        ]

        for s_title, _ in self.schemes:
            self.NamingSchemeCombo.Items.Add(s_title)
        self.NamingSchemeCombo.SelectedIndex = 0

        self.NamingPatternInput.Text = self.schemes[0][1]
        proj_code_default = re.sub(r'[^A-Za-z0-9]', '', (doc.Title or "PRJ")[:4]).upper() or "PRJ"
        self.IsoProjectInput.Text = proj_code_default

        # 2. Collect levels
        levels_collector = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.Level)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        sorted_levels = sorted(levels_collector, key=lambda l: l.Elevation)
        self.level_items = [LevelItem(lvl) for lvl in sorted_levels]

        if not self.level_items:
            forms.alert("No levels found in project to generate views from.", title="Views Generator")
            self.Close()
            return

        self.LevelsListView.ItemsSource = self.level_items
        self.LevelsListView.SelectAll()

        # 3. Collect ViewFamilyTypes
        vft_collector = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.ViewFamilyType)
            .ToElements()
        )

        self.floor_plan_vft = None
        self.ceiling_plan_vft = None
        self.struct_plan_vft = None
        self.mech_plan_vft = None
        self.elec_plan_vft = None

        for vft in vft_collector:
            fam = vft.ViewFamily
            vft_name = (vft.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() or "").lower()

            if fam == DB.ViewFamily.FloorPlan:
                if not self.floor_plan_vft:
                    self.floor_plan_vft = vft
                if any(k in vft_name for k in ["mech", "hvac", "mep", "plumb"]):
                    self.mech_plan_vft = vft
                if any(k in vft_name for k in ["elec", "power", "light"]):
                    self.elec_plan_vft = vft

            elif fam == DB.ViewFamily.CeilingPlan:
                if not self.ceiling_plan_vft:
                    self.ceiling_plan_vft = vft

            elif fam == DB.ViewFamily.StructuralPlan:
                if not self.struct_plan_vft:
                    self.struct_plan_vft = vft

        # Fallbacks
        if not self.mech_plan_vft:
            self.mech_plan_vft = self.floor_plan_vft
        if not self.elec_plan_vft:
            self.elec_plan_vft = self.floor_plan_vft
        if not self.struct_plan_vft:
            self.struct_plan_vft = self.floor_plan_vft

        # Disciplines
        self.disc_arch = DB.ViewDiscipline.Architectural
        self.disc_struct = DB.ViewDiscipline.Structural
        self.disc_mech = DB.ViewDiscipline.Mechanical
        self.disc_elec = DB.ViewDiscipline.Electrical
        self.disc_plumb = getattr(DB.ViewDiscipline, "Plumbing", DB.ViewDiscipline.Mechanical)
        self.disc_coord = getattr(DB.ViewDiscipline, "Coordination", DB.ViewDiscipline.Architectural)

        # Bind events
        self.SelectAllLevelsBtn.Click += self.on_select_all_levels
        self.SelectNoneLevelsBtn.Click += self.on_select_none_levels
        self.LevelsListView.SelectionChanged += self.on_option_changed

        self.CheckAllViewsBtn.Click += self.on_check_all_views
        self.UncheckAllViewsBtn.Click += self.on_uncheck_all_views

        self.all_checkboxes = [
            self.ArchFloorPlanCB,
            self.ArchCeilingPlanCB,
            self.StructPlanCB,
            self.StructCeilingPlanCB,
            self.MechPlanCB,
            self.MechCeilingPlanCB,
            self.ElecPlanCB,
            self.ElecCeilingPlanCB,
            self.PlumbPlanCB,
            self.CoordPlanCB,
            self.CoordCeilingPlanCB,
        ]

        for cb in self.all_checkboxes:
            cb.Checked += self.on_option_changed
            cb.Unchecked += self.on_option_changed

        # Scheme & Naming Controls
        self.NamingSchemeCombo.SelectionChanged += self.on_scheme_changed
        self.ForceUppercaseCB.Checked += self.on_option_changed
        self.ForceUppercaseCB.Unchecked += self.on_option_changed
        self.NamingPatternInput.TextChanged += self.on_option_changed
        self.PrefixInput.TextChanged += self.on_option_changed
        self.SuffixInput.TextChanged += self.on_option_changed

        self.IsoProjectInput.TextChanged += self.on_option_changed
        self.IsoOriginatorInput.TextChanged += self.on_option_changed
        self.IsoZoneInput.TextChanged += self.on_option_changed
        self.IsoSeqInput.TextChanged += self.on_option_changed
        self.IsoSepInput.TextChanged += self.on_option_changed

        self.RefreshPreviewBtn.Click += self.on_option_changed
        self.GenerateBtn.Click += self.on_generate_views
        self.CancelBtn.Click += self.on_cancel

        self.update_preview()

    def on_scheme_changed(self, sender, e):
        from System.Windows import Visibility
        idx = self.NamingSchemeCombo.SelectedIndex
        if idx < 0 or idx >= len(self.schemes):
            return

        _, pattern_val = self.schemes[idx]

        if pattern_val == "ISO19650":
            self.IsoNamingPanel.Visibility = Visibility.Visible
            self.PatternInputPanel.Visibility = Visibility.Collapsed
        else:
            self.IsoNamingPanel.Visibility = Visibility.Collapsed
            self.PatternInputPanel.Visibility = Visibility.Visible
            if idx != 5:  # Don't overwrite if on Custom
                self.NamingPatternInput.Text = pattern_val

        self.update_preview()

    def on_select_all_levels(self, sender, e):
        self.LevelsListView.SelectAll()
        self.update_preview()

    def on_select_none_levels(self, sender, e):
        self.LevelsListView.UnselectAll()
        self.update_preview()

    def on_check_all_views(self, sender, e):
        for cb in self.all_checkboxes:
            cb.IsChecked = True
        self.update_preview()

    def on_uncheck_all_views(self, sender, e):
        for cb in self.all_checkboxes:
            cb.IsChecked = False
        self.update_preview()

    def on_option_changed(self, sender, e):
        self.update_preview()

    def on_cancel(self, sender, e):
        self.Close()

    def update_preview(self):
        selected_levels = list(self.LevelsListView.SelectedItems)
        scheme_idx = self.NamingSchemeCombo.SelectedIndex
        is_iso = (scheme_idx == 4)
        force_upper = bool(self.ForceUppercaseCB.IsChecked)

        pfx = (self.PrefixInput.Text or "")
        sfx = (self.SuffixInput.Text or "")

        plan_configs = []

        # Architecture
        if bool(self.ArchFloorPlanCB.IsChecked) and self.floor_plan_vft:
            plan_configs.append(("Arch", "Floor Plan", self.floor_plan_vft, self.disc_arch))
        if bool(self.ArchCeilingPlanCB.IsChecked) and self.ceiling_plan_vft:
            plan_configs.append(("Arch", "Ceiling Plan", self.ceiling_plan_vft, self.disc_arch))

        # Structural
        if bool(self.StructPlanCB.IsChecked) and self.struct_plan_vft:
            plan_configs.append(("Struct", "Floor Plan", self.struct_plan_vft, self.disc_struct))
        if bool(self.StructCeilingPlanCB.IsChecked) and self.ceiling_plan_vft:
            plan_configs.append(("Struct", "Soffit Plan", self.ceiling_plan_vft, self.disc_struct))

        # Mechanical
        if bool(self.MechPlanCB.IsChecked) and self.mech_plan_vft:
            plan_configs.append(("Mech", "Floor Plan", self.mech_plan_vft, self.disc_mech))
        if bool(self.MechCeilingPlanCB.IsChecked) and self.ceiling_plan_vft:
            plan_configs.append(("Mech", "Ceiling Plan", self.ceiling_plan_vft, self.disc_mech))

        # Electrical
        if bool(self.ElecPlanCB.IsChecked) and self.elec_plan_vft:
            plan_configs.append(("Elec", "Floor Plan", self.elec_plan_vft, self.disc_elec))
        if bool(self.ElecCeilingPlanCB.IsChecked) and self.ceiling_plan_vft:
            plan_configs.append(("Elec", "Ceiling Plan", self.ceiling_plan_vft, self.disc_elec))

        # Plumbing
        if bool(self.PlumbPlanCB.IsChecked) and self.floor_plan_vft:
            plan_configs.append(("Plumb", "Floor Plan", self.floor_plan_vft, self.disc_plumb))

        # Coordination
        if bool(self.CoordPlanCB.IsChecked) and self.floor_plan_vft:
            plan_configs.append(("Coord", "Floor Plan", self.floor_plan_vft, self.disc_coord))
        if bool(self.CoordCeilingPlanCB.IsChecked) and self.ceiling_plan_vft:
            plan_configs.append(("Coord", "Ceiling Plan", self.ceiling_plan_vft, self.disc_coord))

        self.preview_items = []
        counter = 1

        if is_iso:
            prj = (self.IsoProjectInput.Text or "PRJ").strip().upper()
            orig = (self.IsoOriginatorInput.Text or "ARC").strip().upper()
            zone = (self.IsoZoneInput.Text or "ZZ").strip().upper()
            seq_str = (self.IsoSeqInput.Text or "0001").strip()
            sep = (self.IsoSepInput.Text or "-")
            try:
                start_num = int(seq_str)
                pad_width = len(seq_str)
            except ValueError:
                start_num = 1
                pad_width = 4

            for lvl_item in selected_levels:
                lvl_code = get_iso_level_code(lvl_item.Name)
                for disc, vtype, vft, disc_enum in plan_configs:
                    type_code = get_iso_type_code(vtype)
                    role_code = get_iso_role_code(disc)
                    cur_seq = str(start_num + (counter - 1)).zfill(pad_width)
                    raw_name = "{0}{s}{1}{s}{2}{s}{3}{s}{4}{s}{5}{s}{6}".format(
                        prj, orig, zone, lvl_code, type_code, role_code, cur_seq, s=sep
                    )
                    final_name = raw_name.upper() if force_upper else raw_name
                    self.preview_items.append(
                        ViewGenPreviewItem(counter, final_name, disc, vtype, lvl_item, vft, disc_enum)
                    )
                    counter += 1
        else:
            pattern = (self.NamingPatternInput.Text or "[discipline] - [type] - [level]").strip()
            for lvl_item in selected_levels:
                lvl_code = get_iso_level_code(lvl_item.Name)
                for disc, vtype, vft, disc_enum in plan_configs:
                    type_code = get_iso_type_code(vtype)
                    role_code = get_iso_role_code(disc)
                    disc_short = get_disc_short_code(disc)
                    seq_str = "{0:02d}".format(counter)

                    name = (
                        pattern.replace("[discipline]", disc)
                        .replace("[type]", vtype)
                        .replace("[level]", lvl_item.Name)
                        .replace("[level_code]", lvl_code)
                        .replace("[level_num]", lvl_code)
                        .replace("[type_code]", type_code)
                        .replace("[role]", role_code)
                        .replace("[disc_code]", role_code)
                        .replace("[disc_short]", disc_short)
                        .replace("[seq]", seq_str)
                        .replace("[project]", doc.Title or "Project")
                        .replace("{discipline}", disc)
                        .replace("{type}", vtype)
                        .replace("{level}", lvl_item.Name)
                        .replace("{seq}", seq_str)
                    )
                    assembled = "{0}{1}{2}".format(pfx, name, sfx)
                    final_name = assembled.upper() if force_upper else assembled
                    self.preview_items.append(
                        ViewGenPreviewItem(counter, final_name, disc, vtype, lvl_item, vft, disc_enum)
                    )
                    counter += 1

        self.PreviewListView.ItemsSource = None
        self.PreviewListView.ItemsSource = self.preview_items

    def on_generate_views(self, sender, e):
        self.update_preview()
        if not self.preview_items:
            forms.alert("No views to generate. Please select at least one level and view type.", title="Views Generator")
            return

        all_views = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.View)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        existing_names = set(v.Name for v in all_views if not v.IsTemplate)

        created_views = []
        errors = []

        with revit.Transaction("BIMToolkit: Generate Views"):
            for item in self.preview_items:
                try:
                    # 1. Create ViewPlan
                    new_view = DB.ViewPlan.Create(doc, item.vft.Id, item.level_item.level.Id)

                    # 2. Set View Discipline
                    try:
                        disc_param = new_view.get_Parameter(DB.BuiltInParameter.VIEW_DISCIPLINE)
                        if disc_param and not disc_param.IsReadOnly:
                            disc_param.Set(int(item.disc_enum))
                    except Exception:
                        pass

                    # 3. Ensure Unique Name
                    candidate_name = item.ProposedName
                    unique_name = candidate_name
                    suffix_counter = 2
                    while unique_name in existing_names:
                        unique_name = "{0} ({1})".format(candidate_name, suffix_counter)
                        suffix_counter += 1

                    new_view.Name = unique_name
                    existing_names.add(unique_name)

                    created_views.append([
                        item.Index,
                        unique_name,
                        item.Discipline,
                        item.ViewType,
                        item.LevelName,
                        "✅ Created"
                    ])
                except Exception as ex:
                    errors.append([
                        item.Index,
                        item.ProposedName,
                        item.Discipline,
                        item.ViewType,
                        item.LevelName,
                        "❌ {0}".format(ex)
                    ])

        self.Close()

        output.print_md("# 📐 Views Generator Results")
        output.print_md(
            "**Total Generated:** {0} | **Failed:** {1}".format(len(created_views), len(errors))
        )
        output.print_md("---")
        all_results = created_views + errors
        output.print_table(
            table_data=all_results,
            title="Generated Views Log",
            columns=["#", "View Name", "Discipline", "Type", "Level", "Status"],
            formats=["{}", "{}", "{}", "{}", "{}", "{}"]
        )


def main():
    xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = ViewsGeneratorWindow(xaml_path)
    win.show_dialog()


if __name__ == "__main__":
    main()
