# -*- coding: utf-8 - *-

import clr
from Autodesk.Revit.UI.Selection import *
from Autodesk.Revit.DB import Transaction, Structure
from Autodesk.Revit import DB
from pyrevit import EXEC_PARAMS
import System
import os

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


coupler_name = "Skarvlängd (Coupler)"

# shift-click delete placed couplers
if EXEC_PARAMS.config_mode:
    rebar = DB.FilteredElementCollector(
        doc, active_view_id).OfCategory(DB.BuiltInCategory.OST_Rebar)

    to_delete = []

    for r in rebar:
        for i in [0, 1]:
            existing_coupler_id = r.GetCouplerId(i)
            if existing_coupler_id.IntegerValue > 0:
                existing_coupler = doc.GetElement(existing_coupler_id)
                if doc.GetElement(existing_coupler.GetTypeId()).Family.Name == coupler_name:
                    to_delete.append(existing_coupler_id)

    t = Transaction(doc, 'Ta bort Skarvlängd-coupler')
    t.Start()

    for e in to_delete:
        doc.Delete(e)

    t.Commit()

else:
    # get coupler family

    collector = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Coupler)\
        .OfClass(DB.FamilySymbol)\
        .WhereElementIsElementType()\
        .Where(lambda e: e.Family.Name.Equals(coupler_name))

    if collector.Count <= 0:
        absolute_path = os.path.dirname(__file__)
        fam_path = os.path.join(absolute_path, "Skarvlängd (Coupler).rfa")
        t = Transaction(doc, 'Load skarvlängd-coupler')
        t.Start()
        test = doc.LoadFamily(fam_path)
        t.Commit()
        collector = DB.FilteredElementCollector(doc)\
            .OfCategory(DB.BuiltInCategory.OST_Coupler)\
            .OfClass(DB.FamilySymbol)\
            .WhereElementIsElementType()\
            .Where(lambda e: e.Family.Name.Equals(coupler_name))

    coupler_dict = {}

    for i in collector:
        if i.Family.Name == coupler_name:
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
