from enum import Enum

from yamcs.pymdb import *

import sys

import data.srs3_tm as tmd
import data.srs3_tc as tcd

class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21


system = System("SRS3")
csp_header_name="../csp-header"

#SRS3のheader
srs3_header_list = [
    ["telemetry-id", uint8_t, 0],
    ["srs3-reserved", uint16_t, 0],
    ["srs3-id", uint16_t, 0],
]

entries_list=[]
for l in srs3_header_list:
    tm = IntegerParameter(
        system=system,
        name=l[0],
        signed=False,
        encoding=l[1],
    )
    entries_list.append(ParameterEntry(tm))

srs3_container = Container(
        system=system,
        name="srs3-header",
        base=csp_header_name,
        abstract=True,
        entries=entries_list,
        condition = all_of(
            eq("/SCSAT1/csp-source-id", 21, calibrated=True),
            eq("/SCSAT1/csp-source-port", 19, calibrated=True),
        )
    )


# SRS3専用
for param in tmd.param_list:
    entries_list=[]
    if len(param) == 3:

        for l in param[2]:
            tm = IntegerParameter(
                system=system,
                name=l[0],
                signed=False,
                encoding=l[1],
            )
            entries_list.append(ParameterEntry(tm))

    container = Container(
            system=system,
            name=param[0],
            base=srs3_container,
            entries=entries_list,
            condition = eq("SRS3/srs3-id", param[1], calibrated=True),
        )

with open("mdb/scsat1_srs3.xml", "wt") as f:
    system.dump(f)
