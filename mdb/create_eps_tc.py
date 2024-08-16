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

def set_command_base_container(system):
    tc_pri = EnumeratedArgument(
        name = "pri",
        short_description = "Message priority",
        choices=[
            (0, "CRITICAL"),
            (1, "HIGH"),
            (2, "NORMAL"),
            (3, "LOW"),
        ],
        default="NORMAL",
        encoding=uint2_t,
    )

    tc_src = EnumeratedArgument(
        name = "src",
        short_description = "Source",
        choices = ids if ids is not None else [],
        encoding = uint5_t,
    )

    tc_dst = EnumeratedArgument(
        name = "dst",
        short_description="Destination",
        choices = ids if ids is not None else [],
        encoding = uint5_t,
    )

    tc_dport = IntegerArgument(
        name="dport",
        short_description="Destination port",
        signed=False,
        encoding=uint6_t,
    )

    tc_hmac = BooleanArgument(
        name="hmac",
        short_description="Use HMAC verification",
        default=False,
        encoding=uint1_t,
    )

    tc_xtea = BooleanArgument(
        name="xtea",
        short_description="Use XTEA encryption",
        default=False,
        encoding=uint1_t,
    )

    tc_rdp = BooleanArgument(
        name="rdp",
        short_description="Use RDP protocol",
        default=False,
        encoding=uint1_t,
    )

    tc_crc = BooleanArgument(
        name="crc",
        short_description="Use CRC32 checksum",
        default=False,
        encoding=uint1_t,
    )

    tc_container = Command(
        system=system,
        name="general",
        abstract=True,
        arguments=[
            tc_pri,
            tc_src,
            tc_dst,
            tc_dport,
            tc_hmac,
            tc_xtea,
            tc_rdp,
            tc_crc,
        ],
        entries=[
            ArgumentEntry(tc_pri),
            ArgumentEntry(tc_src),
            ArgumentEntry(tc_dst),
            ArgumentEntry(tc_dport),
            FixedValueEntry(
                name="sport",
                binary="20",  # 48
                bits=6,
                short_description="Ephemeral port for outgoing connection",
            ),
            FixedValueEntry(name="reserved", binary="00", bits=4),
            ArgumentEntry(tc_hmac),
            ArgumentEntry(tc_xtea),
            ArgumentEntry(tc_rdp),
            ArgumentEntry(tc_crc),
        ],
    )
    return tc_container


def main():
    yaml = YAML()   
    system = System("EPS")

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

    general_command = set_command_base_container(system)

    # eps固有のCommand
    # port 等は何も指定してない
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
                base = general_command,
                name = tc["name"],
                arguments = [command_id, magic_num],
                entries = [
                    ArgumentEntry(command_id),
                    ArgumentEntry(magic_num),
                ],
            )


    with open("mdb/scsat1_eps.xml", "wt") as f:
        system.dump(f)

if __name__ == '__main__':
    main()