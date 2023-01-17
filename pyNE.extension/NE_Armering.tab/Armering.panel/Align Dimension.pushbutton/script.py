"""Aligns dimension lines to first picked line"""

__author__ = "Niklas Edlind"

import sys
from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction
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

#prompt selection of dimension to align to
try:
    selection_parent = uidoc.Selection.PickObject(ObjectType.Element, CustomISelectionFilter("Dimensions"),"Pick dimension to align to")
except: sys.exit("User abort")

#prompt selection of dimensions to align
try:
    selection_children = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilter("Dimensions"),"Pick dimensions to align")
except: sys.exit("User abort")

view_dir = active_view.ViewDirection

parent_crv = doc.GetElement(selection_parent.ElementId).Curve
op = parent_crv.Origin
crv_dir = parent_crv.Direction
dim_plane = DB.Plane.CreateByOriginAndBasis(op,crv_dir,view_dir)
   
t = Transaction(doc, 'Align Dimensions')   
t.Start()
        
for dim_ref in selection_children:         
    #get location point of tag 
    dim = doc.GetElement(dim_ref.ElementId)
    op = dim.Curve.Origin
    new_uv = dim_plane.Project(op)[0]
    new_xyz = dim_plane.Origin + new_uv.U * dim_plane.XVec + new_uv.V * dim_plane.YVec
    dim.Location.Move(new_xyz - op)
    
t.Commit()


            
            

