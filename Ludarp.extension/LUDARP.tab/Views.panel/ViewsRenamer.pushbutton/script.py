# -*- coding: utf-8 -*-
"""
Views Renamer - BIMToolkit
Interactive all-in-one control center for filtering by discipline/type, natural sorting,
and batch renaming views with ISO 19650 or customizable patterns.
"""
__title__ = "Views Renamer"
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


def natural_sort_key(s):
    """Sort strings containing numbers in human order: 1, 2, ..., 9, 10, 11..."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def get_view_discipline(view):
    """Detect view discipline from parameter or naming."""
    try:
        p = view.get_Parameter(DB.BuiltInParameter.VIEW_DISCIPLINE)
        if p and p.HasValue:
            val = p.AsInteger()
            disc_map = {
                1: "Architecture",
                2: "Structural",
                4: "Mechanical",
                8: "Electrical",
                16: "Plumbing",
                32: "Coordination"
            }
            if val in disc_map:
                return disc_map[val]
    except Exception:
        pass

    name_lower = view.Name.lower()
    if name_lower.startswith("arch") or "architecture" in name_lower:
        return "Architecture"
    elif name_lower.startswith("struct") or "structural" in name_lower:
        return "Structural"
    elif name_lower.startswith("mech") or "mechanical" in name_lower or "hvac" in name_lower:
        return "Mechanical"
    elif name_lower.startswith("elec") or "electrical" in name_lower or "light" in name_lower or "power" in name_lower:
        return "Electrical"
    elif name_lower.startswith("plumb") or "plumbing" in name_lower or "pip" in name_lower:
        return "Plumbing"
    elif name_lower.startswith("coord") or "coordination" in name_lower:
        return "Coordination"
    return "Architecture"


def get_view_level(view):
    """Get associated Level object if any."""
    if hasattr(view, "GenLevel") and view.GenLevel:
        return view.GenLevel
    return None


def get_level_elevation(view):
    lvl = get_view_level(view)
    if lvl:
        return lvl.Elevation
    return -999999.0


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


def get_iso_type_code(view):
    vt = view.ViewType
    if vt == DB.ViewType.FloorPlan:
        return "PL"
    elif vt == DB.ViewType.CeilingPlan:
        return "CP"
    elif vt == DB.ViewType.Elevation:
        return "EL"
    elif vt == DB.ViewType.Section:
        return "SC"
    elif vt == DB.ViewType.ThreeD:
        return "3D"
    elif vt == DB.ViewType.AreaPlan:
        return "AP"
    elif vt == DB.ViewType.EngineeringPlan:
        return "SP"
    elif vt == DB.ViewType.Detail:
        return "DT"
    elif vt == DB.ViewType.DraftingView:
        return "DR"
    return "VW"


def get_iso_level_code(view):
    lvl = get_view_level(view)
    if lvl:
        name = lvl.Name
        digits = re.findall(r'\d+', name)
        if digits:
            num = int(digits[0])
            if "b" in name.lower() or "basement" in name.lower():
                return "B{0}".format(num)
            return "{0:02d}".format(num)
        if any(k in name.lower() for k in ["ground", "entry", "site"]):
            return "00"
    return "ZZ"


class ViewListItem(object):
    def __init__(self, view):
        self.view = view
        self.Name = view.Name
        self.Discipline = get_view_discipline(view)
        lvl = get_view_level(view)
        self.LevelName = lvl.Name if lvl else "No Level"
        self.Elevation = get_level_elevation(view)
        self.ViewType = view.ViewType


class PreviewRowItem(object):
    def __init__(self, index, view_item, new_name):
        self.Index = str(index)
        self.view_item = view_item
        self.CurrentName = view_item.Name
        self.NewName = new_name
        self.Discipline = view_item.Discipline
        self.Status = "Will Rename" if self.CurrentName != new_name else "Unchanged"


class ViewsRenamerWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.all_views = []
        self.displayed_views = []
        self.preview_items = []

        # 1. Collect views
        raw_views = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.View)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for v in raw_views:
            if not v.IsTemplate and v.ViewType not in [
                DB.ViewType.DrawingSheet,
                DB.ViewType.Schedule,
                DB.ViewType.SystemBrowser,
                DB.ViewType.ProjectBrowser,
                DB.ViewType.Undefined,
                DB.ViewType.Internal
            ]:
                self.all_views.append(ViewListItem(v))

        # 2. Setup Filter Combos
        disc_options = [
            "All Disciplines",
            "Architecture",
            "Structural",
            "Mechanical",
            "Electrical",
            "Plumbing",
            "Coordination"
        ]
        for d in disc_options:
            self.DisciplineFilterCombo.Items.Add(d)
        self.DisciplineFilterCombo.SelectedIndex = 0

        type_options = [
            "All View Types",
            "Floor Plans",
            "Ceiling Plans",
            "Structural Plans",
            "Sections",
            "Elevations",
            "3D Views",
            "Drafting Views",
            "Legends"
        ]
        for t in type_options:
            self.ViewTypeFilterCombo.Items.Add(t)
        self.ViewTypeFilterCombo.SelectedIndex = 0

        sort_options = [
            "Natural Order (Level 1, 2... 10)",
            "Discipline + Natural Level",
            "Level Elevation (Bottom to Top)",
            "Alphabetical (A-Z)"
        ]
        for s in sort_options:
            self.SortOrderCombo.Items.Add(s)
        self.SortOrderCombo.SelectedIndex = 0

        action_options = [
            "ISO 19650 Standard",
            "Replace Entire Name (Pattern Override)",
            "Add Prefix / Suffix",
            "Find and Replace",
            "Regex Replace",
            "Sequential Numbering",
            "Change Case"
        ]
        for a in action_options:
            self.ActionCombo.Items.Add(a)
        self.ActionCombo.SelectedIndex = 0

        # Defaults for inputs
        proj_code_default = re.sub(r'[^A-Za-z0-9]', '', (doc.Title or "PRJ")[:4]).upper() or "PRJ"
        self.IsoProjectInput.Text = proj_code_default
        self.PatternInput.Text = "{discipline} - {type} - {level}"

        # 3. Bind Events
        self.DisciplineFilterCombo.SelectionChanged += self.on_filter_changed
        self.ViewTypeFilterCombo.SelectionChanged += self.on_filter_changed
        self.SortOrderCombo.SelectionChanged += self.on_filter_changed
        self.SearchInput.TextChanged += self.on_filter_changed

        self.SelectAllBtn.Click += self.on_select_all
        self.DeselectAllBtn.Click += self.on_deselect_all
        self.ViewsListView.SelectionChanged += self.on_selection_changed

        self.ActionCombo.SelectionChanged += self.on_action_changed
        self.RefreshPreviewBtn.Click += self.on_refresh_preview
        self.ApplyBtn.Click += self.on_apply
        self.CancelBtn.Click += self.on_cancel

        # Sub-panel input change bindings
        self.IsoProjectInput.TextChanged += self.on_param_changed
        self.IsoOriginatorInput.TextChanged += self.on_param_changed
        self.IsoZoneInput.TextChanged += self.on_param_changed
        self.IsoLevelInput.TextChanged += self.on_param_changed
        self.IsoTypeInput.TextChanged += self.on_param_changed
        self.IsoRoleInput.TextChanged += self.on_param_changed
        self.IsoSeqInput.TextChanged += self.on_param_changed
        self.IsoSepInput.TextChanged += self.on_param_changed
        self.PatternInput.TextChanged += self.on_param_changed
        self.PrefixInput.TextChanged += self.on_param_changed
        self.SuffixInput.TextChanged += self.on_param_changed
        self.FindInput.TextChanged += self.on_param_changed
        self.ReplaceInput.TextChanged += self.on_param_changed
        self.RegexPatternInput.TextChanged += self.on_param_changed
        self.RegexReplaceInput.TextChanged += self.on_param_changed
        self.SeqPrefixInput.TextChanged += self.on_param_changed
        self.SeqStartInput.TextChanged += self.on_param_changed
        self.SeqPadInput.TextChanged += self.on_param_changed
        self.UpperRadio.Checked += self.on_param_changed
        self.LowerRadio.Checked += self.on_param_changed
        self.TitleRadio.Checked += self.on_param_changed

        # Initial populate
        self.apply_filter_and_sort()
        self.ViewsListView.SelectAll()
        self.update_preview()

    def on_filter_changed(self, sender, e):
        self.apply_filter_and_sort()
        self.ViewsListView.SelectAll()
        self.update_preview()

    def on_selection_changed(self, sender, e):
        self.update_preview()

    def on_param_changed(self, sender, e):
        self.update_preview()

    def on_refresh_preview(self, sender, e):
        self.update_preview()

    def on_select_all(self, sender, e):
        self.ViewsListView.SelectAll()
        self.update_preview()

    def on_deselect_all(self, sender, e):
        self.ViewsListView.UnselectAll()
        self.update_preview()

    def on_cancel(self, sender, e):
        self.Close()

    def on_action_changed(self, sender, e):
        from System.Windows import Visibility
        idx = self.ActionCombo.SelectedIndex

        # Hide all
        self.IsoPanel.Visibility = Visibility.Collapsed
        self.PatternPanel.Visibility = Visibility.Collapsed
        self.PrefixSuffixPanel.Visibility = Visibility.Collapsed
        self.FindReplacePanel.Visibility = Visibility.Collapsed
        self.RegexPanel.Visibility = Visibility.Collapsed
        self.SeqPanel.Visibility = Visibility.Collapsed
        self.CasePanel.Visibility = Visibility.Collapsed

        if idx == 0:
            self.IsoPanel.Visibility = Visibility.Visible
        elif idx == 1:
            self.PatternPanel.Visibility = Visibility.Visible
        elif idx == 2:
            self.PrefixSuffixPanel.Visibility = Visibility.Visible
        elif idx == 3:
            self.FindReplacePanel.Visibility = Visibility.Visible
        elif idx == 4:
            self.RegexPanel.Visibility = Visibility.Visible
        elif idx == 5:
            self.SeqPanel.Visibility = Visibility.Visible
        elif idx == 6:
            self.CasePanel.Visibility = Visibility.Visible

        self.update_preview()

    def apply_filter_and_sort(self):
        disc_sel = self.DisciplineFilterCombo.SelectedItem or "All Disciplines"
        type_sel = self.ViewTypeFilterCombo.SelectedItem or "All View Types"
        search_kw = (self.SearchInput.Text or "").strip().lower()
        sort_sel = self.SortOrderCombo.SelectedItem or "Natural Order (Level 1, 2... 10)"

        filtered = []
        for item in self.all_views:
            # 1. Discipline check
            if disc_sel != "All Disciplines" and item.Discipline != disc_sel:
                continue

            # 2. View Type check
            if type_sel != "All View Types":
                vt = item.ViewType
                if type_sel == "Floor Plans" and vt != DB.ViewType.FloorPlan:
                    continue
                elif type_sel == "Ceiling Plans" and vt != DB.ViewType.CeilingPlan:
                    continue
                elif type_sel == "Structural Plans" and vt != DB.ViewType.EngineeringPlan:
                    continue
                elif type_sel == "Sections" and vt != DB.ViewType.Section:
                    continue
                elif type_sel == "Elevations" and vt != DB.ViewType.Elevation:
                    continue
                elif type_sel == "3D Views" and vt != DB.ViewType.ThreeD:
                    continue
                elif type_sel == "Drafting Views" and vt != DB.ViewType.DraftingView:
                    continue
                elif type_sel == "Legends" and vt != DB.ViewType.Legend:
                    continue

            # 3. Search Keyword
            if search_kw and search_kw not in item.Name.lower():
                continue

            filtered.append(item)

        # 4. Sorting
        if "Discipline + Natural" in sort_sel:
            self.displayed_views = sorted(filtered, key=lambda v: (v.Discipline, natural_sort_key(v.Name)))
        elif "Elevation" in sort_sel:
            self.displayed_views = sorted(filtered, key=lambda v: (v.Elevation, natural_sort_key(v.Name)))
        elif "Alphabetical" in sort_sel:
            self.displayed_views = sorted(filtered, key=lambda v: v.Name)
        else:
            # Natural Order
            self.displayed_views = sorted(filtered, key=lambda v: natural_sort_key(v.Name))

        self.ViewsListView.ItemsSource = None
        self.ViewsListView.ItemsSource = self.displayed_views
        self.ViewsCountLabel.Text = "Views in Scope ({0}):".format(len(self.displayed_views))

    def update_preview(self):
        selected_items = list(self.ViewsListView.SelectedItems)
        action_idx = self.ActionCombo.SelectedIndex

        self.preview_items = []
        if not selected_items:
            self.PreviewListView.ItemsSource = None
            self.SummaryStatusLabel.Text = "No views selected."
            return

        # Generate new names based on chosen action
        # 0: ISO 19650
        if action_idx == 0:
            prj = (self.IsoProjectInput.Text or "PRJ").strip().upper()
            orig = (self.IsoOriginatorInput.Text or "ARC").strip().upper()
            zone = (self.IsoZoneInput.Text or "ZZ").strip().upper()
            level_in = (self.IsoLevelInput.Text or "AUTO").strip()
            type_in = (self.IsoTypeInput.Text or "AUTO").strip()
            role_in = (self.IsoRoleInput.Text or "AUTO").strip()
            sep = (self.IsoSepInput.Text or "-")

            seq_str = (self.IsoSeqInput.Text or "0001").strip()
            try:
                start_num = int(seq_str)
                pad_width = len(seq_str)
            except ValueError:
                start_num = 1
                pad_width = 4

            for idx, item in enumerate(selected_items):
                v = item.view
                # Auto or custom Level
                if level_in.upper() == "AUTO" or not level_in:
                    lvl_code = get_iso_level_code(v)
                else:
                    lvl_code = level_in.upper()

                # Auto or custom Type
                if type_in.upper() == "AUTO" or not type_in:
                    type_code = get_iso_type_code(v)
                else:
                    type_code = type_in.upper()

                # Auto or custom Role
                if role_in.upper() == "AUTO" or not role_in:
                    role_code = get_iso_role_code(item.Discipline)
                else:
                    role_code = role_in.upper()

                cur_seq = str(start_num + idx).zfill(pad_width)
                new_name = "{0}{s}{1}{s}{2}{s}{3}{s}{4}{s}{5}{s}{6}".format(
                    prj, orig, zone, lvl_code, type_code, role_code, cur_seq, s=sep
                )
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 1: Replace Entire Name (Pattern Override)
        elif action_idx == 1:
            pattern = (self.PatternInput.Text or "{discipline} - {type} - {level}").strip()
            for idx, item in enumerate(selected_items):
                v = item.view
                vtype_name = "Floor Plan" if v.ViewType == DB.ViewType.FloorPlan else ("Ceiling Plan" if v.ViewType == DB.ViewType.CeilingPlan else str(v.ViewType).replace("ViewType.", ""))
                seq_str = "{0:02d}".format(idx + 1)
                new_name = (
                    pattern.replace("{discipline}", item.Discipline)
                    .replace("{type}", vtype_name)
                    .replace("{level}", item.LevelName)
                    .replace("{seq}", seq_str)
                    .replace("{project}", doc.Title or "Project")
                    .replace("{name}", item.Name)
                    .replace("[discipline]", item.Discipline)
                    .replace("[type]", vtype_name)
                    .replace("[level]", item.LevelName)
                    .replace("[seq]", seq_str)
                    .replace("[name]", item.Name)
                )
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 2: Prefix / Suffix
        elif action_idx == 2:
            pfx = self.PrefixInput.Text or ""
            sfx = self.SuffixInput.Text or ""
            for idx, item in enumerate(selected_items):
                new_name = "{0}{1}{2}".format(pfx, item.Name, sfx)
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 3: Find & Replace
        elif action_idx == 3:
            find_str = self.FindInput.Text or ""
            rep_str = self.ReplaceInput.Text or ""
            for idx, item in enumerate(selected_items):
                new_name = item.Name.replace(find_str, rep_str) if find_str else item.Name
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 4: Regex Replace
        elif action_idx == 4:
            pattern = self.RegexPatternInput.Text or ""
            rep_str = self.RegexReplaceInput.Text or ""
            compiled = None
            if pattern:
                try:
                    compiled = re.compile(pattern)
                except Exception:
                    compiled = None

            for idx, item in enumerate(selected_items):
                if compiled:
                    try:
                        new_name = compiled.sub(rep_str, item.Name)
                    except Exception:
                        new_name = item.Name
                else:
                    new_name = item.Name
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 5: Sequential Numbering
        elif action_idx == 5:
            pfx = self.SeqPrefixInput.Text or "View "
            try:
                start_num = int(self.SeqStartInput.Text or "1")
                pad_width = int(self.SeqPadInput.Text or "2")
            except ValueError:
                start_num = 1
                pad_width = 2
            pad_width = max(1, pad_width)

            for idx, item in enumerate(selected_items):
                num_str = str(start_num + idx).zfill(pad_width)
                new_name = "{0}{1}".format(pfx, num_str)
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        # 6: Change Case
        elif action_idx == 6:
            is_upper = bool(self.UpperRadio.IsChecked)
            is_lower = bool(self.LowerRadio.IsChecked)
            for idx, item in enumerate(selected_items):
                if is_upper:
                    new_name = item.Name.upper()
                elif is_lower:
                    new_name = item.Name.lower()
                else:
                    new_name = item.Name.title()
                self.preview_items.append(PreviewRowItem(idx + 1, item, new_name))

        self.PreviewListView.ItemsSource = None
        self.PreviewListView.ItemsSource = self.preview_items

        rename_count = sum(1 for it in self.preview_items if it.Status == "Will Rename")
        self.SummaryStatusLabel.Text = "Selected: {0} views | {1} will be renamed".format(
            len(self.preview_items), rename_count
        )

    def on_apply(self, sender, e):
        self.update_preview()
        if not self.preview_items:
            forms.alert("No views selected to rename.", title="Views Renamer")
            return

        rename_items = [it for it in self.preview_items if it.Status == "Will Rename"]
        if not rename_items:
            forms.alert("None of the selected views will change with current settings.", title="Views Renamer")
            return

        confirm = forms.alert(
            "Proceed with renaming {0} view(s)?".format(len(rename_items)),
            title="Confirm Views Renamer",
            yes=True,
            no=True
        )
        if not confirm:
            return

        renamed_count = 0
        error_count = 0
        results = []

        # 2-Pass Transaction: Avoid duplicate name clashes
        with revit.Transaction("BIMToolkit: Views Renamer"):
            # Pass 1: Assign temporary names
            for it in rename_items:
                v = it.view_item.view
                try:
                    v.Name = "__TEMP_VR_{0}__".format(v.Id.IntegerValue)
                except Exception:
                    pass

            # Pass 2: Assign final names
            for it in rename_items:
                v = it.view_item.view
                orig_name = it.CurrentName
                target_name = it.NewName
                try:
                    v.Name = target_name
                    results.append([it.Index, orig_name, target_name, "✅ Success"])
                    renamed_count += 1
                except Exception as ex:
                    # Restore original name if failed
                    try:
                        v.Name = orig_name
                    except Exception:
                        pass
                    results.append([it.Index, orig_name, target_name, "❌ {0}".format(ex)])
                    error_count += 1

        self.Close()

        output.print_md("# ✏️ Views Renamer Results")
        output.print_md(
            "**Total Processed:** {0} | ✅ Renamed: {1} | ❌ Failed: {2}".format(
                len(rename_items), renamed_count, error_count
            )
        )
        output.print_md("---")
        output.print_table(
            table_data=results,
            title="Renaming Execution Log",
            columns=["#", "Original Name", "New Name", "Status"],
            formats=["{}", "{}", "{}", "{}"]
        )


def main():
    xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = ViewsRenamerWindow(xaml_path)
    win.show_dialog()


if __name__ == "__main__":
    main()
