from ruamel.yaml import YAML
from enum import Enum
from yamcs.pymdb import *
import sys


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
    csp_header_name="csp-header"


    general_container = Container(
        system=system,
        name="scsat1",
        abstract=True,
    )


    entries_list=[]

    for key in data["parameters"].keys():
        for param in data["parameters"][key]:
            tm = IntegerParameter(
                system=system,
                name=param["name"],
                signed=False,
                encoding=globals()[param["type"]]
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




if __name__ == '__main__':
    main()