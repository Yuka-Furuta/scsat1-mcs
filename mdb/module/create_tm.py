from yamcs.pymdb import *
def set_encoding(param, endian):
    param_type = param.get("type", "int")
    if param_type == "int":
        if param.get("signed", False) == True:
            scheme = IntegerEncodingScheme.TWOS_COMPLEMENT
        else:
            scheme = IntegerEncodingScheme.UNSIGNED
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
            bits = param.get("bit", 80),
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
            base = base,
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
