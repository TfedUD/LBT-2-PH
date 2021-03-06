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
Used to apply Winter and Summer Shading Factors to the Honeybee Model's windows. These shading factors can come from any source but should always be 0<-->1 with 0=fully shaded window and 1=fully unshaded window.
Note: Be sure that the order of the windowNames and the shading factors match each other.
-
EM December 9, 2020
    Args:
        _HB_rooms: (List)
        _windowNames: (List) The window names in the HB Model being analyzed. The order of this list should match the order of the Shading Factors input.
        _winter_shading_factors: (List) The winter shading factors (0=fully shaded, 1=fully unshaded). The length and order of this list should match the "_windowNames" input.
        _summer_shading_factors: (List) The summer shading factors (0=fully shaded, 1=fully unshaded). The length and order of this list should match the "_windowNames" input.
    Returns:
        HBZones_: The updated Honeybee Zone objects to pass along to the next step.
"""

ghenv.Component.Name = "LBT2PH_ApplyWindowShadingFactors"
ghenv.Component.NickName = "Apply Win. Shading Factors"
ghenv.Component.Message = 'DEC_09_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Grasshopper.Kernel as ghK
from collections import namedtuple

import LBT2PH
import LBT2PH.windows

reload( LBT2PH )
reload( LBT2PH.windows )

if len(_window_names) != len(_winter_shading_factors) or len(_window_names) != len(_summer_shading_factors):
    warning = "The number of windows in the HB Model doesn't match the shading factor inputs?\n"\
    "Check the HB Model / shading factor values. For now I'll use 0.75 for all the missing ones."
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)

# ------------------------------------------------------------------------------
# Build the window param dict
Params = namedtuple('Params', ['winter', 'summer'])
param_dict = {}
for i, window_name in enumerate(_window_names):

    try:
        winter_factor= float(_winter_shading_factors[i])
    except IndexError as e:
        winter_factor = 0.75
    except SystemError as e:
        winter_factor = 0.75
    
    try:
        summer_factor= float(_summer_shading_factors[i])
    except IndexError as e:
        summer_factor = 0.75
    except SystemError as e:
        summer_factor = 0.75
    
    param_dict[window_name] = Params(winter_factor, summer_factor)


# ------------------------------------------------------------------------------
HB_rooms_ = []
for room in _HB_rooms:
    new_room = room.duplicate()
    for face in new_room.faces:
        for aperture in face.apertures:
            # ------------------------------------------------------------------
            # Re-Build the PHPP_Window
            name = aperture.display_name
            try:
                phpp_window = LBT2PH.windows.PHPP_Window.from_dict( aperture.user_data['phpp'] )
            except KeyError as e:
                print('No "phpp" data found on the aperture.user_data for {}?'.format(name), e)
                continue
            except TypeError as e:
                print('No "phpp" data found on the aperture.user_data for {}?'.format(name), e)
                continue
            
            # ------------------------------------------------------------------
            # Set the Window's Shading Factor information
            window_factors = param_dict.get( name, None)
            
            if not window_factors:
                msg = "Error finding a matching name for Honeybee Aperture {}?".format(name)
                continue
            
            phpp_window.shading_factor_winter = window_factors.winter
            phpp_window.shading_factor_summer = window_factors.summer
            phpp_window.shading_dimensions = None
            
            # ------------------------------------------------------------------
            # Pack everything onto the Aperture
            user_data = {}
            user_data['phpp'] = phpp_window.to_dict()
            aperture.user_data = user_data
            
    HB_rooms_.append( new_room )

# ------------------------------------------------------------------------------
# Warnings
for k, v in param_dict.items():
    if 0 in v:
        warn = "Warning. One or more windows have a calculated shading factor of 0?\n"\
        "Thats probably not right. Double check window: {}. It might have its surface normal\n"\
        "backwards or something else funny is happening with your shading surfaces? Double check.".format(k)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warn)