# -*- coding: utf-8 -*-

"""Kontrollerar minsta delmått på vald armering"""

__author__ = "Niklas Edlind"

import sys
import os
import math
import json
from Autodesk.Revit import DB
from Autodesk.Revit.DB import UnitUtils, LabelUtils
from Autodesk.Revit.UI.Selection import *
from pyrevit import script, EXEC_PARAMS

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


def check_max_length(length):
    max_length = checkdata["max_length"]
    if length > max_length:
        return ":cross_mark: Maxlängd " + '{:.0f}'.format(length) + " > " + str(max_length)
    else:
        return None


def get_transport_width(rebar):

    bar_type = doc.GetElement(bar.GetTypeId())
    diam = bar_type.BarModelDiameter

    bar_curves = rebar.GetCenterlineCurves(0, 1, 0, 0, 0)
    bar_pts = []

    for crv in bar_curves:
        if "Arc" in crv.GetType().ToString():
            for p in crv.Tessellate():
                bar_pts.append(p)
            bar_pts.pop(-1)  # remove last point to avoid duplicates
        else:
            # start point of all segments
            bar_pts.append(crv.GetEndPoint(0))
     # end point of last segment
    bar_pts.append(crv.GetEndPoint(1))

    # Straight bars
    if len(bar_pts) < 3:
        return 0

    bar_plane = DB.Plane.CreateByThreePoints(
        bar_pts[0], bar_pts[1], bar_pts[2])
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

    return min(dims) + diam


def check_transport_width(width):
    max_width = checkdata["transport_width"]
    if width > max_width:
        return ":warning: Transportbredd " + '{:.0f}'.format(width) + " > " + str(max_width)
    else:
        return None


def check_end_leg(leg_length, diam, bend_radius):
    try:
        minlength = checkdata["end_leg"][str(diam)][str(bend_radius)]
    except:
        return ":cross_mark:" + str(bend_radius) + " är inte standard bockningsradie för Ø" + str(diam)
    if leg_length < minlength:
        return ":cross_mark: Ändskänkelmått " + '{:.0f}'.format(leg_length) + " < " + str(minlength)
    else:
        return None


def check_mid_leg(leg_length, diam, bend_radius):
    try:
        minlength = checkdata["mid_leg"][str(diam)][str(bend_radius)]
    except:
        return ":cross_mark:" + str(bend_radius) + " är inte standard bockningsradie för Ø" + str(diam)
    if leg_length < minlength:
        return ":cross_mark: Delmått " + '{:.0f}'.format(leg_length) + " < " + str(minlength)
    else:
        return None

        # TODO: Hantera key error (= kombinationen av diameter och bockningsradie är icke-standard)


def get_leg_length(line_len, delta_0, delta_1):
    return line_len + delta_0 + delta_1


def get_delta_length(angle, radius, diam):
    if angle > math.pi/2:
        return radius + diam
    else:
        return (radius + diam) * math.tan(angle/2)


# get data for minimum leg lengths
dirname = os.path.dirname(__file__)

# TODO: Hantera inställning av kontrollfil

with open(os.path.join(dirname, "armering_kontrollmått_std.json"), "r") as minlengthfile:
    checkdata = json.load(minlengthfile)

# prompt selection of dimension to align to
try:
    bar_selection = uidoc.Selection.PickObjects(
        ObjectType.Element, CustomISelectionFilter("Structural Rebar"), "Pick bar to check")
except:
    sys.exit("User abort")

errors = {}

for sel in bar_selection:
    eid = sel.ElementId
    bar = doc.GetElement(eid)

    bar_errors = set()

    bar_type = doc.GetElement(bar.GetTypeId())
    diam = int(unit_from_internal(doc, bar_type.BarModelDiameter))
    bend_radius = int(unit_from_internal(
        doc, bar_type.StandardBendDiameter) / 2)

    bar_curves = bar.GetCenterlineCurves(1, 0, 0, 0, 0)

    line_len = []
    angles = []
    radii = []
    previous_line = None

    # check transport width
    transport_width = unit_from_internal(doc, get_transport_width(bar))
    if EXEC_PARAMS.debug_mode:
        print("Transport width = " + str(transport_width))
    check = check_transport_width(transport_width)
    if check:
        bar_errors.add(check)

    if len(bar_curves) == 1:
        check = check_max_length(unit_from_internal(doc, bar_curves[0].Length))
        if check:
            errors[eid] = [check]
        continue

    for crv in bar_curves:
        line_type = crv.GetType().ToString()
        if "Line" in line_type:
            line_len.append(unit_from_internal(doc, crv.Length))
            if previous_line:
                line_dir = crv.Direction
                prev_line_dir = previous_line.Direction
                angles.append(line_dir.AngleTo(prev_line_dir))
            previous_line = crv
        if "Arc" in line_type:
            radii.append(unit_from_internal(doc, crv.Radius) - diam/2)

    # check first leg
    dl = get_delta_length(angles[0], bend_radius, diam)
    leg_length = get_leg_length(
        line_len[0], 0, dl)
    check = check_end_leg(leg_length, diam, bend_radius)
    if check:
        bar_errors.add(check)

    if EXEC_PARAMS.debug_mode:
        print(leg_length)
    dl_prev = dl

    # check mid legs
    for i in range(1, len(line_len)-1):
        dl = get_delta_length(angles[i], bend_radius, diam)
        leg_length = get_leg_length(
            line_len[i], dl_prev, dl)
        check = check_mid_leg(leg_length, diam, bend_radius)
        if check:
            bar_errors.add(check)
        dl_prev = dl

        if EXEC_PARAMS.debug_mode:
            print(leg_length)

    # check last leg
    leg_length = get_leg_length(
        line_len[-1], dl_prev, 0)
    check = check_end_leg(leg_length, diam, bend_radius)
    if check:
        bar_errors.add(check)
    if EXEC_PARAMS.debug_mode:
        print(leg_length)

    if len(bar_errors) > 0:
        errors[eid] = bar_errors

# unit symmbol
if int(doc.Application.VersionNumber) < 2022:
    pass
else:
    format_options = doc.GetUnits().GetFormatOptions(DB.SpecTypeId.Length)
    unit_id = format_options.GetUnitTypeId()
    if unit_id.Empty():
        symbol = ""
    else:
        unit = LabelUtils.GetLabelForUnit(unit_id)

if unit == "Meters":
    dec_format = '{:.3f}'
    symbol = 'm'
elif unit == "Millimeters":
    dec_format = '{:.0f}'
    symbol = 'mm'
else:
    dec_format = '{:.3f}'

if len(errors) > 0:
    for b, err in errors.items():
        print(output.linkify(b))
        for e in err:
            print(e)
else:
    print(":white_heavy_check_mark: Delmått OK!")
