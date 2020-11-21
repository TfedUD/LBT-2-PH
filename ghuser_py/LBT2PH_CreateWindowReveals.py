#
# LBT2PH: A Plugin for creating Passive House Planning Package (PHPP) models from LadybugTools. Created by blgdtyp, llc
# 
# This component is part of the PH-Tools toolkit <https://github.com/PH-Tools>.
# 
# Copyright (c) 2020, bldgtyp, llc <phtools@bldgtyp.com> 
# LBT2PH is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# LBT2PH is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
#
"""
Will create geometry for the window 'reveals' (the sides, top and bottom for windows which are installed in a host surface). These are used to accurately calcualte the window shading factors. Will also generate 'punched' envelope surface geometry to allow for accurate shading assessment.
-
EM November 21, 2020
    Args:
        _HBZones: (list) The Honeybee Zones for analysis
        moveWindows_: (bool) True = will move the window surfaces based on their 'InstallDepth' parameter. Use this if you want to push the windows 'in' to the host surface for the shading calculations. False = will not move the window surfaces.
    Returns:
        HBZones_: The updated Honeybee Zone objects to pass along to the next step.
        windowNames_: A list of the window names in the order calculated.
        windowSurfaces_: The window surfaces in the same order as the "windowNames_" output. If "moveWindows_" is set to True, these surfaces will be pushed 'in' according to their 'InstallDepth' parameter and surface normal.
        windowSurrounds_: (Tree) Each branch represents one window object. The surfaces in each branch correspond to the Bottom, Left, Top and Right 'reveal' surfaces. Use this to calculate the shading factors for the window surface.
        envelopSrfcs: The Honeybee zone surfaces, except with all the windows 'punched' out. 
"""

ghenv.Component.Name = "LBT2PH_CreateWindowReveals"
ghenv.Component.NickName = "Create Window Reveals"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

from ladybug_rhino.fromgeometry import from_face3d 

import LBT2PH
import LBT2PH.windows

reload( LBT2PH )
reload( LBT2PH.windows )

window_surrounds_ = DataTree[Object]()
envelope_surfaces_ = []
window_names_ = []
window_surfaces_ = []
envelope_surfaces_punched = []

count = 0
for hb_room in _HB_rooms:
    for face in hb_room.faces:
        # ----------------------------------------------------------------------
        # Envelope Surfaces for shading
        envelope_surfaces_punched.append( from_face3d(face.punched_geometry) )
        envelope_surfaces_.append( from_face3d(face.geometry) )
        
        # ----------------------------------------------------------------------
        # Window Surfaces and reveal geometry
        if not face.apertures:
            continue
        
        for aperture in face.apertures:
            name = aperture.display_name
            try:
                phpp_window = LBT2PH.windows.PHPP_Window.from_dict( aperture.user_data['phpp'] )
                window_surrounds_.AddRange( phpp_window.reveal_geometry, GH_Path(count)  )
                window_surfaces_.append( phpp_window.inset_window_surface )
                window_names_.append( name )
                count += 1
            except KeyError as e:
                print('No "phpp" data found on the aperture.user_data for {}?'.format(name), e)
                pass
            except TypeError as e:
                print('No "phpp" data found on the aperture.user_data for {}?'.format(name), e)
                pass

# ------------------------------------------------------------------------------
HB_rooms_ = _HB_rooms
