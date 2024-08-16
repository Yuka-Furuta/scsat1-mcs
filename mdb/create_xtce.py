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
    parser.add_argument("--data", choices = ["srs3","eps","main","adcs"])

    return parser.parse_args()

def create_header_tm(yaml):
    # yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/header.yaml"

    # with open(yaml_file, 'r') as file:
    #     data = yaml.load(file)

    system = System("SCSAT1")
    csp_header = csp.add_csp_header(system, ids=Subsystem)
    # general_container = Container(
    #     system=system,
    #     name="scsat1",
    #     abstract=True,
    # )

    # ctm.set_telemetry(system,data["containers"],general_container)

    with open("mdb/scsat1_header.xml", "wt") as f:
        system.dump(f)


def create_tm(system,yaml, sys_name):
    yaml_file = f"/home/yuka/myproject/task/scsat1-mcs/mdb/data/{sys_name}_tm.yaml"
    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    # EPS Parameter
    header_container = ctm.create_header(system,data["headers"])

    ctm.set_telemetry(system,data["containers"], header_container)
            


def main():
    # option
    args = get_argument()
    if args.data == None:
        print("Please specify options: --data {srs3,eps,main,adcs}")
        sys.exit(1)

    sys_name = args.data

    yaml = YAML()
    system = System(sys_name.upper())
    csp_header = csp.add_csp_header(system, ids=Subsystem)
    create_header_tm(yaml)
    create_tm(system,yaml,sys_name)

    with open(f"mdb/scsat1_{sys_name}.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()
