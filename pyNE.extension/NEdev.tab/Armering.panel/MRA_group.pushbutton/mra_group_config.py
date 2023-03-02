# -*- coding: utf-8 -*-

"""Config file to specify families to use in MRA group command"""

__author__ = "Niklas Edlind"

from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

class FamItem(forms.TemplateListItem):
    """Wrapper class for family list item"""
    pass

my_config = script.get_config("mra_group_families")

def configure_families():
    """Ask for users for families to use in MRA group"""
    
    # prev_mra_group_families = load_configs()
    
    detail_components = [x for x in DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_DetailComponents)\
    .OfClass(DB.FamilySymbol)\
    .WhereElementIsElementType()\
    .ToElements()]
    
    # det_opening = forms.SelectFromList.show(
    #     sorted(
    #         [FamItem(x, name_attr='FamilyName') for x in detail_components],
    #         key=lambda x: x.name
    #         ),
    #     title = "Välj Detail Item för uppehållslinje",
    #     button_name = "Välj"
    #     # resetfunc = 
    #     )
    
    # det_dist_line = forms.SelectFromList.show(
    #     sorted(
    #         [FamItem(x, name_attr='FamilyName') for x in detail_components],
    #         key=lambda x: x.name
    #         ),
    #     title = "Välj Detail Item för fördelningslinje",
    #     button_name = "Välj"
    #     # resetfunc = 
    #     )
    
    #get mra family
    mra_families = [x for x in DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_MultiReferenceAnnotations)\
    .WhereElementIsElementType()\
    .ToElements()]
    
    mra_fam = forms.SelectFromList.show(
        sorted(
            [FamItem(x, name_attr='LookupParameter('Type Name').AsString()') for x in mra_families],
            key=lambda x: x.name
        ),
        title = "Välj Multi Rebar Annotation",
        button_name = "Välj"
        # resetfunc = 
        )
    
    print(mra_fam)
    
    # if fscats:
    #     save_configs(mra_group_families)
    # return fscats

if __name__ == "__main__":
    configure_families()