# -*- coding: utf-8 -*-

"""Reverts the actions of MRA group"""

__author__ = "Niklas Edlind"

import clr
clr.AddReference("System")
from System.Collections.Generic import List

import sys

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.UI.Selection import *

from pyrevit import script

logger = script.get_logger()

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
        
#prompt selection of mra
try:
    selection_parent_mra = uidoc.Selection.PickObject(ObjectType.Element, CustomISelectionFilter("Multi-Rebar Annotations"),"Pick main Multi-Rebar Annotation")
except Exception as err:
    logger.debug(err)
    sys.exit()
    
mra = doc.GetElement(selection_parent_mra)

#get main tagged rebar
rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
    .OfCategory(DB.BuiltInCategory.OST_Rebar)
    
for b in rebar_collector:
    for el_id in b.GetDependentElements(DB.ElementCategoryFilter(DB.BuiltInCategory.OST_MultiReferenceAnnotations)):
        if el_id == selection_parent_mra.ElementId:
            parent_rebar = b

linked_id_string = parent_rebar.LookupParameter("Comments").AsString()
linked_ids = [DB.ElementId(int(x)) for x in linked_id_string.split(',')]

rebar_to_unhide = DB.FilteredElementCollector(doc, List[DB.ElementId](linked_ids)).OfCategory(DB.BuiltInCategory.OST_Rebar).ToElementIds()
dimlines_to_delete = DB.FilteredElementCollector(doc, List[DB.ElementId](linked_ids)).OfCategory(DB.BuiltInCategory.OST_DetailComponents).ToElementIds()

#get original MRA
mra_collector = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_MultiReferenceAnnotations)\
    .WhereElementIsElementType()\
    .ToElements()
     
mra_group_familytype = next(i for i in mra_collector if i.LookupParameter("Type Name").AsString() == "Structural Rebar")    

t = Transaction(doc, 'Ungroup Multi-Rebar Annotations')   
t.Start()

#delete distribution lines      
doc.Delete(List[DB.ElementId](dimlines_to_delete))

#unhide grouped rebar
active_view.UnhideElements(List[DB.ElementId](rebar_to_unhide))

#change mra type
mra.ChangeTypeId(mra_group_familytype.Id)

#set grouped object ids to parent rebar
id_string = ""
parent_rebar.LookupParameter("Comments").Set(id_string)

t.Commit()

#   TODO

   


            
            

