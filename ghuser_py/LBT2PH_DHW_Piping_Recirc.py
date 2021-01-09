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
Creates DHW Recirculation loops for the 'DHW+Distribution' PHPP worksheet. Can create up to 5 recirculation loops. Will take in a DataTree of curves from Rhino and calculate their lengths automatically. Will try and pull curve object attributes from Rhino as well - use attribute setter to assign the pipe diameter, insulation, etc... on the Rhino side.
-
EM November 26, 2020
    Args:
        pipe_geom_: <Tree> A DataTree where each branch describes one 'set' of recirculation piping. 
        PHPP allows up to 5 'sets' of recirc piping. Each 'set' should include the forward and return piping lengths for that distribution leg.
        Use the 'Entwine' component to organize your inputs into branches before inputing if more than one set of piping is passed in.
------
The input here will accept either:
>  A single number representing the length (m) of the total loop in meters
>  A list (multiline input) representing multiple pipe lengths (m). These will be summed together for each branch
>  A curve or curves with no parameter values. The length of the curves will be summed together for each branch. You'll then need to enter the diam, insulation, etc here in the GH Component.
>  A curve or curves with paramerer values applied back in the Rhino scene. If passing in geometry with parameter value, be sure to use an 'ID' component before inputing the geometry here.
        pipe_diam_: <Optional> (mm) A List of numbers representing the nominal diameters (mm) of the pipes in each branch. This will override any values goten from the Rhino scene objects. If only one value is passed, will be used for all objects.
        insulThickness_: <Optional> (mm) A List of numbers representing the insulation thickness (mm) of the pipes in each branch. This will override any values goten from the Rhino scene objects. If only one value is passed, will be used for all objects.
        insulConductivity_: <Optional> (W/mk) A List of numbers representing the insulation conductivity (W/mk) of the pipes in each branch. This will override any values goten from the Rhino scene objects. If only one value is passed, will be used for all objects.
        insulReflective_: <Optional> A List of True/False values for the pipes in each branch. True=Reflective Wrapper, False=No Reflective Wrapper. This will override any values goten from the Rhino scene objects. If only one value is passed, will be used for all objects.
        insul_quality_: ("1-None", "2-Moderate", "3-Good") The Quality of the insulaton installation at the mountings, pipe-suspentions, couplings, valves, etc.. (Note: not the quality of the overall pipe insulation).
        daily_period_: (hours) The usage period in hours/day that the recirculation system operates. Default is 18 hrs/day.
    Returns:
        circulation_piping_: The Recirculation Piping object(s). Connect this to the 'circulation_piping_' input on the 'DHW System' component in order to pass along to the PHPP.
"""

ghenv.Component.Name = "LBT2PH_DHW_Piping_Recirc"
ghenv.Component.NickName = "Piping | Recirc"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Rhino
import rhinoscriptsyntax as rs
import Grasshopper.Kernel as ghK
from collections import namedtuple

import LBT2PH
from LBT2PH.dhw import PHPP_DHW_RecircPipe
from LBT2PH.helpers import convert_value_to_metric

reload( LBT2PH )
reload( LBT2PH.dhw )
reload( LBT2PH.helpers )

# Classes and Defs
def get_values_from_Rhino(_inputs):
    
    def cleanPipeDimInputs(_diam, _thickness):
        # Clean diam, thickness
        if _diam != None:
            if " (" in _diam: 
                _diam = float( _diam.split(" (")[0] )
        
        if _thickness != None:
            if " (" in _thickness: 
                _thickness = float( _thickness.split(" (")[0] )
        
        return _diam, _thickness
    
    # First, see if I can pull any data from the Rhino scene?
    # Otherwise, if its just a number, use that as the length
    lengths, diams, insul_thks, insul_lambdas, refectives = [], [], [], [], []
    for i, input in enumerate( _inputs ):
        try:
            lengths.append( float(LBT2PH.helpers.convert_value_to_metric( input, 'M' )) )
        except AttributeError as e:
            try:
                rhinoGuid = ghenv.Component.Params.Input[0].VolatileData[0][i].ReferenceID
                rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( rhinoGuid )
                
                length = float(rh_obj.CurveGeometry.GetLength())
                
                k = rs.GetUserText(rh_obj, 'insulation_conductivity')
                r = rs.GetUserText(rh_obj, 'insulation_reflective')
                t = rs.GetUserText(rh_obj, 'insulation_thickness')
                d = rs.GetUserText(rh_obj, 'pipe_diameter')
                d, t = cleanPipeDimInputs(d, t)
                
                lengths.append(length)
                diams.append(d)
                insul_thks.append(t)
                insul_lambdas.append(k)
                refectives.append(r)
            except Exception as e:
                msg = str(e)
                msg += "\nSorry, I am not sure what to do with the input: {} in 'pipe_geom_'?\n"\
                      "Please input either a Curve or a number/numbers representing the pipe segments.".format(input)
                ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg )
            
    Output = namedtuple('Output', ['lengths', 'diams', 'insul_thicknesses', 'insul_conductivities', 'insul_reflectives'])
    return Output(lengths, diams, insul_thks, insul_lambdas, refectives)

def clean_input(_input, _unit):
    val_list = [ convert_value_to_metric(val, _unit) for val in _input]
    
    return val_list

# ------------------------------------------------------------------------------
# Build the Default Re-Circulation Pipe Object
circulation_piping_ = PHPP_DHW_RecircPipe()

if pipe_geom_:
    # Get Rhino scene inputs
    rhino_values = get_values_from_Rhino( pipe_geom_ )
    
    if rhino_values.lengths:
        circulation_piping_.lengths = rhino_values.lengths
    if rhino_values.diams:
        circulation_piping_.diams = rhino_values.diams
    if rhino_values.insul_thicknesses:
        circulation_piping_.insul_thicknesses = rhino_values.insul_thicknesses
    if rhino_values.insul_conductivities:
        circulation_piping_.insul_conductivities = rhino_values.insul_conductivities
    if rhino_values.insul_reflectives:
        circulation_piping_.insul_reflectives = rhino_values.insul_reflectives

# ------------------------------------------------------------------------------
# Get GH Component inputs
if pipe_diam_:
    circulation_piping_.diams = clean_input( pipe_diam_, 'MM')
if insulThickness_:
    circulation_piping_.insul_thicknesses = clean_input( insulThickness_, 'MM')
if insulConductivity_:
    circulation_piping_.insul_conductivities = clean_input( insulConductivity_, 'W/MK') 
if insulReflective_:
    circulation_piping_.insul_reflectives = insulReflective_
if insul_quality_:
    circulation_piping_.quality = insul_quality_
if daily_period_:
    circulation_piping_.period = daily_period_

LBT2PH.helpers.preview_obj(circulation_piping_)