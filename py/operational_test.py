from time import sleep, time
import yaml
from yamcs.client import VerificationConfig, YamcsClient
import argparse

def issue_command(command_name, argument):
    # Issue a command with args if provided
    if argument:
        command = processor.issue_command(
            command_name,
            args=argument
        )
    else:
        # Issue a command without args
        command = processor.issue_command(
            command_name
        )
    print("Issued", command)


def set_args(argument, checks):
    replace_dict = {}
    for check in checks:
        if check["name"] == "timestamp":
            # If timestamp exists replace it with the current timestamp
            argument["timestamp"] = int(time())
        else:
            # Generate args based on parameter history
            pval = print_current_raw_values(check["name"])
            replace_dict[check["target"]] = pval + check.get("add", 0)
    # Replace matching args values using replace_dict
    replaced_argument = {
        key: replace_dict[value] if isinstance(value, str) and value in replace_dict else value
        for key, value in argument.items()
    }
    return replaced_argument


def print_current_raw_values(param_name):
    # Retrieve and return the current raw_value of the given parameter
    pval = processor.get_parameter_value(
        param_name
    )
    return pval.raw_value


def main(steps, interval):
    # Execute commands in each step, applying checks to args if needed
    for step in steps:
        for command in step["command"]:
            argument = command.get("args", None)
            # If checks exist, adjust args using current parameter values
            if command.get("checks", None):
                argument = set_args(argument, command["checks"])
            # Issue the command
            issue_command(command["name"], argument)
            sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--yaml-file', required=True, help='Command list yaml file')
    parser.add_argument('--yamcs-url',    type=str, default='http://localhost:8090', help='Yamcs URL')
    parser.add_argument('--interval',    type=int, default=1, help='Command sending interval (s)')
    args = vars(parser.parse_args())
    yaml_file = args['yaml_file']
    yamcs_url = args['yamcs_url']
    interval = args['interval']
    # Connect to the Yamcs client and obtain the processor
    client = YamcsClient(yamcs_url)
    processor = client.get_processor("scsat1", "realtime")
    # Load the YAML file and read steps
    with open(yaml_file, 'r') as file:
        operation = yaml.safe_load(file)
    
    main(operation["steps"], interval)

