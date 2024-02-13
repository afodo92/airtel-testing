#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Alin Andronache
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used to enable communication with Netbox Service """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import sys
import requests
from collections import defaultdict
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from parameters.global_parameters import Reporting as REPORTINGPARAMS
import helpers.Logger as Local_logger
import json
import urllib3
from helpers.RequestsWrapper import APISession

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], "netbox_core_log.txt")


class API:
    def __init__(self, netbox_ip, api_token):
        self.base_url = "https://" + netbox_ip + "/"
        self.api_token = api_token
        self.this_class_name = self.__class__.__name__
        self.api_session = APISession()
        self.api_session.headers = {'accept': 'application/json',
                                    "Authorization": f"Token {api_token}",
                                    "content-type": "application/json"}
        self.api_session.verify = False

    def create_token(self, username, password):

        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get a NetBox token.")

        url = self.base_url + "api/users/tokens/provision/"
        response = self.api_session.send_request(request_type="post",
                                                 json_data={"username": username, "password": password},
                                                 url=url, log_worker=log_worker, method_name=this_method_name,
                                                 request_description="Netbox token creation")
        if not response:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Failed get a NetBox token.")
            self.api_token = False
        else:
            self.api_token = response["key"]

    def get_ipam_ip_addresses(self):
        """
        Method used to GET ALL IPAM IP Address information.
        :returns: Dict {'id_1':{"ip_family", "ip_address", "ip_netmask","ip_status"}, 'id2':...} or False
        """
        this_method_name = sys._getframe().f_code.co_name

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get all IPAM Addresses.")
        return_data = {}
        url = self.base_url + "api/ipam/ip-addresses/"
        if self.api_token:
            response = self.api_session.send_request(request_type="get",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="list of IPAM addresses")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            # if response.status_code == 200:
            for element in response["results"]:
                element_data = defaultdict(None, element)
                ip_address = element_data.get("address").split("/")[0]
                ip_netmask = element_data.get("address").split("/")[1]
                ip_family = element_data.get("family").get("value")
                ip_status = element_data.get("status").get("value")
                ip_id = element_data.get("id")

                return_data[ip_id] = {"ip_family": ip_family, "ip_address": ip_address, "ip_netmask": ip_netmask,
                                      "ip_status": ip_status}
            return defaultdict(None, return_data)
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def create_ipam_ip_address(self, ip_address, ip_netmask, ip_status):
        """
        Method used to CREATE A IPAM IP Address.
        INPUT: ip_address
        INPUT: ip_netmask
        INPUT: ip_status - active, reserved, deprecated, dhcp, slaac
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create IP Address "
                         f"{ip_address}/{ip_netmask} with status {ip_status}.")

        ipam_ip_information = {"address": f"{ip_address}/{ip_netmask}", "status": ip_status}

        url = self.base_url + "api/ipam/ip-addresses/"
        if self.api_token:
            response = self.api_session.send_request(request_type="post", json_data=ipam_ip_information,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="IPAM addresse creation")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            response_data = defaultdict(None, response)
            log_worker.info(f"{self.this_class_name} - {this_method_name} - IP Address {ip_address}/{ip_netmask} was "
                            f"created.")
            return response_data
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_ipam_ip_address_by_id(self, ip_id):
        """
        Method used to DELETE A IPAM IP Address by ID.
        INPUT: ip_id
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete IP Address with ID {ip_id}.")

        url = self.base_url + f"api/ipam/ip-addresses/{ip_id}"
        if self.api_token:
            response = self.api_session.send_request(request_type="delete",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="IPAM address deletion")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - IP Address with {ip_id} was removed.")
            return True
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def create_racks(self, data):
        """
        Method used to create a set of racks using data from the DATA body.
        INPUT: data - list with JSON structures
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create racks using the provided "
                         f"data")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Json list: {data}")

        url = self.base_url + f"api/dcim/racks/"
        data = json.loads(data)

        if self.api_token:
            response = self.api_session.send_request(request_type="post", json_data=data,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="rack creation")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Racks from the provided data were "
                            f"successfully created.")
            return response

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def get_racks(self):
        """
        Method used to GET ALL Racks information.
        :returns: Dict {'id_1':{"name", "name", "url","url"}, 'id2':...} or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get all Racks.")

        return_data = {}
        url = self.base_url + "api/dcim/racks?limit=10000"
        if self.api_token:
            response = self.api_session.send_request(request_type="get",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="getting racks")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            for element in response["results"]:
                element_data = defaultdict(None, element)
                rack_id = element_data.get("id")
                rack_url = element_data.get("url")
                rack_name = element_data.get("name")

                return_data[rack_id] = {"url": rack_url, "name": rack_name}
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Racks information was extracted.")
            return defaultdict(None, return_data)

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_rack_by_id(self, rack_id):
        """
        Method used to DELETE A RACK by ID.
        INPUT: rack_id
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete Rack with ID {rack_id}.")

        url = self.base_url + f"api/dcim/racks/{rack_id}"
        if self.api_token:
            response = self.api_session.send_request(request_type="delete",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="rack deletion by ID")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Rack with {rack_id} was removed.")
            return True
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_racks(self, rack_ids):
        """
        Method used to delete all racks from a Netbox instance given by the list of rack ids.
        INPUT: rack_ids , string: [{"id": 23891},{"id": 23892}]
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete all racks.")

        url = self.base_url + f"api/dcim/racks/"

        if self.api_token:
            self.api_session.headers['content-type'] = "application/json"
            response = self.api_session.send_request(request_type="delete", json_data=rack_ids,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="multiple rack deletion")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Racks from the Netbox instance were "
                            f"successfully deleted.")
            return True

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def create_device_types(self, data):
        """
        Method used to create a set of device types using data from the DATA body.
        INPUT: data - list with JSON structures
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create device types using the "
                         f"provided data")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Json list: {data}")

        url = self.base_url + f"api/dcim/device-types/"
        data = json.loads(data)

        if self.api_token:
            response = self.api_session.send_request(request_type="post", json_data=data,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device type creation")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Device types from the provided data were "
                            f"successfully created.")
            return response

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def get_device_types(self):
        """
        Method used to GET ALL Device Types information.
        :returns: Dict {'id_1':{"name", "name1", "status","status1"}, 'id2':...} or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get all Devices.")

        return_data = {}
        url = self.base_url + "api/dcim/device-types?limit=10000"
        if self.api_token:
            response = self.api_session.send_request(request_type="get",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="getting device types")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            for element in response["results"]:
                element_data = defaultdict(None, element)
                device_id = element_data.get("id")
                device_status = element_data.get("status")
                device_name = element_data.get("name")

                return_data[device_id] = {"name": device_name, "status": device_status}
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Device Types information was extracted.")
            return defaultdict(None, return_data)
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_device_type_by_id(self, device_id):
        """
        Method used to DELETE A DEVICE TYPE by ID.
        INPUT: device type id
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete Device Type with ID "
                         f"{device_id}.")

        url = self.base_url + f"api/dcim/device-types/{device_id}"
        if self.api_token:
            response = self.api_session.send_request(request_type="delete",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device type deletion by id")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Device Type with {device_id} was removed.")
            return True
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_device_types(self, device_type_ids):
        """
        Method used to delete all device types from a Netbox instance given by the list of device type ids.
        INPUT: device_type_ids , string: [{"id": 23891},{"id": 23892}]
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete all device types.")

        url = self.base_url + f"api/dcim/device-types/"

        if self.api_token:
            response = self.api_session.send_request(request_type="delete", json_data=device_type_ids,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device type deletion")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(
                f"{self.this_class_name} - {this_method_name} - Device types from the Netbox instance were "
                f"successfully deleted.")
            return True

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def create_devices(self, data):
        """
        Method used to create a set of devices using data from the DATA body.
        INPUT: data - list with JSON structures
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create devices using the provided "
                         f"data")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Json list: {data}")

        url = self.base_url + f"api/dcim/devices/"

        if self.api_token:
            response = self.api_session.send_request(request_type="post", json_data=data,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device creation")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Devices from the provided data were "
                            f"successfully created.")
            return response

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def get_devices(self):
        """
        Method used to GET ALL Devices information.
        :returns: Dict {'id_1':{"name", "name1", "status","status1"}, 'id2':...} or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get all Devices.")

        return_data = {}
        url = self.base_url + "api/dcim/devices?limit=1000"
        if self.api_token:
            response = self.api_session.send_request(request_type="get",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="getting devices")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            for element in response["results"]:
                element_data = defaultdict(None, element)
                device_id = element_data.get("id")
                device_status = element_data.get("status")
                device_name = element_data.get("name")

                return_data[device_id] = {"name": device_name, "status": device_status}
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Devices information was extracted.")
            return defaultdict(None, return_data)

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_device_by_id(self, device_id):
        """'
        Method used to DELETE A DEVICE by ID.
        INPUT: device
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete Rack with ID {device_id}.")

        url = self.base_url + f"api/dcim/devices/{device_id}"
        if self.api_token:
            response = self.api_session.send_request(request_type="delete",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device deletion by id")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Device with {device_id} was removed.")
            return True

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def delete_devices(self, device_ids):
        """
        Method used to delete all devices from a Netbox instance given by the list of device ids.
        INPUT: device_ids , string: [{"id": 23891},{"id": 23892}]
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete all devices.")

        url = self.base_url + f"api/dcim/devices/"

        if self.api_token:
            response = self.api_session.send_request(request_type="delete", json_data=device_ids,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="device deletion")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Devices from the Netbox instance were "
                            f"successfully deleted.")
            return True

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def clear_netbox(self):
        """
        Method used to delete all racks, devices and device types in a Netbox instance in order to prepare the setup for
        a new inventory set.
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Deleting custom fields.")

        try:
            custom_field_ids = self.get_custom_fields().keys()
            while len(custom_field_ids) != 0:
                custom_field_ids_json = []
                for custom_field_id in custom_field_ids:
                    custom_field_ids_json.append({"id": f"{custom_field_id}"})
                if not self.delete_custom_fields(custom_field_ids_json):
                    log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete custom fields.")
                    return False
                custom_field_ids = self.get_custom_fields().keys()
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Custom fields were deleted.")

        except Exception as e:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete custom fields: {e}.")
            return False

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Deleting devices.")

        try:
            device_ids = self.get_devices().keys()
            while len(device_ids) != 0:
                device_ids_json = []
                for device_id in device_ids:
                    device_ids_json.append({"id": f"{device_id}"})
                if not self.delete_devices(device_ids_json):
                    log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete devices.")
                    return False
                device_ids = self.get_devices().keys()
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Devices were deleted.")

        except Exception as e:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete devices: {e}.")
            return False

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Deleting racks.")

        try:
            rack_ids = self.get_racks().keys()
            while len(rack_ids) != 0:
                rack_ids_json = []
                for rack_id in rack_ids:
                    rack_ids_json.append({"id": f"{rack_id}"})
                if not self.delete_racks(rack_ids_json):
                    log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete racks.")
                    return False
                rack_ids = self.get_racks().keys()
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Racks were deleted.")

        except Exception as e:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete racks: {e}.")
            return False

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Deleting device types.")

        try:
            device_type_ids = self.get_device_types().keys()
            while len(device_type_ids) != 0:
                device_type_ids_json = []
                for device_type_id in device_type_ids:
                    device_type_ids_json.append({"id": f"{device_type_id}"})
                if not self.delete_device_types(device_type_ids_json):
                    log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete device types.")
                    return False
                device_type_ids = self.get_device_types().keys()
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Device types were deleted.")

        except Exception as e:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Failed to delete device types: {e}.")
            return False

        return True

    def process_velocity_racks(self, racks, devices):
        """
        Method used to create racks processed from a Velocity JSON generated response.
        INPUT: racks - JSON structure with rack information.
        INPUT: devices - JSON structure with device information.
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Performing basic cleanup.")
        try:
            cleanup_result = self.clear_netbox()
            if not cleanup_result:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Cleanup failed.")
                return False
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Cleanup is completed.")
        except Exception as e:
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Basic cleanup failed: {e}")
            return False

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create racks using the provided "
                         f"data.")

        total_racks = len(racks['devices'])
        total_devices = len(devices['devices'])

        ignore_duplication_list = []
        device_sets = []

        rack_create = '['
        device_create = '['
        device_type_create = '['
        rack_occupied_positions = {}

        if self.api_token:
            for i in range(0, total_racks):
                rack_name = racks['devices'][i]['name']
                properties_count = len(racks['devices'][i]['properties'])
                max_installed_power = "N/A"
                max_power_consumption = "N/A"
                pdu_reported_power = "N/A"
                for j in range(0, properties_count):
                    if racks['devices'][i]['properties'][j]['name'] == "Max Installed Power":
                        max_installed_power = racks['devices'][i]['properties'][j]['value']
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Rack Max Installed Power: "
                                         f"{max_installed_power}")
                    if racks['devices'][i]['properties'][j]['name'] == "Max Power Consumption":
                        max_power_consumption = racks['devices'][i]['properties'][j]['value']
                        log_worker.debug(
                            f"{self.this_class_name} - {this_method_name} - Rack Max Power Consumption: "
                            f"{max_power_consumption}")
                    if racks['devices'][i]['properties'][j]['name'] == "PDU Reported Power":
                        pdu_reported_power = racks['devices'][i]['properties'][j]['value']
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Rack PDU reported power: "
                                         f"{pdu_reported_power}")
                    if max_installed_power != "N/A" and max_power_consumption != "N/A" and pdu_reported_power != "N/A":
                        break

                rack_temp_row = rack_name[4]
                rack_temp_rack = rack_name[-2:]
                temp_create = f'{{"site" : 1,"status":"active","location":null,"name":"{rack_name}","u_height": 45,' \
                              f'"custom_fields":{{"labrow": "{rack_temp_row}", "racknumber": "{rack_temp_rack}",' \
                              f'"maxinstalledpower": "{max_installed_power}", "maxpowerconsumption":"' \
                              f'{max_power_consumption}", "pdureportedpower": "{pdu_reported_power}"}}}} '
                rack_create = rack_create + temp_create + ','

            custom_fields = [
                {
                    "content_types": [
                        "dcim.device",
                        "dcim.rack"
                    ],
                    "type": "text",
                    "name": "labrow",
                    "label": "Lab Row"
                },
                {
                    "content_types": [
                        "dcim.device",
                        "dcim.rack"
                    ],
                    "type": "text",
                    "name": "racknumber",
                    "label": "Rack Number"
                },
                {
                    "content_types": [
                        "dcim.rack"
                    ],
                    "type": "text",
                    "name": "maxinstalledpower",
                    "label": "Max Installed Power"
                },
                {
                    "content_types": [
                        "dcim.device",
                        "dcim.rack"
                    ],
                    "type": "text",
                    "name": "maxpowerconsumption",
                    "label": "Max Power Consumption"
                },
                {
                    "content_types": [
                        "dcim.rack"
                    ],
                    "type": "text",
                    "name": "pdureportedpower",
                    "label": "PDU Reported Power"
                }
            ]

            self.create_custom_fields(custom_fields)

            rack_create = rack_create[:-1] + ']'
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating the following racks: "
                             f"{rack_create}")
            netbox_racks = self.create_racks(rack_create)
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - The following racks were created: "
                             f"{netbox_racks}")
            temp_list = []
            units_number_list = []
            for i in range(0, total_devices):
                device_name = devices['devices'][i]['name']
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Working on device: {device_name}")
                device_host_id = devices['devices'][i]['hostId']
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - {device_name} has hostId "
                                 f"{device_host_id}")
                device_host_name = ''
                device_host_netbox_id = ''
                device_positioning = ''
                rack_units_number = ''
                face = ''

                properties_count = len(devices['devices'][i]['properties'])
                for j in range(0, properties_count):
                    if devices['devices'][i]['properties'][j]['name'] == "Rack Positioning":
                        device_positioning = devices['devices'][i]['properties'][j]['value']
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Device positioning: "
                                         f"{device_positioning}")
                    if devices['devices'][i]['properties'][j]['name'] == "No of Rack Units":
                        rack_units_number = devices['devices'][i]['properties'][j]['value']
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - No of Rack Units: "
                                         f"{rack_units_number}")
                    if devices['devices'][i]['properties'][j]['name'] == "Rack Face":
                        face = devices['devices'][i]['properties'][j]['value'].lower()
                        if face == '':
                            face = 'front'
                        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Rack face: {face}")
                    if device_positioning and rack_units_number and face:
                        break
                if not device_positioning:
                    log_worker.warning(f"{self.this_class_name} - {this_method_name} - 'Rack Positioning' property "
                                       f"was not found for {devices['devices'][i]['name']} or the property's value is "
                                       f"empty. Device will be skipped!")
                    continue
                if not device_positioning:
                    log_worker.warning(  f"{self.this_class_name} - {this_method_name} - 'No of Rack Units' property "
                                         f"was not found for {devices['devices'][i]['name']} or the property's value "
                                         f"is empty. Device will be skipped!")
                    continue
                if not face:
                    log_worker.warning( f"{self.this_class_name} - {this_method_name} - 'Rack Face' property was not "
                                        f"found for {devices['devices'][i]['name']} or the property's value is empty. "
                                        f"Device will be skipped!")
                    continue
                try:
                    if device_positioning[0] == "U" and int(device_positioning[1:]):
                        log_worker.debug(
                            f"{self.this_class_name} - {this_method_name} - Device positioning {device_positioning} "
                            f"has valid format.")
                        device_positioning = device_positioning[1:]
                        temp_list.append(device_positioning)
                except Exception as e:
                    log_worker.debug(
                        f"{self.this_class_name} - {this_method_name} - Device positioning {device_positioning} does "
                        f"not have valid format.")
                    continue
                if rack_units_number and int(rack_units_number) > 0:
                    log_worker.debug(
                        f"{self.this_class_name} - {this_method_name} - Rack unit number {rack_units_number} has "
                        f"valid format.")
                    units_number_list.append(int(rack_units_number))
                else:
                    log_worker.warning(
                        f"{self.this_class_name} - {this_method_name} - {device_name} has invalid rack unit number: "
                        f"{rack_units_number}.")

                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Looking for rack ID")
                for j in range(total_racks):
                    if racks['devices'][j]['id'] == device_host_id:
                        device_host_name = racks['devices'][j]['name']
                        break
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Found rack {device_host_name}")
                if device_host_name:
                    for j in range(0, len(netbox_racks)):
                        if device_host_name == netbox_racks[j]['name']:
                            device_host_netbox_id = netbox_racks[j]['id']
                            break
                if device_host_name not in rack_occupied_positions.keys():
                    rack_occupied_positions[device_host_name] = []
                ignored = 0
                current_slots = []
                for j in range(int(device_positioning), int(device_positioning) + int(rack_units_number)):
                    current_slots.append(j)
                for j in range(0, len(rack_occupied_positions[device_host_name])):
                    if [k for k in current_slots if k in rack_occupied_positions[device_host_name][j]['slots']] \
                            and rack_occupied_positions[device_host_name][j]['face'] == face:
                        ignore_duplication_list.append(f"{device_name} (positions {current_slots} - "
                                                       f"{rack_units_number} slots) conflicts with "
                                                       f"{rack_occupied_positions[device_host_name][j]['deviceName']} "
                                                       f"placed on face "
                                                       f"{rack_occupied_positions[device_host_name][j]['face']}, "
                                                       f"slots {rack_occupied_positions[device_host_name][j]['slots']}"
                                                       f"{device_host_name}")
                        ignored = 1
                        break
                if device_host_netbox_id and ignored == 0 and int(rack_units_number) > 0:
                    rack_occupied_positions[device_host_name].append(
                        {'deviceName': device_name, 'face': face, 'slots': current_slots})
                    if face == "back":
                        face = "rear"
                    temp_create = f'{{"rack" : {device_host_netbox_id},"site": 1,"device_type":{rack_units_number}, ' \
                                  f'"device_role" : 1,"name":"{device_name}", "position":{device_positioning},' \
                                  f'"face": "{face}"}}'
                    device_create = device_create + temp_create + ','
                    if device_create.count('device_role') % 500 == 0:
                        device_sets.append(device_create[:-1] + ']')
                        device_create = '['

            if device_create != '[':
                device_create = device_create[:-1] + ']'
                device_sets.append(device_create)

            temp_temp_list = []
            for i in units_number_list:
                if i not in temp_temp_list:
                    temp_temp_list.append(i)
            temp_temp_list.sort()
            units_number_list = temp_temp_list
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Final list of unit numbers: "
                             f"{units_number_list}.")

            for unit_number in units_number_list:
                temp_create = f'{{"manufacturer" : 1,"model": "Automation Generated Height {unit_number}",' \
                              f'"slug":"automation-generated-{unit_number}", "is_full_depth":"false",' \
                              f' "u_height" : {unit_number}}}'
                device_type_create = device_type_create + temp_create + ','
            device_type_create = device_type_create[:-1] + ']'
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating the following device types: "
                             f"{device_type_create}.")
            device_types = self.create_device_types(device_type_create)
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - The following device types were created: "
                             f"{device_types}.")

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Replacing device_type values for devices "
                             f"with IDs.")
            temp_device_sets = []

            for device_create in device_sets:
                device_create = json.loads(device_create)
                for device in range(0, len(device_create)):
                    old_device_type = device_create[device]['device_type']
                    device_type_id = ''
                    for device_type in range(0, len(device_types)):
                        if device_types[device_type]['u_height'] == int(old_device_type):
                            device_type_id = device_types[device_type]['id']
                            break
                    if device_type_id:
                        device_create[device]['device_type'] = device_type_id
                temp_device_sets.append(device_create)
            device_sets = temp_device_sets

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - "
                             f"Extracting all properties from the devices.")
            property_collection = self.get_all_existing_properties(devices)

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating custom fields set of properties "
                             f"for NetBox.")
            property_collection = self.convert_properties_velocity_to_netbox(property_collection)

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Removing existing fields added earlier.")
            already_added = [p for p in range(len(property_collection)) if
                             property_collection[p]['name'] in ["labrow", "racknumber", "maxinstalledpower",
                                                                "maxpowerconsumption", "pdureportedpower"]]

            for p in already_added:
                log_worker.debug(
                    f"{self.this_class_name} - {this_method_name} - Removing "
                    f"{property_collection[p - already_added.index(p)]}.")
                property_collection.pop(p - already_added.index(p))

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Create the rest of NetBox custom fields.")
            self.create_custom_fields(property_collection)
            custom_fields = self.get_custom_fields()

            log_worker.debug(f"{self.this_class_name} - {this_method_name} - Integrate custom fields in existing "
                             f"device sets.")
            device_sets = self.integrate_custom_fields(custom_fields, device_sets, devices)

            for device_create in device_sets:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Creating the following devices:"
                                 f"{device_create}.")
                devices = self.create_devices(device_create)
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - The following devices were created: "
                                 f"{devices}.")
            ignore_duplication_list = str(ignore_duplication_list).replace("'", '"')
            log_worker.debug(f"{self.this_class_name} - {this_method_name} - The following devices were ignored "
                             f"because of conflicting positioning: {ignore_duplication_list}.")
            log_worker.info(f"Finished: PASSED")
            return True
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def get_all_existing_properties(self, devices):
        """
        Method used to get all device properties from a Velocity JSON structure.
        """

        this_method_name = sys._getframe().f_code.co_name
        log_worker.info(f"{self.this_class_name} - {this_method_name} - Extracting all properties from the devices.")
        property_collection = {}

        for i in range(len(devices['devices'])):
            for j in range(len(devices['devices'][i]['properties'])):
                if devices['devices'][i]['properties'][j]['name'] not in property_collection.keys():
                    property_collection[devices['devices'][i]['properties'][j]['name']] = \
                        devices['devices'][i]['properties'][j]['type']

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Properties were extracted successfully.")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Properties were extracted: {property_collection}")
        return property_collection

    def convert_properties_velocity_to_netbox(self, properties_collection):
        """
        Method used to convert Velocity property JSON structure to NetBox custom fields JSON structure.
        INPUT: properties_collection - dictionary with Velocity device properties
        :returns: netbox_properties - dictionary with Netbox device properties
        """

        this_method_name = sys._getframe().f_code.co_name
        log_worker.info(f"{self.this_class_name} - {this_method_name} - Converting properties from Velocity type to "
                        f"Netbox type.")
        netbox_properties = []

        for velocity_property in properties_collection.keys():
            if velocity_property != "password":
                property_body = {'name': velocity_property.lower(), 'content_types': ["dcim.device"]}
                for char in ". ,-/":
                    property_body['name'] = property_body['name'].replace(char, "")
                property_body['label'] = velocity_property
                property_body['type'] = "text"
                property_body['weight'] = 100
                if property_body['name'] == "ipaddress":
                    property_body['weight'] = 0
                netbox_properties.append(property_body)

        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Properties were processed successfully.")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Properties were processed:"
                         f" {netbox_properties}")
        return netbox_properties

    def delete_custom_fields(self, custom_field_ids):
        """
        Method used to delete all custom fields from a Netbox instance given by the list of custom field ids.
        INPUT: custom_field_ids , string: [{"id": 23891},{"id": 23892}]
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to delete all custom fields.")

        url = self.base_url + f"api/extras/custom-fields/"

        if self.api_token:
            return self.api_session.send_request(request_type="delete", json_data=custom_field_ids,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="custom field deletion")
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def get_custom_fields(self):
        """
        Method used to GET ALL custom fields information.
        :returns: Dict {'id_1':{"name", "name1", "status","status1"}, 'id2':...} or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get all custom fields.")

        return_data = {}
        url = self.base_url + "api/extras/custom-fields?limit=10000"
        if self.api_token:
            response = self.api_session.send_request(request_type="get",
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="getting custom fields")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            for element in response["results"]:
                element_data = defaultdict(None, element)
                custom_field_id = element_data.get("id")
                custom_field_type = element_data.get("type")
                custom_field_name = element_data.get("name")
                custom_field_label = element_data.get("label")

                return_data[custom_field_id] = {"name": custom_field_name, "type": custom_field_type,
                                                "label": custom_field_label}
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Custom field information was extracted.")
            return return_data
        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def create_custom_fields(self, data):
        """
        Method used to create a set of custom fields using data from the DATA body.
        INPUT: data - list with JSON structures
        :returns: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create custom fields using the "
                         f"provided data")
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Json list: {data}")

        url = self.base_url + f"api/extras/custom-fields/"

        if self.api_token:
            response = self.api_session.send_request(request_type="post", json_data=data,
                                                     url=url, log_worker=log_worker, method_name=this_method_name,
                                                     request_description="custom field creation")
            if response:
                log_worker.debug(f"{self.this_class_name} - {this_method_name} - Request on {url} completed.")
            else:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Request on {url} failed.")
                return False

            log_worker.info(f"{self.this_class_name} - {this_method_name} - Custom fields from the provided data were "
                            f"successfully created.")
            return response

        else:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - No session to execute the action")
            return False

    def integrate_custom_fields(self, custom_fields, device_sets, velocity_devices):
        """
        Custom procedure to add new custom fields in existing device sets used for NetBox device creation
        INPUT: custom_fields - dictionary with custom fields to be included in the sets of devices
        INPUT: device_sets - existing set of NetBox devices
        INPUT: velocity_devices - existing set of Velocity devices
        :returns: device_sets - resulting set of NetBox devices
        """

        this_method_name = sys._getframe().f_code.co_name
        for device_set_ind in range(len(device_sets)):
            for device_ind in range(len(device_sets[device_set_ind])):
                device_name = device_sets[device_set_ind][device_ind]['name']
                vel_index = [i for i in range(len(velocity_devices['devices'])) if
                             velocity_devices['devices'][i]['name'] == device_name][0]
                device_sets[device_set_ind][device_ind]['custom_fields'] = {}
                for property_ind in range(len(velocity_devices['devices'][vel_index]['properties'])):
                    vel_prop_name = velocity_devices['devices'][vel_index]['properties'][property_ind]['name']
                    vel_prop_value = str(velocity_devices['devices'][vel_index]['properties'][property_ind]['value'])
                    if vel_prop_name.lower() != 'password':
                        try:
                            netbox_custom_field = [i for i in custom_fields.keys() if custom_fields[i]['label'] ==
                                                   vel_prop_name][0]
                            device_sets[device_set_ind][device_ind]['custom_fields'][
                                custom_fields[netbox_custom_field]["name"]] = vel_prop_value
                        except:
                            log_worker.error( f"{self.this_class_name} - {this_method_name} - Velocity property "
                                              f"{vel_prop_name} was not found in the list of custom fields: "
                                              f"{custom_fields.keys()}")

        return device_sets


if __name__ == "__main__":
    pass
