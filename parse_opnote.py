import yaml
import re
from datetime import datetime
from db_funcs import insert_patient, insert_op
import ast


def _wrap_time_stamp(content):
    result = re.sub(
        r"(?i)(start time|end time):\s*([0-9]{1,2}:[0-9]{2})", r'\1: "\2"', content
    )
    return result


def _wrap_id_stamp(content):
    result = re.sub(r"(?i)(id):\s*([0-9]{8})", r'\1: "\2"', content)
    return result


def conv_paragraph_head(content):
    result = re.sub(r"^##\s+(.*)", r"\\paragraph{\1}", content, flags=re.MULTILINE)
    return result


def parse_opnote(filename):
    yaml_lines = []
    indication_lines = []
    opnote_lines = []
    in_yaml = False
    in_indication = False
    in_opnote = False
    with open(filename) as f:
        for line in f:
            if line.strip() == "---":
                in_yaml = not in_yaml
                continue
            if line.strip() == "# Indication":
                in_indication = not in_indication
                continue
            if line.strip() == "# Procedure":
                in_indication = not in_indication
                in_opnote = not in_opnote
                continue
            if in_yaml:
                yaml_lines.append(line)
            elif in_indication:
                indication_lines.append(line)
            elif in_opnote:
                opnote_lines.append(line)

    yaml_content = _wrap_time_stamp("".join(yaml_lines))
    yaml_content = _wrap_id_stamp(yaml_content)
    data = yaml.safe_load(yaml_content)
    indication = "".join(indication_lines)
    opnote = "".join(opnote_lines)
    data["indication"] = conv_paragraph_head(indication)
    data["opnote"] = conv_paragraph_head(opnote)

    # Change some keys
    data["patient_id"] = data["id"]
    data.pop("id", None)
    data["kanji_name"] = data["name"]
    data.pop("name", None)
    data["op_date"] = data["opdate"]
    data.pop("opdate", None)
    data["op_note"] = data["opnote"]
    data.pop("opnote", None)
    data["start_time"] = data["start time"]
    data.pop("start time", None)
    data["end_time"] = data["end time"]
    data.pop("end time", None)
    data["phones"] = [data["phone"]]
    return data


if __name__ == "__main__":
    filename = input("File name: ")
    result = parse_opnote(filename)
    result["kana_name"] = ""
    result["sex"] = ""
    result["preop_dx"] = ""
    result["postop_dx"] = ""
    result["procedure"] = ""
    result["surgeon_list"] = []
    result["assistant_list"] = []

    def display_dict(mydict):
        for key, value in mydict.items():
            print(key)
            print(value)

    display_dict(result)
    while True:
        resp = input("Hit any key to continue, q to quit")
        if resp.strip() == "q":
            break
        change_key = input("Which key? ")
        change_value = input("Value? ")
        if change_key in ["start_time", "end_time"]:
            change_value = datetime.strptime(change_key, "%H:%M").time()
        if change_key == "op_date":
            change_value = datetime.strptime(change_key, "%Y-%m-%d").date()
        if change_key in ["surgeon_list", "assistant_list"]:
            change_value = ast.literal_eval(change_value)

        result[change_key] = change_value

        display_dict(result)
    insert_patient(result)
    insert_op(result)
