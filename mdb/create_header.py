from ruamel.yaml import YAML
from enum import Enum
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
    yaml = YAML()
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/header.yaml"

    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    system = System("SCSAT1")


    general_container = Container(
        system=system,
        name="scsat1",
        abstract=True,
    )

    ctm.set_telemetry(system,data["containers"],general_container)

    with open("mdb/scsat1_header.xml", "wt") as f:
        system.dump(f)


if __name__ == '__main__':
    main()