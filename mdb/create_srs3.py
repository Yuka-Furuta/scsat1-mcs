from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys
uint34_t = IntegerEncoding(
    bits=34,
    little_endian=False,
    scheme=IntegerEncodingScheme.TWOS_COMPLEMENT,
)
class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21


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
    system = System("SRS3")
    yaml = YAML()
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/srs3_tm.yaml"

    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # SRS3のoriginal header
    header_container = create_header(system,data["headers"])
    
    # telrmetryの設定
    set_telemetry(system,data["containers"],header_container)

    # ファイル出力
    with open("mdb/scsat1_srs3.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()
