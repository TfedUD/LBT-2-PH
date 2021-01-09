from contextlib import contextmanager
from copy import deepcopy
import scriptcontext as sc
import Rhino
from copy import deepcopy
import re
import Grasshopper.Kernel as ghK

from honeybee.typing import clean_and_id_ep_string
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier


def add_to_HB_model( _hb_model, _key, _dict, _ghenv, _write='update' ):

    user_data = deepcopy( _hb_model.user_data )
    if not user_data:
        _hb_model.user_data = {'phpp': { _key: _dict} }
        return _hb_model
    
    try:
        if _write == 'update':
            user_data['phpp'][_key].update( _dict )
        elif _write == 'overwrite':
            user_data['phpp'][_key] = _dict
    except KeyError as e:
        try:
            user_data['phpp'].update( {_key:_dict } )
        except KeyError:
            try:
                user_data = {'phpp':{_key:_dict }}
            except Exception as e:
                msg = e
                msg += 'Error writing data to the model user_data?'
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Error, msg )

    _hb_model.user_data = user_data
    return _hb_model

#
#
#
# Remove?
def add_to_hb_obj_user_data(_hb_obj, key, _val):
    if _hb_obj.user_data is None:
        _hb_obj.user_data = {}
    
    if not isinstance(_hb_obj.user_data, dict):
        raise Exception
    
    # Decided to do a deepcopy here, otherwise ref pointer always
    # goes to the same dict which makes it confusing as things are added/edited.
    # I dont *think* it would error without the copy? But more predictable with it.
    new_user_data = deepcopy(_hb_obj.user_data)
    if new_user_data.has_key('phpp'):
        if new_user_data['phpp'].has_key(key):
            new_user_data['phpp'][key].update(_val)
        else:
            new_user_data['phpp'][key] = _val
    else:
        new_user_data['phpp'] = {}
        new_user_data['phpp'][key] = _val
    
    _hb_obj.user_data = new_user_data
    
    return _hb_obj
#
#
#
#

@contextmanager
def context_rh_doc(_ghdoc):
    ''' Switches the sc.doc to the Rhino Active Doc temporaily '''
    if not _ghdoc:
        return

    try:
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        yield
    finally:
        sc.doc = _ghdoc

def preview_obj(_classObj):
    ''' For looking at the contents of a Class Object '''

    if not hasattr(_classObj, '__dict__'):
    	print('{} object "{}" has no "__dict__" attribute.'.format(type(_classObj), _classObj))
    	return None
    
    print('-------')
    for item_key, item in _classObj.__dict__.items():
        print(item_key, "::", item)
        try:
            for k, v in item.__dict__.items():
                print("   > {} :: {}".format(k, v))
        except:
            pass

def find_input_string(_in):
    """ Util func  used by the unit converter """
    
    evalString = str(_in).upper()
    
    if 'FT' in evalString or "'" in evalString:
        inputUnit = 'FT'
    elif 'IN' in evalString or '"' in evalString:
        inputUnit = 'IN'
    elif 'MM' in evalString:
        inputUnit = 'MM'
    elif 'CM' in evalString:
        inputUnit = 'CM'
    elif 'M' in evalString and 'MM' not in evalString:
        inputUnit = 'M'
    elif 'IP' in evalString:
        inputUnit = 'IP'
    elif 'FT3' in evalString:
        inputUnit = 'FT3'
    else:
        inputUnit = 'SI'
    
    return inputUnit

