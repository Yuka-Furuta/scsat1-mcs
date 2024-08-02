from enum import Enum

from yamcs.pymdb import *

import sys
import data.eps_tm as tmd

class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21

system = System("EPS")
csp_header = csp.add_csp_header(system, ids=Subsystem)
csp_header_name="../csp-header"

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


# EPS Parameter
tm_command_id = IntegerParameter(
    system=system,
    name="command_id",
    signed=False,
    encoding=uint8_t,
)

eps_container = Container(
    system=system,
    name="esp_container",
    base=csp_header_name,
    entries=[
        ParameterEntry(tm_command_id),
    ],
    condition = eq("/SCSAT1/csp-source-id", 4, calibrated=True),
)

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
                base = eps_container,
                entries=entries_list,
                condition = all_of(
                    eq("/SCSAT1/csp-source-port", param[1], calibrated=True),
                    eq("EPS/command_id", param[2], calibrated=True),
                )
            )
        
with open("mdb/scsat1_eps.xml", "wt") as f:
    system.dump(f)