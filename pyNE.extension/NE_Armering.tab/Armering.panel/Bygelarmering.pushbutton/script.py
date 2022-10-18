"""Skapar armering med samma diameter som markerad bygel i varje bock"""

__author__ = "Niklas Edlind"

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction, Structure
from Autodesk.Revit.UI.Selection import *
from System import Type
from System.Collections.Generic import List

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

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
    
def getRebarBends(rebar, pos, offset):
    transform = rebar.GetShapeDrivenAccessor().GetBarPositionTransform(pos)
    b_curves = rebar.GetCenterlineCurves(0,1,0,0,pos)
    pt_list = []
    for crv in b_curves:
        if crv.GetType() == DB.Arc:
            crv_tranformed = crv.CreateTransformed(transform)
            #point on centerline rebar
            pt_cl = crv_tranformed.Evaluate(0.5, True)
            #arc center point
            pt_center = crv_tranformed.Center
            offset_dir = (pt_center - pt_cl).Normalize()
            pt_list.append(pt_cl + offset_dir*offset)
    return pt_list

#prompt selection of dimension to align to
stirrup_selection = uidoc.Selection.PickObject(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick stirrup to to place bend rebar in")
stirrup = doc.GetElement(stirrup_selection.ElementId)

host = doc.GetElement(stirrup.GetHostId())
rebarbartype = doc.GetElement(stirrup.GetTypeId())
rebarhookdir = DB.Structure.RebarHookOrientation.Right

stirrup_normal = stirrup.GetShapeDrivenAccessor().Normal

rebarhooktype = None
offset = 0.1

sp = getRebarBends(stirrup, 0, offset)
ep = getRebarBends(stirrup, stirrup.NumberOfBarPositions-1, offset)


t = Transaction(doc, 'Create rebar in stirrup bend')

t.Start()

for i, p in enumerate(sp):
    bar_plane = DB.Plane.CreateByNormalAndOrigin(stirrup_normal, p)
    bar_normal = bar_plane.XVec
    line = DB.Line.CreateBound(sp[i], ep[i])

    crv_list = List[DB.Curve]([line])
    try:
        Structure.Rebar.CreateFromCurves(doc, DB.Structure.RebarStyle.Standard, rebarbartype, rebarhooktype, rebarhooktype, host, bar_normal, crv_list, rebarhookdir, rebarhookdir, True, False)
    except:
        print("error")

t.Commit()

# TODO : 
#   Set partition same as parent rebar
#   Set offset by rebar diameter
#   Set ELU_Rebar_Code EE?E
#   Set Revit selection to created bars
