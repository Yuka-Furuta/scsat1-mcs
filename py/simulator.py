#!/usr/bin/env python3
import sys
import re
import binascii
import socket
import argparse
import requests
import struct
import time
import numpy as np
from dataclasses import dataclass
from threading import Thread
from time import sleep

parser = argparse.ArgumentParser(description='Yamcs Simulator')
# simulator
parser.add_argument('--yamcs-url',    type=str, default='http://localhost:8090', help='Yamcs URL')
parser.add_argument('--instance', type=str, default='scsat1', help='Yamcs instance')
parser.add_argument('--test-tm', required=True, help='Telemetry full name to test')

# telemetry
parser.add_argument('--tm-host',    type=str, default='127.0.0.1', help='TM host')
parser.add_argument('--tm-port',    type=int, default=52004,       help='TM port')
parser.add_argument('-i', '--tm-interval', type=float, default=1.0, help='TM playback interval (seconds)')

# telecommand
parser.add_argument('--tc-host', type=str, default='127.0.0.1', help='TC host')
parser.add_argument('--tc-port', type=int, default=52002,      help='TC port')

args = vars(parser.parse_args())
# simulator
YAMCS_URL = args['yamcs_url']
INSTANCE = args['instance']
TEST_TM = args['test_tm']

# telemetry
TM_SEND_ADDRESS = args['tm_host']
TM_SEND_PORT = args['tm_port']
TM_INTERVAL = args['tm_interval']

# telecommand
TC_RECEIVE_ADDRESS = args['tc_host']
TC_RECEIVE_PORT = args['tc_port']

DEFAULT_A = 10
DEFAULT_F = 0.5
SYSTEM_DICT = {
    "YAMCS": 10,
    "SRS3":  2,
    "EPS":   4,
    "MAIN":  8,
    "ADCS": 16,
    "ZERO": 24,
    "PICO": 26
}


@dataclass
class CspHeaderField:
    value: int = 0
    bit: int = 1
    sign: bool = False


class Telemetry:
    def __init__(self, tm_dict):
        self.dst = "YAMCS"
        self.src = self.src = tm_dict.get("csp_src", None)
        self.sport = tm_dict.get("csp_sport", 0)
        self.dport = tm_dict.get("csp_dport", 0)
        self.srs3_reserved = self.srs3_id = tm_dict.get("srs3_reserved", 99)
        self.srs3_id = tm_dict.get("srs3_id", 99)
        if "command_id" in tm_dict:
            self.command_id = tm_dict["command_id"]
        elif "telemetry_id" in tm_dict:
            self.command_id = tm_dict["telemetry_id"]
        else:
            self.command_id = None

    def set_header(self):
        fields = [
            CspHeaderField(bit=2),  # Priority
            CspHeaderField(value=SYSTEM_DICT[self.src], bit=5),  # Source
            CspHeaderField(value=SYSTEM_DICT[self.dst], bit=5),  # Destination
            CspHeaderField(value=self.dport, bit=6),  # DPort
            CspHeaderField(value=self.sport, bit=6),  # SPort
            CspHeaderField(bit=4),    # Reserved
            CspHeaderField(),         # HMAC
            CspHeaderField(),         # XTEA
            CspHeaderField(value=1),  # RDP
            CspHeaderField(),         # CRC
        ]
        hsum = 0
        for field in fields:
            hsum = (hsum << field.bit) | field.value
        return bytearray(hsum.to_bytes(4, byteorder='big'))


class Simulator():
    def __init__(self, interval, data):
        self.tm_counter = 0
        self.tc_counter = 0
        self.tm_thread = None
        self.tc_thread = None
        self.last_tc = None
        self.interval = interval
        self.data = data

    def start(self):
        self.tm_thread = Thread(target=send_tm, args=(self,))
        self.tm_thread.daemon = True
        self.tm_thread.start()
        self.tc_thread = Thread(target=receive_tc, args=(self,))
        self.tc_thread.daemon = True
        self.tc_thread.start()

    def print_status(self):
        cmdhex = None
        if self.last_tc:
            cmdhex = binascii.hexlify(self.last_tc).decode('ascii')
        return 'Sent: {} packets. Received: {} commands. Last command: {}'.format(
                        self.tm_counter, self.tc_counter, cmdhex)


