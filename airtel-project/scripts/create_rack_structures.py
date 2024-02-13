#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Alin Andronache
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Script used to create new rack structures in Velocity the platform """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import helpers.Logger as Local_logger
import libs.libs_velocity.Velocity as Velocity
from parameters.global_parameters import Velocity as VELOCITYPARAMS
from parameters.global_parameters import Reporting as REPORTINGPARAMS

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_create_rack_structures.txt")


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

    log_worker.info(f"Getting all resources from Velocity.")
    folder_filter_list = ["folderId:!:a6b78358-5e37-453e-9632-4bc6045ed116",
                          "folderId:!:7fa332cc-9f85-4369-b3a9-c3c9ecaadc13"]
    log_worker.info(f"The resources from the following folders will be ignored: {folder_filter_list}")

    inventory_json = velocity_session.get_resources(folder_filter_list)
    if not inventory_json:
        log_worker.error(f"Failed to get the requested resources.")
        log_worker.error(f"Finished: FAILED")
        return
    else:
        log_worker.info(f"The requested resources were successfully obtained.")

    final_result = velocity_session.create_rack_structure(inventory_json, lab_row_template_name="Lab Row",
                                                          rack_template_name="Rack")
    if not final_result:
        log_worker.error(f"Failed to create the rack structures in Velocity.")
        log_worker.error(f"Finished: FAILED")
        return
    else:
        log_worker.info(f"The rack structures were successfully created in Velocity.")
        log_worker.info(f"Finished: PASSED")


if __name__ == "__main__":
    main()
