#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Alin Andronache
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Script used to export the rack structures from Velocity into the Netbox platform """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import libs.libs_netbox.NetBox as NetBox
import helpers.Logger as Local_logger
import libs.libs_velocity.Velocity as Velocity
from parameters.global_parameters import Velocity as VELOCITYPARAMS
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import Netbox as NETBOXPARAMS

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_create_netbox_racks.txt")


def main():
    velocity = VELOCITYPARAMS['host']
    velo_user = VELOCITYPARAMS['user']
    velo_password = VELOCITYPARAMS['pass']

    log_worker.info(f"Opening Velocity session to {velocity} with user {velo_user}")
    try:
        velocity_session = Velocity.API(velocity, velo_user, velo_password)
        log_worker.info(f"Successfully opened the Velocity session.")
    except Exception as e:
        log_worker.error(f"Failed to open the Velocity session.")
        log_worker.info(f"Error: {e}.")
        log_worker.error(f"Finished: FAILED")
        return

    log_worker.info(f"Getting Netbox connection details.")

    Netbox_Velo_service_name = NETBOXPARAMS['service_name_velo']
    properties_list = ['ipAddress', 'password']

    NetBox_host = velocity_session.get_resource_property_value(Netbox_Velo_service_name, properties_list)
    if not NetBox_host:
        log_worker.error(f"Failed to get the properties for the {Netbox_Velo_service_name} device.")
        log_worker.error(f"Finished: FAILED")
        return
    else:
        log_worker.info(f"Obtained the properties for the {Netbox_Velo_service_name} device.")

    netbox = NetBox_host['ipAddress']
    netbox_token = NetBox_host['password']

    log_worker.info(f"Getting rack and device structures from Velocity.")
    rack_structure, device_structure = velocity_session.get_airtel_racks(rack_template_name="Rack")

    log_worker.info(f"Opening Velocity session to {velocity} with user {velo_user}")
    try:
        netbox_session = NetBox.API(netbox, netbox_token)
        log_worker.info(f"Successfully opened the Netbox session.")
    except Exception as e:
        log_worker.error(f"Failed to open the Netbox session.")
        log_worker.info(f"Error: {e}.")
        log_worker.error(f"Finished: FAILED")
        return

    log_worker.info(f"Creating the obtained racks and devices in Netbox.")
    result = netbox_session.process_velocity_racks(rack_structure, device_structure)
    if not result:
        log_worker.error(f"Failed to create the racks and devices in Netbox.")
        log_worker.error(f"Finished: FAILED")
        return
    else:
        log_worker.info(f"Racks and devices were successfully created in Netbox.")
        log_worker.info(f"Finished: PASSED")


if __name__ == "__main__":
    main()
