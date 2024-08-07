from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys

import data.eps_tm as tmd

class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21

def en_set_le(type_name):
    if type_name == "char":
        si = False
        en = StringEncoding()
    elif type_name =="bool":
        si = False
        en = float64le_t
    elif type_name =="double_t":
        si = False
        en = float64le_t
    elif type_name == "float64_t":
        si = False
        en = float32le_t
    elif type_name == int8_t:
        si = True
        en = IntegerEncoding(
                bits=8,
                little_endian=True,
                scheme=IntegerEncodingScheme.TWOS_COMPLEMENT,
            )
    elif type_name == uint8_t:
        si = False
        en = IntegerEncoding(
                bits=8,
                little_endian=True,
                scheme=IntegerEncodingScheme.UNSIGNED,
            )
    elif type_name == uint1_t:
        si = False
        en = uint1_t
    elif type_name == uint16_t:
        si = False
        en = uint16le_t        
    elif type_name == uint32_t:
        si = False
        en = uint32le_t    
    else :
        print("Error: "+ str(type_name) + "is not defined\n")
        sys.exit(1)

    return si,en


def create_header(system,data):
    for cont in data:
        header_container = Container(
            system=system,
            name = cont["name"],
            base = cont["base"],
            abstract = True,
            entries = set_entries_list(system, cont),
            condition = set_conditions(cont),
        )
    return header_container


def set_telemetry(system,data,base,abstract = False):
    for cont in data:
        container = Container(
            system = system,
            name = cont["name"],
            base = base,
            entries = set_entries_list(system, cont),
            abstract = abstract,
            condition = set_conditions(cont),
        )
    return container

def set_entries_list(system, cont):
    try:
        param_data = cont["parameters"]
        entries_list = []
        for param in param_data:
            tm = IntegerParameter(
                system=system,
                name=param["name"],
                signed=False,
                encoding=globals()[param["type"]],
            )
            entries_list.append(ParameterEntry(tm))
        return entries_list
    except:
        return None


def set_conditions(cont):
    try:
        condition_data = cont["conditions"]
        if len(condition_data) > 1:
            exp = []
            for cond in condition_data:
                exp.append(eq(cond["name"], cond["num"], calibrated=True))
            return all_of(*exp)

        else:
            for cond in condition_data:
                exp = eq(cond["name"], cond["num"], calibrated=True)
            return exp
    except:
        return None

def main():
        
    system = System("EPS")
    yaml = YAML()
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/eps_tm.yaml"
    csp_header_name="../csp-header"

    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # EPS Parameter
    header_container = create_header(system,data["headers"])

    # set_telemetry(system,data["containers"],header_container)
  

    for param in tmd.param_list:
        entries_list=[]
        if len(param) == 4:
            for l in param[3]:
                si,en=en_set_le(l[1])
                if l[1] == "double_t":
                    tm = FloatParameter(
                        system=system,
                        name=l[0],
                        bits=64,
                        encoding=en,
                    )
                else:
                    tm = IntegerParameter(
                        system=system,
                        name=l[0],
                        signed=si,
                        encoding=en,
                    )
                entries_list.append(ParameterEntry(tm))

            container = Container(
                    system=system,
                    name=param[0],
                    base = header_container,
                    entries=entries_list,
                    condition = all_of(
                        eq("/SCSAT1/csp-source-port", param[1], calibrated=True),
                        eq("EPS/command_id", param[2], calibrated=True),
                    )
                )
            
    with open("mdb/scsat1_eps.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()