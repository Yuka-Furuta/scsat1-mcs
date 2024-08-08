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
    yaml = YAML()   
    system = System("SRS3")

    # SRS3のoriginal header
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/srs3_tm.yaml"
    with open(yaml_file, 'r') as file:
        data = yaml.load(file)
    # telrmetryの設定
    header_container = ctm.create_header(system,data["headers"])
    ctm.set_telemetry(system,data["containers"],header_container)



    yaml_file2 = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/srs3_tc.yaml"
    with open(yaml_file2, 'r') as file:
        tc_data = yaml.load(file)

    general_command = Command(
        system=system,
        name="MyGeneralCommand",
        abstract=True,

    )
    # SRS3固有のCommand

    # port 等は何も指定してない
    for commands in tc_data["default_commands"]:
        for tc in commands["commands"]:
            binary_id = BinaryArgument(
                name = "binary_id",
                encoding = BinaryEncoding(bits=48),
                default = tc["command_id"]
            )

            tc_command = Command(
                system = system,
                base = general_command,
                name = tc["name"],
                arguments = [binary_id],
                entries = [
                    ArgumentEntry(binary_id)
                ],
            )


    with open("mdb/scsat1_srs3.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()