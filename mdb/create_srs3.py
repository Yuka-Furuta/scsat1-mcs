from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys
import argparse
import module. create_tm as ctm

class Subsystem(Enum):
    EPS = 4
    COM = 2
    ADCS = 3
    YAMCS = 12
    SRS3 = 21

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

def create_srs3_tm(yaml):
    system = System("SRS3")
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/srs3_tm.yaml"

    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # SRS3のoriginal header
    header_container = ctm.create_header(system,data["headers"])

    # telrmetryの設定
    ctm.set_telemetry(system,data["containers"],header_container)

    # ファイル出力
    with open("mdb/scsat1_srs3.xml", "wt") as f:
        system.dump(f)

def main():

    # 参照できる
    yaml = YAML()
    create_header_tm(yaml)
    create_srs3_tm(yaml)

if __name__ == '__main__':
    main()
