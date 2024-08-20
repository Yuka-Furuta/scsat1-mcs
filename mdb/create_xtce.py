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
    system = System("SCSAT1")
    csp_header = csp.add_csp_header(system, ids=Subsystem)

    with open("mdb/scsat1_header.xml", "wt") as f:
        system.dump(f)


def create_tm(system,yaml, sys_name):
    yaml_file = f"mdb/data/{sys_name}_tm.yaml"
    with open(yaml_file, 'r') as file:
        data = yaml.load(file)

    header_container = ctm.create_header(system,data["headers"])

    ctm.set_telemetry(system,data["containers"], header_container)
            

def set_command(system,csp_header,base,tc_data):
    for commands in tc_data:
        for tc in commands["commands"]:
            # arguments 設定
            arg_list = []
            entries_list = []
            if tc.get("arguments",None) != None:
                for arguments in tc["arguments"]:
                    if arguments.get("type","int") == "int":
                        argument = IntegerArgument(
                            name = arguments["name"],
                            encoding = ctm.set_encoding(arguments, tc.get("endian",False)),
                            default = arguments.get("num",None),
                        )
                    elif arguments.get("type","int") == "binary":
                        argument = BinaryArgument(
                            name = arguments["name"],
                            encoding = ctm.set_encoding(arguments, tc.get("endian",False)),
                            default = arguments.get("num",None),
                        )
                    elif arguments.get("type","int") == "string":
                        # 動作確認してない　mainに含まれるコマンド
                        argument = StringArgument(
                            name = arguments["name"],
                        )
                    else:
                        print("Not defined argument type")
                        sys.exit(1)
                    arg_list.append(argument)
                    entries_list.append(ArgumentEntry(argument))
            
            # Command 作成
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

def create_tc(system,yaml,sys_name):
    yaml_file2 = f"mdb/data/{sys_name}_tc.yaml"
    with open(yaml_file2, 'r') as file:
        tc_data = yaml.load(file)

    csp_header = csp.add_csp_header(system, ids=Subsystem)

    general_command = Command(
        system=system,
        name="MyGeneralCommand",
        abstract=True,
        base=csp_header.tc_container,
        assignments={
            csp_header.tc_dst.name:sys_name.upper(),
            csp_header.tc_src.name: "YAMCS",
        },
    )
    #　一旦別々に呼ぶ形にする　csp_commands を各ファイルに書いているので、、
    set_command(system,csp_header,general_command,tc_data["csp_commands"])
    set_command(system,csp_header,general_command,tc_data["default_commands"])

def main():
    # option
    args = get_argument()
    if args.data == None:
        print("Please specify options: --data {srs3,eps,main,adcs}")
        sys.exit(1)

    sys_name = args.data

    yaml = YAML()
    system = System(sys_name.upper())
    create_header_tm(yaml)
    create_tm(system,yaml,sys_name)
    create_tc(system,yaml,sys_name)

    with open(f"mdb/scsat1_{sys_name}.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()
