# -*- coding: utf-8 - *-

import clr
from Autodesk.Revit.UI.Selection import *
from Autodesk.Revit.DB import Transaction, Structure
from Autodesk.Revit import DB
import System

"""Lägger till coupler på vald armering för att visuellt granska skarvlängder"""

__author__ = "Niklas Edlind"


clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

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


def addCoupler(id):

    rebar = doc.GetElement(id)
    bar_type_id = rebar.GetTypeId()
    bar_diam = doc.GetElement(bar_type_id).BarModelDiameter

    for i in [0, 1]:
        existing_coupler_id = rebar.GetCouplerId(i).IntegerValue
        if existing_coupler_id < 0:
            rebarData = Structure.RebarReinforcementData.Create(id, i)
            Structure.RebarCoupler.Create(
                doc, coupler_dict[bar_diam], rebarData, None)


# get coupler family

collector = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_Coupler)\
    .OfClass(DB.FamilySymbol)\
    .WhereElementIsElementType()\
    .Where(lambda e: e.Family.Name.Equals("Skarvlängd (Coupler)"))

if collector.Count <= 0:
    t = Transaction(doc, 'Load skarvlängd-coupler')
    t.Start()
    test = doc.LoadFamily(
        "t:/05_Personliga_mappar/Niklas_Edlind/test/Skarvlängd (Coupler).rfa")
    t.Commit()
    collector = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Coupler)\
        .OfClass(DB.FamilySymbol)\
        .WhereElementIsElementType()\
        .Where(lambda e: e.Family.Name.Equals("Skarvlängd (Coupler)"))

coupler_dict = {}

for i in collector:
    if i.Family.Name == "Skarvlängd (Coupler)":
        bar_type_id = i.Parameter[DB.BuiltInParameter.COUPLER_MAIN_BAR_SIZE].AsElementId(
        )
        diam = doc.GetElement(bar_type_id).BarModelDiameter
        coupler_dict[diam] = i.Id


# prompt selection of rebar
selection_rebar = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilter(
    "Structural Rebar"), "Välj armering att lägga till skarvlängdscoupler på")

t = Transaction(doc, 'Skarvlängd-coupler')
t.Start()

for s in selection_rebar:
    addCoupler(s.ElementId)

t.Commit()
