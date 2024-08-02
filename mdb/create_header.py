from enum import Enum

from yamcs.pymdb import *

import sys



class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21


system = System("SCSAT1")
csp_header_name="csp-header"

csp_list=[
    ["csp-priority", uint2_t, 0],
    ["csp-source-id", uint5_t, 0],
    ["csp-dst-id", uint5_t, 0],
    ["csp-dst-port", uint6_t, 0],
    ["csp-source-port", uint6_t, 0],
    ["csp-reserved", uint4_t, 0],
    ["csp-hmac", uint1_t, 0],
    ["csp-xtea", uint1_t, 0],
    ["csp-rdp", uint1_t, 0],
    ["csp-crc", uint1_t, 0],
]


general_container = Container(
    system=system,
    name="scsat1",
    abstract=True,
)


entries_list=[]
for l in csp_list:
    tm = IntegerParameter(
        system=system,
        name=l[0],
        signed=False,
        encoding=l[1],
    )
    entries_list.append(ParameterEntry(tm))


container = Container(
        system=system,
        name=csp_header_name,
        base=general_container ,
        entries=entries_list
    )

with open("mdb/scsat1_header.xml", "wt") as f:
    system.dump(f)
