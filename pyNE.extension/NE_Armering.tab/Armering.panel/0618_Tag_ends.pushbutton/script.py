"""Adds specified tag to each end of selected rebar with leader arrow at bar end locations"""

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
    
def tagEnd(rebar_tag, bar_reference, point):
    tag = DB.IndependentTag.Create(doc, active_view_id, bar_reference, True, DB.TagMode.TM_ADDBY_CATEGORY, DB.TagOrientation.Horizontal, point)
    tag.ChangeTypeId(rebar_tag.Id)
    tag.LeaderEndCondition = DB.LeaderEndCondition.Free
    if int(doc.Application.VersionNumber) > 2022:   #API change in Revit 2023
        tag.SetLeaderEnd(tag.GetTaggedReferences()[0], point)
    else:
        tag.LeaderEnd = point

tags = DB.FilteredElementCollector(doc)\
                        .OfCategory(DB.BuiltInCategory.OST_RebarTags)\
                        .WhereElementIsElementType()\
                        .ToElements()
                        

tag_names = [tag.FamilyName + tag.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for tag in tags]

                       
sel_tag = forms.SelectFromList.show(tag_names, button_name='Select Item')

if not sel_tag: sys.exit("User abort")

rebar_tag = tags[tag_names.index(sel_tag)]
    
    
#prompt selection of dimension to align to
try:
    stirrup_selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick rebar to tag")
except: sys.exit("User abort")

t = Transaction(doc, 'Tag Rebar Ends')
t.Start()
            
for bar_ref in stirrup_selection:
    bar = doc.GetElement(bar_ref.ElementId)
    for i in range(bar.NumberOfBarPositions):
        if not bar.IsBarHidden(active_view, i):
            #get start and end points of visible bar
            transform = bar.GetShapeDrivenAccessor().GetBarPositionTransform(i)
            b_curves = bar.GetCenterlineCurves(0,1,1,0,i)
            
            sp = b_curves[0].CreateTransformed(transform).GetEndPoint(0)
            ep = b_curves[len(b_curves)-1].CreateTransformed(transform).GetEndPoint(1)
 
            if int(doc.Application.VersionNumber) > 2022:   #API change in Revit 2023
                subelement = bar.GetSubelements()[i].GetReference()
                tagEnd(rebar_tag, subelement, sp)
                tagEnd(rebar_tag, subelement, ep)
            else:
                tagEnd(rebar_tag, bar_ref, sp)
                tagEnd(rebar_tag, bar_ref, ep)
            
            break
                               
t.Commit()
            
#   TODO
#   Allow script to run from selection of rebar and/or mra tag
			