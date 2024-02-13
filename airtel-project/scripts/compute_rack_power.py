#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : George Popovici
# Created Date: 11.2021
# version ='1.0'
# ---------------------------------------------------------------------------
""" Script is reading power information from Velocity and upload it to OpenSearh db """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import libs.libs_velocity.Velocity as Velocity
import libs.libs_opensearch.OpenSearch as OpenSearch
import re
import datetime
import helpers.Logger as Local_logger
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import Velocity as VELOCITYPARAMS
from parameters.global_parameters import OpenSearch as OPENSEARCHPARAMS

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_compute_rack_power.txt")


def main():

    # Get Velocity details and open session
    velocity = VELOCITYPARAMS['host']
    velo_user = VELOCITYPARAMS['user']
    velo_password = VELOCITYPARAMS['pass']

    rack_template_id = "2ec509fe-a50c-4328-b3d9-76a98e2ee560"

    velocity_session = Velocity.API(velocity, velo_user, velo_password)

    # Get OpenSearch credentials from Velocity and open session
    open_search_velo_service_name = OPENSEARCHPARAMS['service_name_velo']
    properties_list = ['ipAddress', 'username', 'password']
    open_search_host = velocity_session.get_resource_property_value(open_search_velo_service_name, properties_list)
    if not open_search_host:
        log_worker.error(f"Finished: Could not get OpenSearch host details")
        log_worker.error(f"Finished: FAIL")
        return

    open_search_client = OpenSearch.API(open_search_host['ipAddress'], open_search_host['username'], open_search_host['password'])

    rack_structure = velocity_session.get_airtel_racks_v2(rack_template_id)
    if not rack_structure:
        log_worker.error(f"Finished: Could not get rack structure")
        log_worker.error(f"Finished: FAIL")
        return

    # Delete existing entries related to rack power
    if not open_search_client.delete_index():
        log_worker.warning(f"Could not delete open search index, continue to write new entries on it")

    # loop through all racks
    for rack in rack_structure['devices']:
        rack_id = rack['id']
        rack_name = rack['name']
        rack_max_power = 0
        pdu_reported_power = 0
        max_installed_power = 0
        available_power_vs_pdu_reported = 0
        available_power_vs_user_reported = 0

        # Get devices that has parent the current rack in iteration
        filterlist = ["hostId::"+rack['id']]
        rack_devices = velocity_session.get_resources(filterlist)
        if not rack_devices:
            log_worker.error(f"Finished: Could not get rack devices")
            log_worker.error(f"Finished: FAIL")
            return

        # Get Max Power Consumption from each device under the rack and do the sum
        # Do the same for PDU Reported Power
        for rack_device in rack_devices['devices']:
            for rack_device_property in rack_device['properties']:
                if rack_device_property['name'] == "Max Power Consumption" and rack_device_property['value']:
                    rack_max_power += int(rack_device_property['value'])
                if rack_device_property['name'] == "PDU Reported Power" and rack_device_property['value']:
                    pdu_reported_power += int(rack_device_property['value'])

        # Update Max Power Consumption / PDU Reported Power at rack level
        definition_id_max_power = 0
        definition_id_pdu = 0
        for property_list in rack['properties']:
            if property_list['name'] == "Max Power Consumption":
                definition_id_max_power = property_list['definitionId']
            if property_list['name'] == "PDU Reported Power":
                definition_id_pdu = property_list['definitionId']
            if property_list['name'] == "Max Installed Power":
                max_installed_power = int(property_list['value'])

        available_power_vs_user_reported = max_installed_power - rack_max_power
        available_power_vs_pdu_reported = max_installed_power - pdu_reported_power

        log_worker.info(f"Update rack: {rack_name}")
        log_worker.info(f"----Max Power Consumption: {rack_max_power}")
        log_worker.info(f"----Max Installed Power: {max_installed_power}")
        log_worker.info(f"----PDU Reported Power: {pdu_reported_power}")
        log_worker.info(f"----Available Power vs User reported: {available_power_vs_user_reported}")
        log_worker.info(f"----Available Power vs PDU reported: {available_power_vs_pdu_reported}")
        if definition_id_max_power != 0:
            if not velocity_session.update_device_property(rack_id, definition_id_max_power, rack_max_power):
                log_worker.error(f"Could not update max power for rack {rack_id}")
        if definition_id_pdu != 0:
            if not velocity_session.update_device_property(rack_id, definition_id_pdu, pdu_reported_power):
                log_worker.error(f"Could not update pdu power for rack {rack_id}")

        # Prepare the document and write to OpenSearch
        rack_row = "TBD"
        rack_number = "TBD"
        m = re.search('(.+)_(RACK.+)', rack_name)

        if m:
            rack_row = m.group(1)
            rack_number = m.group(2)

        document = {
            'timestamp': datetime.datetime.now(),
            'rack_name': rack_name,
            'rack_row': rack_row,
            'rack_number': rack_number,
            'max_power_consumption': rack_max_power,
            'max_installed_power': max_installed_power,
            'pdu_reported_power': pdu_reported_power,
            'available_power_vs_user_reported': available_power_vs_user_reported,
            'available_power_vs_pdu_reported': available_power_vs_pdu_reported
        }

        if not open_search_client.create_document(document):
            log_worker.error(f"Could not write document {document}")
            log_worker.info(f"Finished: FAILED")
            return

    log_worker.info(f"Finished: PASSED")


if __name__ == "__main__":
    main()
