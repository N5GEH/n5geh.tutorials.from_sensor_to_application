import json
import os

# # load mapping and reverse mapping
# path_mapping = "mapping_v2.json"
# with open(path_mapping, "r") as f:
#     mapping = json.load(f)  # mapping from urn to device id
#     mapping_rev = reverse_mapping(mapping)  # mapping from device id to urn

# def parse2dict(measurements: str) -> list:
#     # TODO the format of the command
#     #  source     {outer_temp_sensor_urn: "value",
#     #              inner_temp_sensor_urn: "value"}
#     #  target {"device_id": {"attribute_name": "value"}}
#     measurements_list = []
#     measurements = json.loads(measurements)
#     for urn in measurements:
#         urn1, urn2 = urn.split("/")  # TODO other connection card can be defined
#         value = measurements[urn]
#         measurement_dict = {
#             mapping[urn1]["device_id"]: {
#                 mapping[urn1]["attribute/command"][urn2]: value
#             }
#         }
#         measurements_list.append(measurement_dict)
#     return measurements_list
#
#
# def parse_from_dict(commands_dict: dict) -> str:
#     # TODO the format of the command
#     #  source {"device_id": {"attribute_name": "value"}}
#     #  target {"URN/URN": value}
#     device_id, attribute_value = list(commands_dict.items())[0]
#     attribute_name, value = list(attribute_value.items())[0]
#
#     urn_1 = mapping_rev[device_id]["urn"]
#     urn_2 = mapping_rev[device_id]["attribute/command"][attribute_name]["urn"]
#     urn = urn_1 + "/" + urn_2  # TODO other connection card can be defined
#     commands = {urn: value}
#     commands = json.dumps(commands)
#     return commands


def reverse_mapping(mapping_dict: dict) -> dict:
    reverse_dict = dict()
    for urn in mapping_dict.keys():
        device_dict = mapping_dict[urn].copy()
        device_dict_rev = device_dict
        device_id = device_dict["device_id"]

        attr_comm = device_dict["attribute/command"]
        attr_comm_rev = {
            attr_comm[urn_attr]: {"urn": urn_attr} for urn_attr in attr_comm.keys()
        }

        device_dict_rev["attribute/command"] = attr_comm_rev
        device_dict_rev["urn"] = urn

        reverse_dict[device_id] = device_dict_rev
    return reverse_dict

# def reverse_mapping_file(path_mapping, path_mapping_rev):
#     with open(path_mapping, "r") as f:
#         mapping = json.load(f)
#     mapping_rev = reverse_mapping(mapping)
#     with open(path_mapping_rev, "w") as f:
#         json.dump(mapping_rev, f, indent=2)
if __name__ == '__main__':
    path_mapping = "mapping_v2.json"
    with open(path_mapping, "r") as f:
        mapping = json.load(f)
    mapping_rev = reverse_mapping(mapping)
    path_mapping_rev = "mapping_v2_rev.json"
    with open(path_mapping_rev, "w") as f:
        json.dump(mapping_rev, f, indent=2)
