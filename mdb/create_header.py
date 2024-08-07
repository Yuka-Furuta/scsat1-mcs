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


    for cont in data["containers"]:
        container = Container(
                system=system,
                name=cont["name"],
                base=general_container ,
                entries=set_entries_list(system, cont),
            )

    with open("mdb/scsat1_header.xml", "wt") as f:
        system.dump(f)




if __name__ == '__main__':
    main()