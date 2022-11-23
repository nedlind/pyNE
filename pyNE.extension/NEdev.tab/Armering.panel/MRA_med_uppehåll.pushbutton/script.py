# -*- coding: utf-8 -*-

"""Aligns dimension lines to first picked line"""

__author__ = "Niklas Edlind"

import clr
clr.AddReference("System")
from System.Collections.Generic import List

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.UI.Selection import *
from Autodesk.Revit.Creation import ItemFactoryBase

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

def makeRebarString(rebar):
    shape_id = rebar.GetShapeId().ToString()
    type_id = rebar.GetTypeId().ToString()
    spacing = rebar.LookupParameter("Spacing").AsValueString()
    schedule_mark = rebar.LookupParameter("Schedule Mark").AsValueString()
    rebar_string = '.'.join([shape_id, type_id, spacing, schedule_mark])
    return rebar_string

def uvToXyz(uv, plane):
    return plane.Origin + uv.U * plane.XVec + uv.V * plane.YVec

def rebarLocation(rebar):
    b_curves = rebar.GetCenterlineCurves(0,1,1,0,0)
    return b_curves[0].GetEndPoint(0)  

def projectedRebarDistributionPoints(rebar, plane):
        #create translation to rebar orgigin (distribution path is relative)
        b_point = rebarLocation(rebar)
        transform = DB.Transform.CreateTranslation(DB.XYZ(b_point.X, b_point.Y, 0))    
    
        distribution_path = rebar.GetShapeDrivenAccessor().GetDistributionPath().CreateTransformed(transform)
        
        #xyz on rebar
        sp = distribution_path.GetEndPoint(0)
        ep = distribution_path.GetEndPoint(1)
        
        #projected points, converted from uv to xyz
        dim_start_xyz = uvToXyz(plane.Project(sp)[0], plane)
        dim_end_xyz = uvToXyz(plane.Project(ep)[0], plane)
        
        return dim_start_xyz, dim_end_xyz
    
def outerPoints(pts):
    n = len(pts)
    max_dist = 0
    outer_pts = ()
    for i in range(n):
        for j in range(i+1, n):
            p1 = pts[i]
            p2 = pts[j]
            dist = p1.DistanceTo(p2)
            if dist > max_dist:
                max_dist = dist
                outer_pts = p1, p2
    return outer_pts

def getOrderedQuantities(rebar_list, plane):
    uv_list = []
    for b in rebar_list:
        location = rebarLocation(b)
        projected = plane.Project(location)[0]
        quantity = str(b.LookupParameter("Quantity").AsInteger())
        uv_list.append((quantity, projected.U, projected.V))
    
    uv_sorted = sorted(uv_list, key = lambda tup: tup[1])
    return [x[0] for x in uv_sorted]

def allSame(list):
    return all([x == list[0] for x in list])
        
#prompt selection of dimension to align to
selection_parent_mra = uidoc.Selection.PickObject(ObjectType.Element, CustomISelectionFilter("Multi-Rebar Annotations"),"Pick main Multi-Rebar Annotation")

#prompt selection of dimensions to align
selection_child_rebar = uidoc.Selection\
    .PickObjects(ObjectType.Element, CustomISelectionFilter("Structural Rebar"),"Pick rebar to associate with main Multi-Rebar Annotation")\

view_dir = active_view.ViewDirection

mra = doc.GetElement(selection_parent_mra)
parent_dim_id = mra.DimensionId
parent_dim_crv = doc.GetElement(parent_dim_id).Curve
op = parent_dim_crv.Origin
crv_dir = parent_dim_crv.Direction
dim_plane = DB.Plane.CreateByOriginAndBasis(op,crv_dir,view_dir)

#get main tagged rebar
rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
    .OfCategory(DB.BuiltInCategory.OST_Rebar)
    
for b in rebar_collector:
    for el_id in b.GetDependentElements(DB.ElementCategoryFilter(DB.BuiltInCategory.OST_MultiReferenceAnnotations)):
        if el_id == selection_parent_mra.ElementId:
            parent_rebar = b

#get dim points for parent rebar
dim_pts = [projectedRebarDistributionPoints(parent_rebar, dim_plane)]
            
#create rebar string to check for similarity
parent_rebar_string = makeRebarString(parent_rebar)

ids_to_hide = []
rebar_quantity_set = [parent_rebar]

for b_ref in selection_child_rebar:
    b = doc.GetElement(b_ref)
    #only add rebar if they have the same rebar type, mark and spacing
    if makeRebarString(b) == parent_rebar_string and b.Id != parent_rebar.Id:
        dim_pts.append(projectedRebarDistributionPoints(b, dim_plane))
        rebar_quantity_set.append(b)
        #rebar_quantities.append(str(b.LookupParameter("Quantity").AsInteger()))
        ids_to_hide.append(b_ref.ElementId)

#create copy of rebar id strings to append annotation ids to
linked_ids = [x.ToString() for x in ids_to_hide]

# check for outermost points on flattened list
# to be used for opening dimline over the whole area
outer_pts = outerPoints(list(sum(dim_pts,())))

#create quantity string
rebar_quantities = getOrderedQuantities(rebar_quantity_set, dim_plane)
  
#get detail item family for distribution lines               
collector = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_DetailComponents)\
    .OfClass(DB.FamilySymbol)\
    .WhereElementIsElementType()\
    .ToElements()
     
dist_family = next(i for i in collector if i.Family.Name == "NE_fördelningslinje")     
dist_opening_family = next(i for i in collector if i.Family.Name == "NE_fördelningslinje_uppehåll")  

mra_collector = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_MultiReferenceAnnotations)\
    .WhereElementIsElementType()\
    .ToElements()
     
mra_group_familytype = next(i for i in mra_collector if i.LookupParameter("Type Name").AsString() == "Structural Rebar 2")     

#remove parent bar points since they have multi-rebar annotation
dim_pts.pop(0)

t = Transaction(doc, 'Group Multi-Rebar Annotations')   
t.Start()

#create distribution lines      
for pts in dim_pts:
    (p1, p2) = pts
    dim_line = DB.Line.CreateBound(p1, p2)
    dline = doc.Create.NewFamilyInstance(dim_line, dist_family, active_view)
    linked_ids.append(dline.Id.ToString())

#create opening distribution line
dim_line = DB.Line.CreateBound(outer_pts[0], outer_pts[1])
dline = doc.Create.NewFamilyInstance(dim_line, dist_opening_family, active_view)
linked_ids.append(dline.Id.ToString())

#create prefix string
if allSame(rebar_quantities) and len(rebar_quantities)>2:
    prefix = str(len(rebar_quantities)) + "x" + rebar_quantities[0]
else:
    prefix = '+'.join(rebar_quantities)
parent_rebar.LookupParameter("CQRebarPrefix").Set(prefix)

#hide grouped rebar
active_view.HideElements(List[DB.ElementId](ids_to_hide))

#change mra type
mra.ChangeTypeId(mra_group_familytype.Id)

#set grouped object ids to parent rebar
id_string = ','.join(linked_ids)
parent_rebar.LookupParameter("Comments").Set(id_string)

t.Commit()

#   TODO
#   Hantera avbryt
#   Hantera tvärgående stänger = line too short
#   Skriv id till huvudstång
#   Fel vid horisontella stänger
#   Felmeddelande vid skippade stänger
#   Script ungroup MRA
#   Script update MRA group
#   Hantera show first/last
   


            
            