def convert_value_to_metric(_inputString, _outputUnit):
    """ Will convert a string such as "12 FT" into the corresponding Metric unit
    
    Arguments:
        _inputString: String: The input value from the user
        _outputUnit: String: ('M', 'CM', 'MM', 'W/M2K', 'W/MK', 'M3') The desired unit
    """
    schema = {
                'M':{'SI': 1, 'M':1, 'CM':0.01, 'MM':0.001, 'FT':0.3048, "'":0.3048, 'IN':0.0254, '"':0.0254},
                'CM':{'SI': 1, 'M':100, 'CM':1, 'MM':0.1, 'FT':30.48, "'":30.48, 'IN':2.54, '"':2.54},
                'MM':{'SI': 1, 'M':1000, 'CM':10, 'MM':1, 'FT':304.8, "'":304.8, 'IN':25.4, '"':25.4},
                'W/M2K':{'SI':1, 'IP':5.678264134}, # IP=Btu/hr-sf-F
                'W/MK':{'SI':1, 'IP':1.730734908}, #IP=Btu/hr-ft-F
                'M3':{'SI':1, 'FT3':0.028316847},
              }
    
    inputValue = _inputString
    
    if _inputString is None:
        return None
    
    try:
        return float(inputValue)
    except:
        try:
            # Pull out just the decimal numeric characters, if any
            for each in re.split(r'[^\d\.]', _inputString):
                if len(each)>0:
                    inputValue = each
                    break # so it will only take the first number found, "123 ft3" doesn't work otherwise
            
            inputUnit = find_input_string(_inputString)
            conversionFactor = schema.get(_outputUnit, {}).get(inputUnit, 1)
            return float(inputValue) * float(conversionFactor)
        except:
            return inputValue

def create_hb_constant_schedule(_name, _type_limit='Fractional'):
    type_limit = schedule_type_limit_by_identifier( _type_limit )

    schedule = ScheduleRuleset.from_constant_value(
        clean_and_id_ep_string(_name), 1, type_limit)

    schedule.display_name = _name

    return schedule


def langDict(self):
    #nested dict for multi-language PHPP interop
    
    self.langDict = {
        'Instructions':{'English': 'Instructions', 'German': 'Anleitung'},
        'Verification':{'English': 'Verification', 'German': 'Nachweis'},
        'Check': {'English': 'Check', 'German': 'Kontrolle'},
        'Climate': {'English': 'Climate', 'German': 'Klima'},
        'U-Values': {'English': 'U-Values', 'German': 'U-Werte'},
        'Areas': {'English': 'Areas', 'German': 'Flächen'},
        'Ground': {'English': 'Ground', 'German': 'Erdreich'},
        'Components': {'English': 'Components', 'German': 'Komponenten'},
        'Windows': {'English': 'Windows', 'German': 'Fenster'},
        'Shading': {'English': 'Shading', 'German': 'Verschattung'},
        'Ventilation': {'English': 'Ventilation', 'German': 'Lüftung'},
        'Additional Vent': {'English': 'Additional Vent', 'German': 'Zusatz Lüftg.'},
        'Annual heating': {'English': 'Annual heating', 'German': 'HeizJahr'},
        'Heating': {'English': 'Heating', 'German': 'Heizung'},
        'Heating Load': {'English': 'Heating Load', 'German': 'Heizlast'},
        'SummVent': {'English': 'SummVent', 'German': 'SommLuft'},
        'Summer': {'English': 'Summer', 'German': 'Sommer'},
        'Cooling': {'English': 'Cooling', 'German': 'Kühlung'},
        'Cooling units': {'English': 'Cooling units', 'German':'Kühlgeräte'},
        'Cooling load': {'English': 'Cooling load', 'German': 'Küllast'},
        'DHW+Distribution': {'English': 'DHW+Distribution', 'German': 'WW+Verteil'},
        'SolarDHW': {'English': 'SolarDHW', 'German': 'SolarWW'},
        'PV': {'English': 'PV', 'German': 'PV'},
        'Electricity': {'English': 'Electricity', 'German': 'Strom'},
        'Use non-res': {'English': 'Use non-res', 'German': 'Nutz NiWo'},
        'Electricity non-res': {'English': 'Electricity non-res', 'German': 'Strom NiWo'},
        'Aux Electricity': {'English': 'Aux Electricity', 'German': 'Hilfsstrom'},
        'IHG': {'English': 'IHG', 'German': 'IWQ'},
        'IHG non-res': {'English': 'IHG non-res', 'German': 'IWQ NiWo'},
        'PER': {'English': 'PER', 'German': 'PER'},
        'Compact': {'English': 'Compact', 'German': 'Kompakt'},
        'HP': {'English': 'HP', 'German': 'WP'},
        'HP Ground': {'English': 'HP Ground', 'German': 'WP Erde'},
        'Boiler': {'English': 'Boiler', 'German': 'Kessel'},
        'District heating': {'English': 'District heating', 'German': 'Fernwärme'},
        'Data': {'English': 'Data', 'German': 'Daten'}}