def send_tm(simulator):
    data = simulator.data
    restriction_dict = collect_restrictions(data)
    telemetry_data = Telemetry(restriction_dict)
    tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    simulator.tm_counter = 1
    header = telemetry_data.set_header()
    t = 0
    while True:
        packet = header + set_data(data, telemetry_data, t)
        tm_socket.sendto(packet, (TM_SEND_ADDRESS, TM_SEND_PORT))
        simulator.tm_counter += 1
        t += 1
        sleep(simulator.interval)


def set_data(data, telemetry_data, t):
    packet_data = parameters_data(data, t)
    if telemetry_data.src == "SRS3" and telemetry_data.sport == 19:
        srs3 = bytearray(telemetry_data.srs3_reserved.to_bytes(2, byteorder='big')) \
                + bytearray(telemetry_data.srs3_id.to_bytes(2, byteorder='big'))
        b_id = bytearray(1) + srs3
    elif telemetry_data.command_id is None:
        return packet_data
    else:
        b_id = bytearray(telemetry_data.command_id.to_bytes(1, byteorder='big'))
    return b_id + packet_data


def parameters_data(data, t):
    type_map = {
        ("INTEGER", 1, True): "b",
        ("INTEGER", 1, False): "B",
        ("INTEGER", 2, True): "h",
        ("INTEGER", 2, False): "H",
        ("INTEGER", 4, True): "i",
        ("INTEGER", 4, False): "I",
        ("INTEGER", 8, True): "q",
        ("INTEGER", 8, False): "Q",
        ("FLOAT", 4, True): "f",
        ("FLOAT", 8, True): "d",
        ("DOUBLE", 8, False): "d",
    }
    packet = bytearray()
    b_data = b''
    b_int = 0
    b_bitlen = 0
    entries = data.get("entry", [])
    p_a = DEFAULT_A
    p_f = DEFAULT_F
    for entry in entries:
        # Get parameter setting by API
        location = entry.get("locationInBits", 0)
        paramter = entry.get("parameter")
        p_name = paramter.get("name")
        p_signed = paramter.get("signed", True)
        parameter_type_data = paramter.get("type")
        if not parameter_type_data:
            return None
        encoding_data = parameter_type_data.get("dataEncoding")
        p_type = encoding_data.get("type")
        p_endian = encoding_data.get("littleEndian")
        p_bits = encoding_data.get("sizeInBits")
        # True: little-endian, False: big-endian
        en = '<' if p_endian else '>'
        p_byte = p_bits // 8
        # Set data creation mode by parameter name
        if re.search(r'TEMP', p_name):
            p_simulate = "Wave"
        elif re.search(r'TIMESTAMP|WALL_CLOCK', p_name):
            p_simulate = "Time"
        else:
            p_simulate = "Liner"
        # Offset
        if location >= 8:
            packet += bytearray(b_data) + bytearray(location//8)
            b_data = b''
        # Creating parameter data
        if p_type == "BINARY":
            y = create_data(p_simulate, t, p_type, p_bits, p_signed)
            # True: little-endian, False: big-endian
            p_byteorder = 'little' if p_endian else 'big'
            packet += bytearray(b_data) + bytearray(y.to_bytes(p_byte, byteorder=p_byteorder))
            b_data = b''
        elif p_type == "STRING":
            y_str = create_data("Word", t, p_type, p_bits, p_signed).encode()
            packet += bytearray(b_data) + bytearray(y_str)
            b_data = b''
        elif p_type == "FLOAT" or p_type == "DOUBLE":
            y = create_data(p_simulate, t, p_type, p_bits, p_signed, a=p_a, f=p_f)
            fmt_c = type_map.get((p_type, p_byte, p_signed))
            b_data += struct.pack(f'{en}{fmt_c}', y)
        elif p_type == "INTEGER":
            y = create_data(p_simulate, t, p_type, p_bits, p_signed, a=p_a, f=p_f)
            if p_bits < 8:
                # Offset
                if location % 8 > 0:
                    bit_offset = location % 8
                    b_int = b_int << bit_offset
                    b_bitlen = b_bitlen + bit_offset
                b_int = b_int << p_bits | y
                b_bitlen = b_bitlen + p_bits
                if b_bitlen == 8:
                    fmt_c = type_map.get((p_type, 1, p_signed))
                    b_data += struct.pack(f'{en}{fmt_c}', b_int)
                    b_bitlen = b_int = 0
            else:
                fmt_c = type_map.get((p_type, p_byte, p_signed))
                b_data += struct.pack(f'{en}{fmt_c}', y)
        else:
            print(f"Error: Undefined parameter type: {p_type}")
            sys.exit(1)
    packet += bytearray(b_data)
    return packet


def create_data(mode, t, p_type, p_bit, signed, a=10, f=0.5):
    if p_type == "BINARY":
        max_value = 2 ** p_bit - 1
        return t % (max_value + 1)
    if mode == "Word":
        y_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        p_byte = p_bit // 8
        return (y_str * ((p_byte // len(y_str)) + 1))[:p_byte]
    y = cal_y(mode, t, a, f)
    if p_type == "INTEGER":
        if signed:
            y_max = 2 ** (p_bit-1)
            y_min = (2 ** (p_bit-1) - 1) * (-1)
            if y > y_max:
                y = y % y_max
            elif y < y_min:
                y = y_min
            y = np.int64(y)
        else:
            y_max = 2 ** p_bit
            y_min = 0
            if y > y_max:
                y = y % y_max
            elif y < y_min:
                y = y_min
            y = np.uint64(y)
    return y


def cal_y(mode, t, a, f):
    if mode == "Wave":
        y = a * np.sin(2 * np.pi * f * (t/10) + 0)
    elif mode == "Wave_abs":
        y = abs(a * np.sin(2 * np.pi * f * (t/10) + 0))
    elif mode == "Liner":
        if a*t < sys.float_info.min:
            y = sys.float_info.min
        elif a*t > sys.float_info.max:
            y = sys.float_info.max
        else:
            y = a*t
    elif mode == "Time":
        y = time.time()
    elif mode == "Step":
        y = (t // f) % a
    else:
        print(f"Not defined: {mode}")
        exit(1)
    return np.double(y)


def receive_tc(simulator):
    tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tc_socket.bind((TC_RECEIVE_ADDRESS, TC_RECEIVE_PORT))
    while True:
        data, _ = tc_socket.recvfrom(4096)
        simulator.last_tc = data
        simulator.tc_counter += 1


def parse_restriction_expression(restriction):
    # 'full_key' == "value" or 'full_key' == number
    pattern = r"'([^']+)'\s*==\s*(\"[^\"]*\"|\d+)"
    matches = re.findall(pattern, restriction)
    result = {}
    for full_key, value in matches:
        key = full_key.split('/')[-1]
        if value.startswith('"'):
            result[key] = value.strip('"')
        else:
            result[key] = int(value)
    return result


def collect_restrictions(container, restriction_dict=None):
    if restriction_dict is None:
        restriction_dict = {}
    restriction = container.get("restrictionCriteriaExpression")
    if restriction:
        parsed = parse_restriction_expression(restriction)
        restriction_dict.update(parsed)
    base_container = container.get("baseContainer")
    if base_container:
        collect_restrictions(base_container, restriction_dict)
    return restriction_dict


def get_json_data(url):
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        print(f"Error: {e}")
        sys.exit(1)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


def main():
    url = f"{YAMCS_URL}/api/mdb/{INSTANCE}/containers/{TEST_TM}"
    data = get_json_data(url)
    simulator = Simulator(TM_INTERVAL, data)
    simulator.start()
    sys.stdout.write('Measuring every ' + str(TM_INTERVAL) + 's, ')
    sys.stdout.write('TM host=' + str(TM_SEND_ADDRESS) + ', TM port=' + str(TM_SEND_PORT) + ', ')
    sys.stdout.write('TC host=' + str(TC_RECEIVE_ADDRESS) + ', TC port=' + str(TC_RECEIVE_PORT) + '\r\n')
    try:
        prev_status = None
        while True:
            status = simulator.print_status()
            if status != prev_status:
                # Using '\r' to overwrite the output
                sys.stdout.write('\r')
                sys.stdout.write(status)
                sys.stdout.flush()
                prev_status = status
            sleep(0.5)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
