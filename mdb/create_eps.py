from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys

import module. create_tm as ctm

class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21


def main():
    system = System("EPS")
    yaml = YAML()
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/eps_tm.yaml"


    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # EPS Parameter
    header_container = ctm.create_header(system,data["headers"])

    ctm.set_telemetry(system,data["containers"], header_container)
            
    with open("mdb/scsat1_eps.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()