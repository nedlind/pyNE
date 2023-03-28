# -*- coding: utf-8 -*-

"""Opens views and activates workset from saved settings"""

from pyrevit import script, EXEC_PARAMS
__author__ = "Niklas Edlind"

import sys
import os
import json

from Autodesk.Revit import DB
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

rvt_file_path = doc.PathName
dir_path = os.path.dirname(rvt_file_path)

rvt_file_name = os.path.basename(rvt_file_path)

settings_fname = os.path.splitext(rvt_file_name)[0] + "_user_settings.json"
settings_file_path = os.path.join(dir_path, settings_fname)


# save current environment n CTRL-click

if EXEC_PARAMS.config_mode:

    if os.path.exists(settings_file_path):
        os.remove(settings_file_path)

    view_list = [v.ViewId.IntegerValue for v in uidoc.GetOpenUIViews()]

    if doc.IsWorkshared:
        ws_table = doc.GetWorksetTable()
        active_ws = ws_table.GetActiveWorksetId().IntegerValue
    else:
        active_ws = None

    settings = {
        "open_views": view_list,
        "active_ws": active_ws
    }

    with open(settings_file_path, "w") as outfile:
        json.dump(settings, outfile)

# load saved environment on click

else:
    if os.path.isfile(settings_file_path):
        with open(settings_file_path, "r") as f:
            settings = json.load(f)
            for v in settings["open_views"]:
                __revit__.ActiveUIDocument.RequestViewChange(
                    doc.GetElement(DB.ElementId(v)))
            ws = settings["active_ws"]
            if ws:
                ws_table = doc.GetWorksetTable()
                ws_table.SetActiveWorksetId(DB.WorksetId(ws))

    else:
        print(":magnifying_glass_tilted_left: Inga sparade inställningar hittas. Använd SHIFT-klick på kommandot för att spara öppna vyer och aktivt workset för aktivt projekt.")
