"""Selects all rebar in active view without tag"""

__author__ = "Niklas Edlind"

import clr
clr.AddReference("System")
from System.Collections.Generic import List

from Autodesk.Revit import DB, UI
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.UI import Selection

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

active_view_id = doc.ActiveView.Id
active_view = doc.GetElement(active_view_id)


rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
                    .OfCategory(DB.BuiltInCategory.OST_Rebar) 
                 
untagged_ids = []

# Create ICollection of Categories t filter on
category_list = List[DB.BuiltInCategory]([DB.BuiltInCategory.OST_MultiReferenceAnnotations, DB.BuiltInCategory.OST_RebarTags])

for b in rebar_collector:
    tag_ids = b.GetDependentElements(DB.ElementMulticategoryFilter(category_list))
    
    if len(tag_ids) < 1:
        untagged_ids.append(b.Id)
        
uidoc.Selection.SetElementIds(List[DB.ElementId](untagged_ids))

# TODO
#   Create icon
