"""Aligns tag of selected Muti-rebar annotation with tagged rebar object"""

__author__ = "Niklas Edlind"

from operator import index
from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

active_view_id = doc.ActiveView.Id
active_view = doc.GetElement(active_view_id)

#get selected objects - non-MRAs will be filtered out in comparison with rebar-dependants
selection_ids = uidoc.Selection.GetElementIds()

#get all rebar in active view
rebar_collector = DB.FilteredElementCollector(doc, active_view_id)\
    .OfCategory(DB.BuiltInCategory.OST_Rebar)
    
elbow_offset = 0.3

#create list of tuples containing MRA Id and tagged bar Id
tagged_bars = []

for b in rebar_collector:
    for el_id in b.GetDependentElements(DB.ElementCategoryFilter(DB.BuiltInCategory.OST_MultiReferenceAnnotations)):
        if el_id in selection_ids:
            tagged_bars.append((doc.GetElement(el_id), doc.GetElement(b.Id)))

view_dir = active_view.ViewDirection
            
for mra, bar in tagged_bars:
    for i in range(bar.NumberOfBarPositions):
        if not bar.IsBarHidden(active_view, i):
            #get start and end points of visible bar
            transform = bar.GetShapeDrivenAccessor().GetBarPositionTransform(i)
            b_curves = bar.GetCenterlineCurves(0,1,1,0,i)
            
            #bar point list initialized with startpoint of first segment
            b_pts = [b_curves[0].CreateTransformed(transform).GetEndPoint(0)] 
            
            for crv in b_curves:
                b_pts.append(crv.CreateTransformed(transform).GetEndPoint(1))
            
            sp = b_pts[0]
            for pt in b_pts:
                #second point cant be in same position as first as seen from view direction, or the three points will not determine a plane
                if not (pt.IsAlmostEqualTo(sp) or (sp-pt).CrossProduct(view_dir).IsZeroLength()):
                    ep = pt
                    break
            
            #create bar plane perpendicular to view
            zp = sp.Add(view_dir)
            bar_plane = DB.Plane.CreateByThreePoints(sp,ep,zp)
            
            #get location point of tag 
            tag = doc.GetElement(mra.TagId)
            old_xyz = tag.TagHeadPosition
            new_uv = bar_plane.Project(old_xyz)[0]
            new_xyz = bar_plane.Origin + new_uv.U * bar_plane.XVec + new_uv.V * bar_plane.YVec
            
            #leader elbow position
            
            dist = [pt.DistanceTo(new_xyz) for pt in b_pts]
            min_index = dist.index(min(dist))
            nearest_xyz = b_pts[min_index]
            
            elbow_xyz = nearest_xyz + (new_xyz-nearest_xyz).Normalize().Multiply(elbow_offset)
            
            t = Transaction(doc, 'Align Multi-Rebar Annotation')
            t.Start()
            
            tag.Location.Move(new_xyz - old_xyz)
            
            #tag.HasLeader =True
            tag.LeaderElbow = elbow_xyz
                
            t.Commit()
            
            
# TODO add functionality to set leader elbow position with tag.LeaderElbow(xyz)
			