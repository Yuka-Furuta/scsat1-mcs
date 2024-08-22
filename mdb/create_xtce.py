from enum import Enum
from ruamel.yaml import YAML
from yamcs.pymdb import *

import sys
import argparse

class Subsystem(Enum):
    EPS = 4
    MAIN = 1
    ADCS = 1
    YAMCS = 22
    SRS3 = 21

def set_encoding(param, endian):
    param_type = param.get("type", "int")
    if param_type == "int":
        if param.get("signed", False) == False:
            scheme = IntegerEncodingScheme.UNSIGNED
        else:
            scheme = IntegerEncodingScheme.TWOS_COMPLEMENT
        enc = IntegerEncoding(
            bits = param.get("bit", 16),
            little_endian=endian,
            scheme=scheme,
        )
    elif param_type == "double" or param_type == "float":
        enc = FloatEncoding(
            bits = param.get("bit", 64),
            little_endian=endian,
            scheme=FloatEncodingScheme.IEEE754_1985
        )
    elif param_type == "string":
        enc = StringEncoding(
            bits = param.get("bit", 32)*8,
        )
    elif param_type == "binary":
        enc = BinaryEncoding(
            bits = param.get("bit", 48),
        )
    else :
        print(f"encoding error: {param_type} is not defined.")
    
    return enc


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
            base = cont.get("base",base),
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
            if param.get("type", "int") == "int":
                tm = IntegerParameter(
                    system = system,
                    name = param["name"],
                    signed = param.get("signed", False),
                    encoding = set_encoding(param, cont.get("endian",False)),
                )
            elif param.get("type", "int") == "double" or param.get("type", "int") == "float":
                tm = FloatParameter(
                    system = system,
                    name = param["name"],
                    bits = param.get("bit", 64),
                    encoding = set_encoding(param, cont.get("endian",False)),
                )
            elif param.get("type", "int") == "string":
                tm = StringParameter(
                    system = system,
                    name = param["name"],
                    encoding = set_encoding(param, cont.get("endian",False)),
                )
            elif param.get("type", "int") == "binary":
                tm = BinaryParameter(
                    system = system,
                    name = param["name"],
                    encoding = set_encoding(param, cont.get("endian",False)),
                )
            else:
                print(f"set parameter error: "+param["name"]+"\n")

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
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.load(file)

        header_container = create_header(system,data["headers"])

        set_telemetry(system,data["containers"], header_container)
    except:
        print(f"Warning: Telemetry was not created. '{yaml_file}' does not exist.")
            

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
                            encoding = set_encoding(arguments, tc.get("endian",False)),
                            default = arguments.get("num",None),
                        )
                    elif arguments.get("type","int") == "binary":
                        argument = BinaryArgument(
                            name = arguments["name"],
                            encoding = set_encoding(arguments, tc.get("endian",False)),
                            default = arguments.get("num",None),
                        )
                    elif arguments.get("type","int") == "string":
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
    yaml_file = f"mdb/data/{sys_name}_tc.yaml"
    try:
        with open(yaml_file, 'r') as file:
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
    except:
        print(f"Warning: Command was not created. '{yaml_file}' does not exist.")

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
