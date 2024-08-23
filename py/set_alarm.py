import sys
import argparse
from pathlib import Path
from ruamel.yaml import YAML
from yamcs.client import YamcsClient
from yamcs.tmtc.model import RangeSet

DIR_PATH = Path(__file__).resolve().parent
DATA_DIR_PATH = Path(DIR_PATH, "alarm")


def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="--data <YAML_FILE>", metavar="YAML_FILE")
    return parser.parse_args()


def get_file_name():
    args = get_argument()
    if args.data is None:
        print("Please specify options: --data <YAML_FILE>")
        sys.exit(1)
    return args.data


def set_critical(processor, alarm_data):
    try:
        for alarm in alarm_data["alarms"]:
            alm = alarm.get("critical", None)
            if alm is not None:
                ranges = [
                    RangeSet(
                        context=None,
                        critical=(alm["low"], alm["high"])
                    )
                ]
                processor.set_alarm_range_sets(parameter=alarm_data["prefix"]+alarm["name"], sets=ranges)
    except KeyError:
        print("'alarms' is not defined.")


def main():
    client = YamcsClient('localhost:8090')
    processor = client.get_processor(instance='myproject', processor='realtime')
    yaml = YAML()
    yaml_file = Path(DATA_DIR_PATH, get_file_name())
    try:
        with open(yaml_file, 'r') as file:
            alarm_data = yaml.load(file)
        set_critical(processor, alarm_data)
    except OSError as e:
        print(e)


if __name__ == '__main__':
    main()
