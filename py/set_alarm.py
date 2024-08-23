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
    parser.add_argument("--data", choices=["srs3", "eps", "main", "adcs"])
    return parser.parse_args()


def get_sys_name():
    args = get_argument()
    if args.data is None:
        print("Please specify options: --data {srs3, eps, main, adcs}")
        sys.exit(1)
    return args.data


def set_critical(processor, sys_name, alarm_data):
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
                name = alarm["name"]
                processor.set_alarm_range_sets(parameter=f"/SCSAT1/{sys_name.upper()}/{name}", sets=ranges)
    except KeyError:
        print("'alamrs' is not defined.")


def main():
    client = YamcsClient('localhost:8090')
    processor = client.get_processor(instance='myproject', processor='realtime')
    sys_name = get_sys_name()
    yaml = YAML()
    yaml_file = Path(DATA_DIR_PATH, f"{sys_name}_alarm.yaml")
    with open(yaml_file, 'r') as file:
        alarm_data = yaml.load(file)
    set_critical(processor, sys_name, alarm_data)


if __name__ == '__main__':
    main()
