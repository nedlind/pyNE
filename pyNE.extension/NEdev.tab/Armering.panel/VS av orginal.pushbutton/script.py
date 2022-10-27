# -*- coding: UTF-8 -*-

import math
from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction, UnitUtils, Structure
from Autodesk.Revit.UI.Selection import *
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
    
def unit_to_internal(doc, value):
    if int(doc.Application.VersionNumber) < 2022:
        um = DB.DisplayUnitType.DUT_MILLIMETERS
        return UnitUtils.ConvertToInternalUnits(value, um)
    else:
        um = DB.UnitTypeId.Millimeters
        return UnitUtils.ConvertToInternalUnits(value, um)

def unit_from_internal(doc, value):
    if int(doc.Application.VersionNumber) < 2022:
        um = DB.DisplayUnitType.DUT_MILLIMETERS
        return UnitUtils.ConvertFromInternalUnits(value, um)
    else:
        um = DB.UnitTypeId.Millimeters
        return UnitUtils.ConvertFromInternalUnits(value, um)


# Select source object (Rebar)
rebar_original_id = uidoc.Selection.PickObject(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick source rebar").ElementId
rebar_original = doc.GetElement(rebar_original_id)

rebar_type = doc.GetElement(rebar_original.GetTypeId())

# Get original length
L = rebar_original.LookupParameter("a").AsDouble()

# Get bar diameter
d = doc, rebar_type.LookupParameter("Bar Diameter").AsDouble()

# Get bar spacing
s = rebar_original.LookupParameter("Spacing").AsDouble()

# Read splice length Ls from source object
Ls = rebar_original.LookupParameter("Skarvlängd").AsDouble()

# Check number of bars for exact spacing
sda_0 = rebar_original.GetShapeDrivenAccessor()
dist_path = sda_0.GetDistributionPath()
n_bars = math.floor(dist_path.Length / s) + 1
n_bars_1 = math.ceil(n_bars / 2) # number of bars in first set
n_bars_2 = n_bars - n_bars_1 # number of bars in second set

bars_on_normal = sda_0.BarsOnNormalSide
include_first = rebar_original.IncludeFirstBar
include_last = rebar_original.IncludeLastBar

# Get vectors for bar direction (longitudinal) and distribution (transversal) direction
dir_trans = dist_path.Direction
dir_long = rebar_original.GetCenterlineCurves(0,1,1,0,0)[0].Direction

# Set max bar length Lmax = 12000 mm
Lmax = unit_to_internal(doc, 12000)

# Set min bar length Lmin = 4000 mm
Lmin = unit_to_internal(doc, 4000)

# Calvulate number of splices
if L < Lmax: 
    n = 0
else:
    n = int(math.ceil((L + 0.3*Ls) / (Lmax + 1 - Ls)))

if n > 0:

    # Calculate start and end bar lenght
    La = L-n*(Lmax-Ls)
    Lb = L-Lmin-(n-1)*Lmax+n*Ls
    if La < Lmin:
      Lstart = Lmin
      Lend = Lb
    else:
      Lstart = La
      Lend = Lmax
      
    t = Transaction(doc, 'Create shifted splice rebar from original')
    t.Start()

    # Copy original bar and move orgiginal to separate Partition
    rebar_1_0 = doc.GetElement(DB.ElementTransformUtils.CopyElement(doc,rebar_original_id,DB.XYZ())[0])
    
    partition = rebar_original.LookupParameter("Partition").AsString()
    rebar_original.LookupParameter("Partition").Set(partition + "_original")

    # Adjust length of rebar_1_0 to Lstart
    rebar_1_0.LookupParameter("a").Set(Lstart)
    
    # Change layout number with double spacing
    sda_1 = rebar_1_0.GetShapeDrivenAccessor()
    sda_1.SetLayoutAsNumberWithSpacing(n_bars_1 , s*2, bars_on_normal, include_first, include_last)

    # Copy rebar_1_0 spacing in transversal direction
    rebar_2_0 = doc.GetElement(DB.ElementTransformUtils.CopyElement(doc,rebar_1_0.Id, dir_trans * s )[0])
    sda_2 = rebar_2_0.GetShapeDrivenAccessor()
    sda_2.SetLayoutAsNumberWithSpacing(n_bars_2 , s*2, bars_on_normal, include_first, include_last)
    
    # Adjust length of rebar_2_0 to Lend
    rebar_2_0.LookupParameter("a").Set(Lend)
    
    ids_to_shift = [] # Every other rebar to shift one diameter in splice

    for i in range(n-1):
        rebar_1_x_id = DB.ElementTransformUtils.CopyElement(doc,rebar_1_0.Id, dir_long * (Lstart + i * Lmax))[0]
        doc.GetElement(rebar_1_x_id).LookupParameter("a").Set(Lmax)
        
        rebar_2_x_id = DB.ElementTransformUtils.CopyElement(doc,rebar_2_0.Id, dir_long * (Lend + i * Lmax))[0]
        doc.GetElement(rebar_2_x_id).LookupParameter("a").Set(Lmax)
        
        if (i % 2) > 0: # Even numbers
            ids_to_shift.extend([rebar_1_x_id, rebar_2_x_id])    

    # Last bars  
    i += 1
      
    rebar_1_1_id = DB.ElementTransformUtils.CopyElement(doc,rebar_1_0.Id, dir_long * (Lstart + i * Lmax))[0]
    doc.GetElement(rebar_1_1_id).LookupParameter("a").Set(Lend)
    
    rebar_2_1_id = DB.ElementTransformUtils.CopyElement(doc,rebar_2_0.Id, dir_long * (Lend + i * Lmax))[0]
    doc.GetElement(rebar_2_1_id).LookupParameter("a").Set(Lstart)
    
    if (i % 2) > 0: # Even numbers
        ids_to_shift.extend([rebar_1_1_id, rebar_2_1_id])    
    
    # Shift every other bar one diameter transversally
    #DB.ElementTransformUtils.MoveElements(doc, List[DB.ElementId](ids_to_shift), dir_trans * d)
    for i in ids_to_shift:
        DB.ElementTransformUtils.MoveElement(doc, i, dir_trans * d)
    
    t.Commit()
