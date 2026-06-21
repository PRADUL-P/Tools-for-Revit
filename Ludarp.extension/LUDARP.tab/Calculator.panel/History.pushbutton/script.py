# -*- coding: utf-8 -*-
"""
📊 LUDARP Calculator: History
Version: 1.2 | Author: PRADUL P

This script opens a custom WPF dialog displaying the history of recent calculations
and provides options to copy results, clear the log, or export to CSV.
"""
__title__ = "Calc History"
__author__ = "PRADUL P"

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import os
import json
import csv
import tempfile
from pyrevit import forms, script

# Path to the history JSON file
temp_dir = tempfile.gettempdir()
HISTORY_FILE = os.path.join(temp_dir, "calculator_history.json")

class HistoryRecord(object):
    def __init__(self, entry):
        self.timestamp = entry.get("timestamp", "")
        self.element_a = entry.get("element_a", "")
        self.value_a = entry.get("value_a", "")
        self.element_b = entry.get("element_b", "")
        self.value_b = entry.get("value_b", "")
        
        self.element_a_disp = "{0} ({1})".format(self.element_a, self.value_a)
        self.element_b_disp = "{0} ({1})".format(self.element_b, self.value_b)
        
        op = entry.get("operation", "")
        if "Addition" in op or "+" in op:
            self.op_disp = "➕ Add"
        elif "Subtraction" in op or "-" in op:
            self.op_disp = "➖ Subtract"
        elif "Multiplication" in op or "*" in op:
            self.op_disp = "✖️ Multiply"
        elif "Division" in op or "/" in op:
            self.op_disp = "➗ Divide"
        else:
            self.op_disp = op
            
        self.result = entry.get("result", "")

class HistoryWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        
        # Load and bind records
        self.records = []
        self.load_history()
        
        # Bind event handlers
        self.CopyBtn.Click += self.copy_result
        self.ExportBtn.Click += self.export_csv
        self.ClearBtn.Click += self.clear_history
        self.CloseBtn.Click += self.close_window
        
    def load_history(self):
        self.records = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    entries = json.load(f)
                    # Show latest calculations first
                    for entry in reversed(entries):
                        self.records.append(HistoryRecord(entry))
            except Exception as e:
                forms.alert("Error loading history:\n{}".format(e))
        self.HistoryList.ItemsSource = self.records
                
    def copy_result(self, sender, e):
        selected = self.HistoryList.SelectedItem
        if selected:
            script.clipboard_copy(selected.result)
            forms.toast("Copied result: {}".format(selected.result))
        else:
            forms.alert("Please select a calculation from the list first.")
            
    def export_csv(self, sender, e):
        if not self.records:
            forms.alert("No history to export.")
            return
            
        dest_file = forms.save_file(file_ext='csv', default_name='LUDARP_Calculation_History.csv')
        if not dest_file:
            return
            
        try:
            with open(dest_file, "wb") as f:  # Python 2 csv writer needs binary mode
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", 
                    "Element A", 
                    "Value A", 
                    "Operation", 
                    "Element B", 
                    "Value B", 
                    "Result"
                ])
                # Write in chronological order
                for rec in reversed(self.records):
                    writer.writerow([
                        rec.timestamp.encode('utf-8') if isinstance(rec.timestamp, unicode) else rec.timestamp,
                        rec.element_a.encode('utf-8') if isinstance(rec.element_a, unicode) else rec.element_a,
                        rec.value_a.encode('utf-8') if isinstance(rec.value_a, unicode) else rec.value_a,
                        rec.op_disp.encode('utf-8') if isinstance(rec.op_disp, unicode) else rec.op_disp,
                        rec.element_b.encode('utf-8') if isinstance(rec.element_b, unicode) else rec.element_b,
                        rec.value_b.encode('utf-8') if isinstance(rec.value_b, unicode) else rec.value_b,
                        rec.result.encode('utf-8') if isinstance(rec.result, unicode) else rec.result
                    ])
            forms.toast("History exported to CSV!")
        except Exception as ex:
            forms.alert("Error exporting CSV:\n{}".format(ex))
            
    def clear_history(self, sender, e):
        if not self.records:
            forms.alert("History is already empty.")
            return
            
        confirm = forms.alert(
            "Are you sure you want to clear all calculation history?",
            yes=True, no=True,
            title="Clear History"
        )
        if confirm:
            try:
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                self.records = []
                self.HistoryList.ItemsSource = self.records
                forms.toast("History cleared!")
            except Exception as ex:
                forms.alert("Error clearing history:\n{}".format(ex))
                
    def close_window(self, sender, e):
        self.Close()

def main():
    xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = HistoryWindow(xaml_path)
    win.show_dialog()

if __name__ == "__main__":
    main()
