"""Changes rebar representation of selected rebar to shown middle"""

__author__ = "Niklas Edlind"

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction, Structure
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

#prompt selection of rebar 
selection_rebar = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick Rebar to modify")

pres_mode = Structure.RebarPresentationMode.Middle

t = Transaction(doc, 'Rebar Representation Middle')   
t.Start()
        
for s in selection_rebar:         
    #get location point of tag 
    bar = doc.GetElement(s.ElementId)
    n_bars = bar.NumberOfBarPositions
    if n_bars > 2:  #two or fewer bars cant display middle
        n_displayed = 0
        
        # count number of displayed bars
        for i in range(bar.NumberOfBarPositions):   
            if not bar.IsBarHidden(active_view, i):
                n_displayed += 1
        if n_displayed > 1 and bar.CanApplyPresentationMode(active_view):  #leave bars with only one displayed bar
            bar.SetPresentationMode(active_view, pres_mode)
        
t.Commit()


            
            

