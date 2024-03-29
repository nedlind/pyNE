"""Checks transport width of selected rebar"""

__author__ = "Niklas Edlind"

import sys
from Autodesk.Revit import DB
from Autodesk.Revit.DB import UnitUtils, LabelUtils
from Autodesk.Revit.UI.Selection import *
from pyrevit import script

output = script.get_output()

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

def unit_to_internal(doc, value):
    if int(doc.Application.VersionNumber) < 2022:
        um = doc.GetUnits().GetFormatOptions(DB.UnitType.UT_Length).DisplayUnits
        return UnitUtils.ConvertToInternalUnits(value, um)
    else:
        um = doc.GetUnits().GetFormatOptions(DB.SpecTypeId.Length).GetUnitTypeId()
        return UnitUtils.ConvertToInternalUnits(value, um)

def unit_from_internal(doc, value):
    if int(doc.Application.VersionNumber) < 2022:
        um = doc.GetUnits().GetFormatOptions(DB.UnitType.UT_Length).DisplayUnits
        return UnitUtils.ConvertFromInternalUnits(value, um)
    else:
        um = doc.GetUnits().GetFormatOptions(DB.SpecTypeId.Length).GetUnitTypeId()
        return UnitUtils.ConvertFromInternalUnits(value, um)

#prompt selection of dimension to align to
try:
    stirrup_selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick stirrup to check")
except: sys.exit("User abort")

transport_widths = []

for sel in stirrup_selection:
    stirrup = doc.GetElement(sel.ElementId)
    bar_curves = stirrup.GetCenterlineCurves(1,1,1,0,0)
    bar_pts = []
    
    for crv in bar_curves:
        #start point of all segments
        bar_pts.append(crv.GetEndPoint(0))
     #end point of last segment
    bar_pts.append(crv.GetEndPoint(1))
    
    bar_plane = DB.Plane.CreateByThreePoints(bar_pts[0], bar_pts[1], bar_pts[2])
    normal = bar_plane.Normal
    
    p1 = bar_pts[-1]
	
    dims = []
    for i in range(len(bar_pts)):
        p2 = bar_pts[i]
        xaxis = (p2 - p1).Normalize()
        segment_plane = DB.Plane.CreateByOriginAndBasis(p1, xaxis, normal)
        p1 = p2
        dist = []
        
        for p in bar_pts:
            uv, d = segment_plane.Project(p)
            dist.append(d)
            
        dims.append(max(dist))

    transport_widths.append((sel.ElementId, min(dims)))

#unit symmbol
if int(doc.Application.VersionNumber) < 2022:
    pass
else:
    format_options = doc.GetUnits().GetFormatOptions(DB.SpecTypeId.Length)
    unit_id = format_options.GetUnitTypeId()
    if unit_id.Empty(): symbol = ""
    else: unit = LabelUtils.GetLabelForUnit(unit_id)

if unit == "Meters":
    dec_format = '{:.3f}'
    symbol = 'm'
elif unit == "Millimeters":
    dec_format = '{:.0f}'
    symbol = 'mm'
else: dec_format = '{:.3f}'

for t in transport_widths:
    print('{} {} {}'.format(output.linkify(t[0]), dec_format.format(unit_from_internal(doc, t[1])), symbol))