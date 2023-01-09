# -*- coding: utf-8 -*-

import sys
import os

from pyrevit import script
output = script.get_output()

with open(os.path.join(sys.path[0], "release-notes.md"), "r") as f:
    md_str = f.read().decode('utf-8')
    output.print_md(md_str)



