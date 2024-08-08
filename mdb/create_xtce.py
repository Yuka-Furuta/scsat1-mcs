from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys
import argparse
import module. create_tm as ctm

# main 未定義
class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21

def get_argument():
    # オブジェクト生成
    parser = argparse.ArgumentParser()
    # 引数設定
    parser.add_argument("--data")

    return parser.parse_args()

def create_header_tm(yaml):
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


def create_tm(yaml, sys_name):
    system = System(sys_name.upper())

    yaml_file = f"/home/yuka/myproject/task/scsat1-mcs/mdb/data/{sys_name}_tm.yaml"
    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # EPS Parameter
    header_container = ctm.create_header(system,data["headers"])

    ctm.set_telemetry(system,data["containers"], header_container)
            
    with open(f"mdb/scsat1_{sys_name}.xml", "wt") as f:
        system.dump(f)


def main():
    # option
    args = get_argument()

    yaml = YAML()
    create_header_tm(yaml)
    create_tm(yaml,args.data)

if __name__ == '__main__':
    main()
