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



def csp_common_command(system,csp_header,base,tc_data):
    for commands in tc_data["csp_commands"]:
        for tc in commands["commands"]:
            arg_list = []
            entries_list = []
            if tc.get("arguments",None) != None:
                for arguments in tc["arguments"]:
                    argument = IntegerArgument(
                        name = arguments["name"],
                        encoding = IntegerEncoding(bits = arguments.get("bit",16)),
                    )
                arg_list.append(argument)
                entries_list.append(ArgumentEntry(argument))

            tc_command = Command(
                system = system,
                base = base,
                name = tc["name"],
                assignments={
                    csp_header.tc_dport.name: tc["port"],
                }, 
                arguments = arg_list,
                entries = entries_list,
            )

def eps_command(system,csp_header,base,tc_data):
    for commands in tc_data["default_commands"]:
        for tc in commands["commands"]:
            command_id = IntegerArgument(
                name = "command_id",
                encoding = IntegerEncoding(bits=8),
                default = tc["command_id"]
            )
            magic_num = IntegerArgument(
                name = "magic_num",
                encoding = IntegerEncoding(bits=16),
                default = tc["magic_num"]
            )

            tc_command = Command(
                system = system,
                base = base,
                name = tc["name"],
                arguments = [command_id, magic_num],
                entries = [
                    ArgumentEntry(command_id),
                    ArgumentEntry(magic_num),
                ],
            )



def main():
    yaml = YAML()   
    system = System("EPS")
    csp_header = csp.add_csp_header(system, ids=Subsystem)

    # EPSのoriginal header
    yaml_file = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/eps_tm.yaml"
    with open(yaml_file, 'r') as file:
        data = yaml.load(file)
    # telrmetryの設定
    header_container = ctm.create_header(system,data["headers"])
    ctm.set_telemetry(system,data["containers"],header_container)



    yaml_file2 = "/home/yuka/myproject/task/scsat1-mcs/mdb/data/eps_tc.yaml"
    with open(yaml_file2, 'r') as file:
        tc_data = yaml.load(file)

    general_command = Command(
        system=system,
        name="MyGeneralCommand",
        abstract=True,
        base=csp_header.tc_container,
        assignments={
            csp_header.tc_dst.name:4,
            csp_header.tc_src.name: 12,
        },
    )

    csp_common_command(system,csp_header,general_command,tc_data)
    # port 等は何も指定してない
    eps_command(system,csp_header,general_command,tc_data)


    with open("mdb/scsat1_eps.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()