"""Toggles solid display of all rebar in active view"""

__author__ = "Niklas Edlind"

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction

doc = __revit__.ActiveUIDocument.Document

active_view_id = doc.ActiveView.Id
active_view = doc.GetElement(active_view_id)

if active_view.ViewType.ToString() == "ThreeD":
    t = Transaction(doc, 'Toggle Rebar Solid in View')
    t.Start()
    rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
                        .OfCategory(DB.BuiltInCategory.OST_Rebar)
        
    if all(b.IsSolidInView(active_view) for b in rebar_collector):
        toggle = False
    else: 
        toggle = True
        
    for bar in rebar_collector:
        bar.SetSolidInView(active_view, toggle)
    t.Commit()
else:
    print("This command only works in 3D Views")

