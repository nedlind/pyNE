"""Sets red color on visibility override for all rebar in active view without tag"""

__author__ = "Niklas Edlind"

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

t = Transaction(doc, 'Show Untagged')
t.Start()

for b in rebar_collector:
     
    #clear override on all rebar 
    active_view.SetElementOverrides(b.Id, clear_override_settings)
                             
t.Commit()

