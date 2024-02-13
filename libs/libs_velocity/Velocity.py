#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Alin Andronache
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used to enable communication with Velocity Service """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from parameters.global_parameters import Reporting as REPORTINGPARAMS
import helpers.Logger as Local_logger
import json
import sys
import os
from helpers.RequestsWrapper import APISession

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], f"velocity_session_log.txt")


class API:
    def __init__(self, velocity_ip, username, password, repeat_step=1):
        log_worker.debug(f"Velocity.py - Initiating Velocity class instance for {velocity_ip}.")
        self.this_class_name = self.__class__.__name__
        self.base_url = "https://" + velocity_ip + "/velocity/api/"
        self.base_url_ito = "https://" + velocity_ip + "/ito/"
        # self.api_session = requests.Session()
        self.api_session = APISession()
        log_worker.debug(f"Velocity.py - Opened Velocity class instance for {velocity_ip}.")
        self.api_session.verify = False
        self.create_token(username, password)
        self.api_session.headers = {'Content-Type': "application/json", "X-Auth-Token": f"{self.api_token}"}
        self.repeat_step = repeat_step

    def create_token(self, username, password):
        """'
        Method used to get an authentication token for a certain user.
        :param username: (name of the user for which the token is being generated)
        :param password: (password of the user)
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to get the token from environment variables.")
        try:
            self.api_token = os.environ['VELOCITY_PARAM_VELOCITY_TOKEN']
        except KeyError as e:
            log_worker.debug(
                f"{self.this_class_name} - {this_method_name} - Environment variables do not contain an execution token.")
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating token for {self.base_url}.")
            url = self.base_url + "auth/v2/token"
            self.api_session.auth = (username, password)
            response = self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                                     log_worker=log_worker,
                                                     request_description="Getting a new Velocity token.")
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Response: {response}.")
            self.api_token = response["token"]
        except Exception as e:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - Failed to get an execution token, error: {e}")
            return False
        return True

    def get_resources(self, filters=None):
        """'
        Method used to get a complete list of all resources based on the given filter.
        :param filters: (list of filters which will be added to the url, example: ["folderId::123","hostId:!:456"])
        :return: Json with all resources and properties if successful, False if requests failed.
        """
        if filters is None:
            filters = []

        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Getting all resources from {self.base_url}.")
        url = self.base_url + "inventory/v16/devices?includeProperties=true&limit=200&"

        if filters:
            for flt in filters:
                url = f"{url}filter={flt}&"

        total = 1
        offset = 0
        all_resources = {"devices": []}

        while offset < total:
            url_offset = f"{url}offset={offset}"
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Getting all resources using {url_offset}.")
            response = self.api_session.send_request(request_type="get", url=url_offset, method_name=this_method_name,
                                                     log_worker=log_worker,
                                                     request_description=f"Getting all resources using url {url}.")
            if response:
                all_resources["devices"].extend(response["devices"])
            else:
                return False
            total = int(response["total"])
            count = int(response["count"])
            offset = offset + count

        return all_resources

    def get_resource_property_value(self, resource_name, property_name_list):
        """
        Method used to get a dictionary of properties together with their values for a certain resource
        :param resource_name: name of the resource
        :param property_name_list: list with the properties for which to get values
        :return: False or dictionary with property name and value pairs
        """
        this_method_name = sys._getframe().f_code.co_name
        property_values_dict = dict()
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Get resource properties values for {resource_name}")

        filter_list = ["name::" + resource_name]
        resource = self.get_resources(filter_list)
        if not resource:
            return False

        resource = resource['devices']
        for resource_property in resource[0]['properties']:
            property_name = resource_property['name']
            if property_name in property_name_list:
                property_values_dict[property_name] = resource_property['value']

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Obtained property values: {property_values_dict}")
        return property_values_dict

    def get_reservation(self, reservation_id="current"):
        """
        Method used to get reservation details
        :param reservation_id: if current then it takes it from os.environ; else, user could provide it as param
        :return: False or reservation information in JSON format
        """

        this_method_name = sys._getframe().f_code.co_name

        if reservation_id == "current":
            reservation_id = os.environ['VELOCITY_PARAM_RESERVATION_ID']
        url = self.base_url + 'reservation/v18/reservation/' + reservation_id
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Get reservation using {url}.")
        response = self.api_session.send_request(request_type="get", url=url, log_worker=log_worker,
                                                 method_name=this_method_name)
        return response

    def get_user_profile(self, user_id):
        """
        Method used to get user profile information
        :param user_id: id of the user
        :return: False or user information in JSON format
        """

        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + 'user/v9/profile/' + user_id
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Get user profile using {url}.")
        response = self.api_session.send_request(request_type="get", url=url, log_worker=log_worker,
                                                 method_name=this_method_name)

        return response

    def get_templates(self, filters=None):
        """'
        Method used to get a list of the first 200 templates based on the given filter.
        :param filters: (list of filters which will be added to the url, example: ["parentId::123","name:!:456"])
        :return: Json with all templates and properties if successful, False if requests failed.
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting all templates from {self.base_url}.")
        url = self.base_url + "inventory/v16/templates?limit=-1"
        if filters:
            for flt in filters:
                url = f"{url}&filter={flt}"

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting all templates using {url}.")
        response = self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                                 log_worker=log_worker,
                                                 request_description="template list")

        return response

    def get_template_id(self, template_id):
        """'
        Method used to get information from a template given by its ID.
        :param template_id: ID of the template
        :return: Json with the template information
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + f"inventory/v16/template/{template_id}"

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting template info using {url}.")
        response = self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                                 log_worker=log_worker,
                                                 request_description="template info")

        return response

    def create_device(self, name, template_id, folder_id="null"):
        """'
        Method used to create a device with a given name and template.
        :param name: Name of the new resource
        :param template_id: ID of the inherited template
        :param folder_id: ID of the folder in which the new resource will be created
        :return: ID of the new device, False if requests failed.
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating device on {self.base_url} using "
                         f"template {template_id}.")
        url = self.base_url + "inventory/v16/device"

        json_data = {"name": name,
                     "templateId": template_id,
                     "folderId": folder_id}

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Using JSON body: {json_data}.")
        response = self.api_session.send_request(request_type="post", url=url, method_name=this_method_name,
                                                 log_worker=log_worker, json_data=json_data,
                                                 request_description=f"{name} resource creation")
        if response:
            response = response["id"]

        return response

    def update_device_property(self, device_id, definition_id, property_value):
        """
        Method used to update a device property based on a definition id
        :param device_id: id of the device
        :param definition_id: definition id of the property to be updated
        :return: False or response in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Updating device on {self.base_url} for id {device_id}.")
        url = self.base_url + "inventory/v15/device/" + device_id
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - URL used: {url}")

        dict_to_load = {
            "properties": [
                {
                    "definitionId": definition_id,
                    "value": property_value,
                }
            ]
        }

        json_data = dict_to_load
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Using JSON body: {json_data}.")

        response = self.api_session.send_request(request_type="put", json_data=json_data, url=url,
                                                 log_worker=log_worker, method_name=this_method_name)

        return response

    def nest_resources(self, parent_id, nest_list):
        """
        Method used to nest multiple resources under another one
        :param parent_id: id of the parent device
        :param nest_list: list of devices which will be nested under parent_id
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + f"inventory/v15/device/{parent_id}/nested_resources"
        json_data = {"ids": []}
        for nest in nest_list:
            json_data["ids"].append(nest)

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Nesting resources: {json_data} under {parent_id}")

        return self.api_session.send_request(request_type="post", json_data=json_data, url=url, log_worker=log_worker,
                                             method_name=this_method_name, request_description="resources nesting")

    def nested_resources_delete(self, parent_id, nest_list):
        """
        Method used to remove nested resources from under a parent
        :param parent_id: id of the parent device
        :param nest_list: list of devices which will be removed from under the parent device
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + f"inventory/v15/devices/{parent_id}/nested_resources_delete"
        json_data = {"ids": []}
        for nest in nest_list:
            json_data["ids"].append(nest)

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Un-nesting resources: {json_data} from under {parent_id}")

        return self.api_session.send_request(request_type="put", json_data=json_data, url=url, log_worker=log_worker,
                                             method_name=this_method_name, request_description="resources un-nesting")

    def nest_template(self, parent_template_id, child_template_id):
        """
        Method used to nest a template under another one
        :param parent_template_id: id of the parent template
        :param child_template_id: template which will be nested under the parent template
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + f"inventory/v15/template/{parent_template_id}/nested_template"
        json_data = {"templateId": child_template_id}
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Nesting template: {child_template_id} under {parent_template_id}")

        return self.api_session.send_request(request_type="post", json_data=json_data, url=url, log_worker=log_worker,
                                             method_name=this_method_name, request_description="template nesting")

    def nest_templates(self, parent_template_id, nest_template_list):
        """
        Method used to nest multiple templates under another one
        :param parent_template_id: id of the parent template
        :param nest_template_list: list of templates which will be nested under the parent template
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        already_nested_templates = self.get_nested_templates(parent_template_id)
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Already nested templates under {parent_template_id}: {already_nested_templates}")

        already_nested_ids = []
        if int(already_nested_templates["total"]) > 0:
            for i in range(0, int(already_nested_templates["total"])):
                already_nested_ids.append(already_nested_templates["items"][i]["templateId"])

        temp_nest_template_list = [i for i in nest_template_list if i not in already_nested_ids]
        nest_template_list = temp_nest_template_list

        if len(nest_template_list) == 0:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - All templates are already nested.")
            return True

        failed_nests = []
        for nest in nest_template_list:
            if not self.nest_template(parent_template_id, nest):
                failed_nests.append(nest)

        if len(failed_nests) == 0:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - All templates were successfully nested.")
            return True
        else:
            log_worker.debug(
                f"{self.this_class_name} - {this_method_name} - Failed to nest some of the templates: {failed_nests}")
            return False

    def get_nested_templates(self, parent_template_id):
        """
        Method used t oget a list of the IDs of the templates nusted under parent_template_id
        :param parent_template_id: id of the parent template
        :return: list of IDs or False if the request fails
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url + f"inventory/v15/template/{parent_template_id}/nested_templates?limit=200"

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting nested templates under {parent_template_id}")

        return self.api_session.send_request(request_type="get", url=url, log_worker=log_worker,
                                             method_name=this_method_name,
                                             request_description=f"list of nested templates under {parent_template_id}")

    def create_rack_structure(self, inventory_json, lab_row_template_name, rack_template_name):
        """
        Method used to create the rack structures for the airtel environment
        :param inventory_json: json with the set of resources returned by Velocity
        :param lab_row_template_name: name of the template representing the Lab Row resources
        :param rack_template_name: name of the template representing the Rack resources
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        flt = [f"name::{lab_row_template_name}"]
        row_template = self.get_templates(flt)["templates"][0]["id"]
        flt = [f"name::{rack_template_name}"]
        rack_template = self.get_templates(flt)["templates"][0]["id"]
        folder_id = "7f384f93-036a-4cbf-b368-8a4643349ab1"

        template_ids = []
        rack_structure = {}

        ignore_list = [None, "To be filled(A-I)", "To be filled(1-16)", "", "None", "N/A"]
        total_number = len(inventory_json['devices'])
        for i in range(0, total_number):
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Processing resource {i}/{total_number} "
                             f"with ID: {inventory_json['devices'][i]['id']}.")
            try:
                lab_row = rack_number = ''
                for j in range(0, len(inventory_json["devices"][i]["properties"])):
                    if inventory_json["devices"][i]["properties"][j]["name"] == "Lab Row" and \
                            inventory_json["devices"][i]["properties"][j]["value"] not in ignore_list:
                        lab_row = inventory_json["devices"][i]["properties"][j]["value"]
                    if inventory_json["devices"][i]["properties"][j]["name"] == "Rack Number" and \
                            inventory_json["devices"][i]["properties"][j]["value"] not in ignore_list:
                        rack_number = inventory_json["devices"][i]["properties"][j]["value"]

                if lab_row and rack_number:
                    log_worker.debug(
                        f"{self.this_class_name} - {this_method_name} - Found combination: lab_row: {lab_row} and rack_number: {rack_number}.")
                    lab_row = lab_row.upper()
                    if lab_row not in rack_structure.keys():
                        lab_row_id = ''

                        for device_iter in inventory_json["devices"]:
                            if device_iter["name"] == f"Row_{lab_row}":
                                lab_row_id = device_iter["id"]
                                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Row_{lab_row} already exists with ID {lab_row_id}")
                                break

                        if lab_row_id == '':
                            lab_row_id = self.create_device(f"Row_{lab_row}", row_template, folder_id)

                        if lab_row_id != '':
                            rack_structure[lab_row] = {}
                            rack_structure[lab_row]["id"] = lab_row_id
                    else:
                        log_worker.debug(
                            f"{self.this_class_name} - {this_method_name} - {lab_row} resource already exists.")
                    rack_name = f"Row_{lab_row}_{rack_number}"
                    if rack_name not in rack_structure[lab_row].keys():
                        log_worker.debug(
                            f"{self.this_class_name} - {this_method_name} - {rack_name} was not created on this run, checking the inventory to see if it already exists.")
                        rack_id = ''

                        for device_iter in inventory_json["devices"]:
                            if device_iter["name"] == rack_name:
                                rack_id = device_iter["id"]
                                log_worker.debug(f"{self.this_class_name} - {this_method_name} - {rack_name} already exists with ID {rack_id}")
                                break

                        if rack_id == '':
                            log_worker.debug(
                                f"{self.this_class_name} - {this_method_name} - {rack_name} will be created.")
                            rack_id = self.create_device(rack_name, rack_template, folder_id)

                        if rack_id != '':
                            rack_structure[lab_row][rack_name] = {}
                            rack_structure[lab_row][rack_name]["id"] = rack_id
                            rack_structure[lab_row][rack_name]["children"] = []
                    else:
                        log_worker.debug(
                            f"{self.this_class_name} - {this_method_name} - {rack_name} resource already exists.")
                    device_id = inventory_json["devices"][i]["id"]
                    rack_structure[lab_row][rack_name]["children"].append(device_id)
                    template_id = inventory_json["devices"][i]["templateId"]
                    if template_id not in template_ids:
                        template_ids.append(template_id)

                else:
                    device_id = inventory_json["devices"][i]["id"]
                    host_device_id = inventory_json["devices"][i]["hostId"]
                    if host_device_id is not None:
                        host_template_id = ''
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Lab row ({lab_row}) or rack "
                                         f"number ({rack_number}) properties are missing. Resource will be un-nested "
                                         f"if it's nested under a rack used by the automation script ("
                                         f"{rack_template}).")
                        for k in range(0, str(inventory_json).count("'id'")):
                            if inventory_json["devices"][k]["id"] == host_device_id:
                                host_template_id = inventory_json["devices"][k]["templateId"]
                                break
                        if host_template_id != '' and host_template_id == rack_template:
                            log_worker.debug(
                                f"{self.this_class_name} - {this_method_name} - Resource {device_id} will be un-nested from {host_device_id}.")
                            self.nested_resources_delete(host_device_id, [device_id])
                        else:
                            log_worker.debug(
                                f"{self.this_class_name} - {this_method_name} - Resource {device_id} does not have to be un-nested.")

            except Exception as e:
                if str(e) == "list index out of range":
                    pass
                else:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log_worker.debug(f"{self.this_class_name} - {this_method_name} - Unknown unhandled error:{e}")
                    log_worker.debug(
                        f"{self.this_class_name} - {this_method_name} - Error details: {exc_type, fname, exc_tb.tb_lineno}")

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Rack structure JSON: {rack_structure}")
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Nesting all required templates if needed using: {template_ids}")
        self.nest_templates(rack_template, template_ids)

        total_children = 0
        for lab_row in rack_structure.keys():
            lab_row_id = rack_structure[lab_row]["id"]
            lab_row_racks = []
            for labRowRack in rack_structure[lab_row].keys():
                if labRowRack != "id":
                    rack_id = rack_structure[lab_row][labRowRack]["id"]
                    lab_row_racks.append(rack_id)
                    device_list = rack_structure[lab_row][labRowRack]["children"]
                    total_children = total_children + len(device_list)
                    self.nest_resources(rack_id, device_list)
            self.nest_resources(lab_row_id, lab_row_racks)

        log_worker.info(f"{self.this_class_name} - {this_method_name} - Finished: PASSED")

        return True

    def get_airtel_racks(self, rack_template_name):
        """
        Method used to get the list of racks created previously by this script, using the same rack template name
        :param rack_template_name: name of the template representing the Rack resources
        :return: response_racks (
        Velocity json structure containing rack resources), response_devices (Velocity json structure containing the
        nested devices under the racks)
        """
        this_method_name = sys._getframe().f_code.co_name

        filter_list = [f"name::{rack_template_name}"]
        rack_template_id = self.get_templates(filter_list)["templates"][0]["id"]
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting rack instances having template Id {rack_template_id}")
        response_racks = self.get_resources([f"templateId::{rack_template_id}"])
        total_number = str(response_racks).count("'id'")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Found {total_number} resources.")

        i = 1
        filters_list = []
        filter_set = ''
        while i <= total_number:
            filter_set = filter_set + "hostId::" + response_racks['devices'][i - 1]['id'] + '|'
            if i % 50 == 0:
                filters_list.append(filter_set[:-1])
                filter_set = ''
            i += 1
        filters_list.append(filter_set[:-1])

        response_devices = {'devices': []}

        for filter_set in filters_list:
            nest_response = self.get_resources([filter_set])
            response_devices = json.dumps(response_devices)
            nest_response = json.dumps(nest_response)
            first_part = str(response_devices)[:-2]
            second_part = str(nest_response)[13:-2]
            if filter_set == filters_list[0]:
                response_devices = first_part + second_part + ']}'
            else:
                response_devices = first_part + ',' + second_part + ']}'
            response_devices = json.loads(response_devices)

        total_number_racks = str(response_racks).count("'id'")
        total_number_devices = str(response_devices).count("'id'")
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Response has {total_number_racks} racks and {total_number_devices} devices.")

        return response_racks, response_devices

    def get_airtel_racks_v2(self, templateId):

        log_worker.debug(f"get_airtel_racks - Getting rack instances having template Id {templateId}")
        responseRacks = self.get_resources([f"templateId::{templateId}"])
        totalNumber = str(responseRacks).count("'id'")
        log_worker.debug(f"get_airtel_racks - Found {totalNumber} resources.")

        totalNumberRacks = str(responseRacks).count("'id'")
        log_worker.debug(f"get_airtel_racks - Response has {totalNumberRacks} racks")

        return responseRacks

    def get_automation_assets(self, filters=None):
        """
        Method used to get the list of automation assets based on the given filter
        :param filters: dictionary set of filters names, together with their values
        :return: json list of the obtained automation assets
        """
        if filters is None:
            filters = {}
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Getting list of automation assets.")
        url = self.base_url_ito + f"repository/v2/testcases?limit=200&filter=driver::false&" \
                                  f"filter=includeInListingQuickCalls::false"
        if filters:
            url = f"{url}&"
            for flt in filters.keys():
                if flt == "tags":
                    for tag in filters[flt]:
                        url = f"{url}filter=tags::{tag}|"
                    url = url[:-1]
                elif flt == "fullPath":
                    url = f"{url}filter={flt}::{filters[flt]}"

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting testcases with the following url {url}")

        count = 0
        total = 1
        offset = 0
        automation_assets = {"content": []}

        while offset < total:
            url_offset = f"{url}&offset={str(offset)}"
            response = self.api_session.send_request(request_type="get", url=url, log_worker=log_worker,
                                                     method_name=this_method_name,
                                                     request_description=f"list of automation assets")
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Successful request.")
            automation_assets["content"].extend(response["content"])
            total = int(response["total"])
            count = int(response["count"])

            offset = offset + count

            if "errorId" in str(response):
                log_worker.eror(f"{self.this_class_name} - {this_method_name} - Response: {response}")
            else:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - List of automation assets was "
                                 f"successfully queried, total items: {len(automation_assets['content'])}")

        return automation_assets

    def extract_testcase_paths(self, get_testcases_response):
        """
        Method used to get a list of testcase paths from a set of JSON data containing automation asset info
        :param get_testcases_response: JSON body returned from the get_automation_assets request
        :return: list of testcase paths
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting list of testcase paths from the JSON structure.")

        paths = []
        for i in range(0, len(get_testcases_response["content"])):
            paths.append(get_testcases_response["content"][i]["fullPath"])

        return paths

    def post_runlist_execution(self, testcase_paths, detail_level, terminate_on_item_fail, execution_name, topology_id):
        """
        Method used to start a runlist execution in Velocity
        :param testcase_paths: list of testcase paths for each of the testcases included in the runlist
        :param detail_level: detail level of the generated execution report (recommended "ALL_ISSUES_ALL_STEPS")
        :param terminate_on_item_fail: set to True to stop the runlist immediately when at least one execution fails
        :param execution_name: name of the runlist execution
        :param topology_id: ID of the topology used throughout the runlist execution
        :return: ID of the runlist execution
        """
        this_method_name = sys._getframe().f_code.co_name

        url = self.base_url_ito + "executions/v1/runlists/"
        if execution_name:
            url = f"{url}main%2F_runlists%2F{execution_name}"
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Creating runlist execution named {execution_name}.")

        post_body = {"general": {"detailLevel": detail_level}, "main": {"items": [], "terminateOnItemFail": "false"}}
        if topology_id:
            post_body["general"]["topologyId"] = topology_id

        if terminate_on_item_fail is True:
            post_body["main"]["terminateOnItemFail"] = "true"

        for path in testcase_paths:
            post_body["main"]["items"].append({"path": path})

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Starting runlist execution sing the following JSON body: {post_body}")
        response = self.api_session.send_request(request_type="post", url=url, log_worker=log_worker,
                                                 json_data=post_body,
                                                 method_name=this_method_name,
                                                 request_description=f"runlist execution creation")

        execution_id = response["guid"]
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Runlist execution was created successfully, id: {execution_id}")

        return execution_id

    def get_runlist_execution(self, execution_id):
        """
        Method used to get the status of a runlist execution
        :param execution_id: runlist execution id
        :return: response of the request
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting information for execution with id {execution_id}.")

        url = f"{self.base_url_ito}executions/v1/runlists/summary"
        body = [execution_id]
        response = self.api_session.send_request(request_type="post", json_data=body, url=url,
                                                 request_description="runlist execution status", log_worker=log_worker,
                                                 method_name=this_method_name)

        return response

    def get_execution_id(self, execution_id):
        """
        Method used to get the status of a testcase execution
        :param execution_id: testcase execution id
        :return: response of the request
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting execution information for execution with ID {execution_id}.")
        url = f"{self.base_url_ito}executions/v1/executions/{execution_id}"
        response = self.api_session.send_request(request_type="get", url=url, request_description="execution status",
                                                 log_worker=log_worker, method_name=this_method_name)

        return response

    def get_execution_failure_reason(self, execution_id):
        """
        Method used to get the reason of an execution's failure
        :param execution_id: testcase execution id
        :return: message with the failure reason, None if no message is found
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting execution failure reason for execution with ID {execution_id}.")

        url = f"{self.base_url_ito}reporting/v1/issues?limit=200&offset=0&sortBy=issueIndex&filter=reportId::" \
              f"{execution_id}&filter=severity::ERROR"
        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description="execution failure reason", log_worker=log_worker,
                                                 method_name=this_method_name)

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Execution information was queried successfully.")

        if response["total"] != 0:
            failure_reason = response["content"][0]["message"]
            log_worker.debug(
                f"{self.this_class_name} - {this_method_name} - Execution failure reason: {failure_reason}.")
        else:
            failure_reason = None

        return failure_reason

    def get_runlist(self, runlist_name):
        """
        Method used to get the information of a runlist identified by runlist_name
        :param runlist_name: name of the runlist
        :return: JSON body with the information of the runlist
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting runlist information using name {runlist_name}.")

        url = f"{self.base_url_ito}repository/v2/repository/main/_runlists/{runlist_name}.vrl"
        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"{runlist_name} runlist information",
                                                 log_worker=log_worker, method_name=this_method_name)

        return response

    def get_topology_id_by_name(self, topology_name):
        """
        Method used to get the topology ID by searching for it using its name
        :param topology_name: name of the topology
        :return: ID of the topology, False if no topologies are found
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting topology ID using name {topology_name}.")

        url = f"{self.base_url}topology/v16/topologies?filter=name::{topology_name}"

        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"{topology_name} topology ID",
                                                 log_worker=log_worker, method_name=this_method_name)

        if response["total"] == 0:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - No topologies named {topology_name} were found.")
            return False

        topology_id = response["topologies"][0]["id"]
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - ID of topology {topology_name} is {topology_id}.")

        return topology_id

    def convert_template_json(self, template_json, driver_id=None, parent_id=None):
        """
        Method used to get the template properties  and convert them to POST comaptible format
        :param template_json: template json response
        :return: JSON with the extracted properties
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting template info from  {template_json}.")

        post_json = dict(template_json)
        ignored_properties = ['id', 'isRemoved', 'iconId', 'isReadOnly', 'lastAction', 'lastModified', 'lastModifierId',
                              'created', 'creatorId', 'propertyGroups', 'portGroups', 'agentRequirements',
                              'firmwareAssetId', 'firmwareURI', 'inheritFirmware', 'configAssetId', 'configURI',
                              'inheritConfig', 'parentId', 'driverId', 'isUpdating']
        for ignore in ignored_properties:
            post_json.pop(ignore, None)

        properties = {"propertyGroups": []}
        for property_group in range(0, len(template_json["propertyGroups"])):
            properties["propertyGroups"].append({"name": template_json["propertyGroups"][property_group]["name"],
                                                 "isHidden": str(template_json["propertyGroups"][property_group][
                                                                     "isHidden"]).lower(),
                                                 "properties": []})
            for prop in range(0, len(template_json["propertyGroups"][property_group]["properties"])):
                default_value = template_json["propertyGroups"][property_group]["properties"][prop]["defaultValue"]
                if default_value == "None":
                    default_value = "null"
                type = template_json["propertyGroups"][property_group]["properties"][prop]["type"]
                if type == "DROP_DOWN_LIST":
                    properties["propertyGroups"][property_group]["properties"].append(
                        {"name": template_json["propertyGroups"][property_group]["properties"][prop]["name"],
                         "description": template_json["propertyGroups"][property_group]["properties"][prop][
                             "description"],
                         "defaultValue": default_value,
                         "isRequired": str(template_json["propertyGroups"][property_group]
                                           ["properties"][prop]["isRequired"]).lower(),
                         "type": template_json["propertyGroups"][property_group]["properties"][prop]["type"]})
                else:
                    properties["propertyGroups"][property_group]["properties"].append(
                        {"name": template_json["propertyGroups"][property_group]["properties"][prop]["name"],
                         "description": template_json["propertyGroups"][property_group]["properties"][prop]["description"],
                         "defaultValue": default_value, "isRequired": str(template_json["propertyGroups"][property_group]
                                                                          ["properties"][prop]["isRequired"]).lower(),
                         "type": template_json["propertyGroups"][property_group]["properties"][prop]["type"]})

        post_json.update(properties)

        if parent_id:
            post_json["parentId"] = parent_id

        if driver_id:
            post_json["driverId"] = driver_id

        return post_json

    def get_drivers(self):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting drivers.")

        url = f"{self.base_url}inventory/v16/drivers?limit=-1"

        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"drivers",
                                                 log_worker=log_worker, method_name=this_method_name)
        return response

    def create_template(self, post_json):

        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating template on {self.base_url}.")
        url = self.base_url + "inventory/v16/template"

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Using JSON body: {post_json}.")
        response = self.api_session.send_request(request_type="post", url=url, method_name=this_method_name,
                                                 log_worker=log_worker, json_data=post_json,
                                                 request_description=f"template creation")

        return response

    def get_profiles(self):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting users.")

        url = f"{self.base_url}user/v9/profiles?limit=200"

        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"users",
                                                 log_worker=log_worker, method_name=this_method_name)
        return response

    def put_profile_id(self, profile_id, data):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Modifying user {profile_id}")

        url = f"{self.base_url}user/v9/profile/{profile_id}"

        response = self.api_session.send_request(request_type="put", url=url,
                                                 request_description=f"modifying user",
                                                 log_worker=log_worker, method_name=this_method_name, json_data=data)
        return response

    def get_user_groups(self, include_users=False):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting user groups")

        url = f"{self.base_url}user/v9/groups"
        if include_users:
            url = url + "?includeUsers=true"

        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"getting user groups",
                                                 log_worker=log_worker, method_name=this_method_name)

        return response

    def post_user_groups(self, data):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Creating user group")

        url = f"{self.base_url}user/v9/group"

        response = self.api_session.send_request(request_type="post", url=url,
                                                 request_description=f"creating user group",
                                                 log_worker=log_worker, method_name=this_method_name, json_data=data)

        return response

    def get_device_groups(self):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting device groups")

        url = f"{self.base_url}inventory/v16/device_groups?limit=200"

        response = self.api_session.send_request(request_type="get", url=url,
                                                 request_description=f"getting device groups",
                                                 log_worker=log_worker, method_name=this_method_name)

        return response

    def get_device_group_id_devices(self, id):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Getting device group {id} devices")

        url = f"{self.base_url}inventory/v16/device_group/{id}/devices?limit=200&"

        total = 1
        offset = 0
        all_resources = {"devices": []}

        while offset < total:
            url_offset = f"{url}offset={offset}"
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Getting all resources using {url_offset}.")
            response = self.api_session.send_request(request_type="get", url=url_offset, method_name=this_method_name,
                                                     log_worker=log_worker,
                                                     request_description=f"Getting all resources using url {url}.")
            if response:
                all_resources["devices"].extend(response["devices"])
            else:
                return False
            total = int(response["total"])
            count = int(response["count"])
            offset = offset + count

        return all_resources

    def post_device_group(self, data):
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Creating device group")

        url = f"{self.base_url}inventory/v16/device_group"

        response = self.api_session.send_request(request_type="post", url=url,
                                                 request_description=f"creating device group",
                                                 log_worker=log_worker, method_name=this_method_name, json_data=data)

        return response