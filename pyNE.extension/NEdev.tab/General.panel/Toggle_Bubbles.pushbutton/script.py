"""Adds specified tag to the middle rebar of selected rebar objects with leader arrow"""

__author__ = "Niklas Edlind"

import sys
from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction
from pyrevit import forms
from Autodesk.Revit.UI.Selection import *


uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

active_view_id = doc.ActiveView.Id
active_view = doc.GetElement(active_view_id)


class CustomISelectionFilter(ISelectionFilter):
    def __init__(self, element_class):
        self.element_class = element_class

    def AllowElement(self, e):
        if e.Category.Name == self.element_class:
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return False


def toggleBubble(level, end, view):
    if level.HasBubbleInView(end, view):
        if level.IsBubbleVisibleInView(end, view):
            level.HideBubbleInView(end, view)
        else:
            level.ShowBubbleInView(end, view)


option, switches = \
    forms.CommandSwitchWindow.show(
        [],
        switches=['Start', 'End'],
        message='Select End Bubbles to toggle:',
        recognize_access_key=True
    )

try:
    level_refs = uidoc.Selection.PickObjects(
        ObjectType.Element, CustomISelectionFilter("Levels"), "Pick levels")
except:
    sys.exit("User abort")


toggle_start = switches["Start"]
toggle_end = switches["End"]

t = Transaction(doc, "Toggle Level Bubbles")
t.Start()

out = []

for ref in level_refs:
    level = doc.GetElement(ref.ElementId)
    if toggle_start:
        end = DB.DatumEnds.End0
        toggleBubble(level, end, active_view)
    if toggle_end:
        end = DB.DatumEnds.End1
        toggleBubble(level, end, active_view)

t.Commit()
