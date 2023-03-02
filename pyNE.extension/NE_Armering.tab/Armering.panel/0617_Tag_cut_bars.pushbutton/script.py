"""Adds specified tag to the middle rebar of selected rebar objects with leader arrow"""

__author__ = "Niklas Edlind"

# from operator import index
import math
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


def tagEnd(rebar_tag, bar_reference, point):
    tag = DB.IndependentTag.Create(doc, active_view_id, bar_reference, True,
                                   DB.TagMode.TM_ADDBY_CATEGORY, DB.TagOrientation.Horizontal, point)
    tag.ChangeTypeId(rebar_tag.Id)
    tag.LeaderEndCondition = DB.LeaderEndCondition.Free
    if int(doc.Application.VersionNumber) > 2022:  # API change in Revit 2023
        tag.SetLeaderEnd(tag.GetTaggedReferences()[0], point)
    else:
        tag.LeaderEnd = point


tags = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_RebarTags)\
    .WhereElementIsElementType()\
    .ToElements()


tag_names = [tag.FamilyName + tag.get_Parameter(
    DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for tag in tags]


sel_tag = forms.SelectFromList.show(tag_names, button_name='Select Item')

if not sel_tag:
    sys.exit("User abort")

rebar_tag = tags[tag_names.index(sel_tag)]


# prompt selection of dimension to align to
try:
    stirrup_selection = uidoc.Selection.PickObjects(
        ObjectType.Element, CustomISelectionFilter("Structural Rebar"), "Pick rebar to tag")
except:
    sys.exit("User abort")

t = Transaction(doc, 'Tag Rebar Ends')
t.Start()

for bar_ref in stirrup_selection:
    bar = doc.GetElement(bar_ref.ElementId)

    bar_index = int(math.floor(bar.NumberOfBarPositions/2))

    if not bar.IsBarHidden(active_view, bar_index):
        # get start and end points of visible bar
        transform = bar.GetShapeDrivenAccessor().GetBarPositionTransform(bar_index)
        b_curves = bar.GetCenterlineCurves(0, 1, 1, 0, bar_index)

        sp = b_curves[0].CreateTransformed(transform).GetEndPoint(0)

        if int(doc.Application.VersionNumber) > 2022:  # API change in Revit 2023
            subelement = bar.GetSubelements()[bar_index].GetReference()
            tagEnd(rebar_tag, subelement, sp)
        else:
            tagEnd(rebar_tag, bar_ref, sp)

t.Commit()

#   TODO
#   Allow script to run from selection of rebar and/or mra tag
#   Implement shift-click configuration of tag family
