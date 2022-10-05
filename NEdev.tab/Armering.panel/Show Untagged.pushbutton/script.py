"""Sets red color on visibility override for all rebar in active view without tag"""

__author__ = "Niklas Edlind"

import clr
clr.AddReference("System")
from System.Collections.Generic import List

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction

doc = __revit__.ActiveUIDocument.Document

active_view_id = doc.ActiveView.Id
active_view = doc.GetElement(active_view_id)


rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
                    .OfCategory(DB.BuiltInCategory.OST_Rebar) 

clear_override_settings = DB.OverrideGraphicSettings()\
                        .SetProjectionLineColor(DB.Color.InvalidColorValue)\
                        .SetProjectionLineWeight(DB.OverrideGraphicSettings.InvalidPenNumber)\
                        .SetCutBackgroundPatternColor(DB.Color.InvalidColorValue)                    
untagged_ids = []

t = Transaction(doc, 'Show Untagged')
t.Start()

# Create ICollection of Categories t filter on
category_list = List[DB.BuiltInCategory]([DB.BuiltInCategory.OST_MultiReferenceAnnotations, DB.BuiltInCategory.OST_RebarTags])

for b in rebar_collector:
    tag_ids = b.GetDependentElements(DB.ElementMulticategoryFilter(category_list))
    
    if len(tag_ids) < 1:
        untagged_ids.append(b.Id)
        
    #clear override on all rebar first
    active_view.SetElementOverrides(b.Id, clear_override_settings)

color = DB.Color(255,0,0)

override_settings = DB.OverrideGraphicSettings()\
                        .SetProjectionLineColor(color)\
                        .SetProjectionLineWeight(4)\
                        .SetCutBackgroundPatternColor(color)

for i in untagged_ids:                     
    active_view.SetElementOverrides(i, override_settings)
                             
t.Commit()

