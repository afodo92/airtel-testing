#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Cosmin-Florin Stanuica, Alin Andronache
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Script used to deploy a runlist execution in Velocity based on Zephyr cycle information """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import os
import sys
import time
from datetime import datetime

# sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import helpers.Logger as Local_logger
import libs.libs_velocity.Velocity as Velocity
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import Jira as JIRAPARAMS
from parameters.global_parameters import Velocity as VELOCITYPARAMS
# from libs.libs_jira.JiraCore import JiraCore
from libs.libs_zephyr.ZephyrCore import ZephyrCore

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_run_zephyr_automation_cycle.txt")


def __jira_get_project_id(session, project_key):
    j_project_details = session.get_project_details(project_key=project_key)
    if not j_project_details:
        log_worker.error("Failed to get Jira Project details")
        return 0
    else:
        if "id" not in j_project_details.keys() or "versions" not in j_project_details.keys():
            log_worker.error("Failed to identify Jira Project ID or Version")
            return 0
    log_worker.info(f"Identified Jira Project ID for project {project_key}")
    return j_project_details["id"]


def __jira_get_project_version_id(session, project_key, jira_project_version_name):
    if jira_project_version_name.lower() == "unscheduled":
        log_worker.info(
            f"Identified Jira Project Version ID for project {project_key} with version name {jira_project_version_name}")
        return -1

    j_project_details = session.get_project_details(project_key=project_key)
    if "versions" not in j_project_details.keys():
        log_worker.error("Failed to get Jira Project Version")
        return 0
    for version in j_project_details["versions"]:
        if "name" not in version.keys() or "id" not in version.keys():
            continue
        if version["name"] == jira_project_version_name:
            log_worker.info(
                f"Identified Jira Project Version ID for project {project_key} with version name {jira_project_version_name}")
            return version["id"]
    return 0


def __zephyr_get_cycle_id(session, project_id, project_version, cycle_name):
    z_cycles_details = session.get_cycles(project_id=project_id, project_version=project_version)
    if not z_cycles_details:
        log_worker.error("Failed to get Zephyr Test Cycles details")
        return 0
    else:
        for current_cycle_id in z_cycles_details.keys():
            if isinstance(z_cycles_details[current_cycle_id], dict):
                if "name" not in z_cycles_details[current_cycle_id].keys():
                    continue
                if z_cycles_details[current_cycle_id]["name"] == cycle_name:
                    log_worker.info(f"Identified Zephyr Test Tycle ID for cycle {cycle_name}")
                    return current_cycle_id
            else:
                continue
    return 0


def __zephyr_get_all_cycle_test_keys(session, project_id, project_version, cycle_id):
    def get_folder_ids(z_folders_details):
        folder_ids = []

        if z_folders_details and len(z_folders_details):
            for folder in z_folders_details:
                if "folderId" not in folder:
                    continue
                log_worker.debug(f"Identified Zephyr folder {folder['folderId']}")
                folder_ids.append(folder["folderId"])

        return folder_ids

    def get_executions_test_keys(z_executions):
        executions_test_keys = []
        if "executions" in z_executions.keys():
            for execution in z_executions["executions"]:
                if "issueKey" not in execution.keys():
                    continue
                log_worker.debug(f"Identified Zephyr execution {execution['issueKey']}")
                executions_test_keys.append(execution["issueKey"])

        return executions_test_keys

    test_keys_list = []

    ''' Get Zephyr Folders included in the Test Cycle '''
    z_folders_details = session.get_cycle_folders_information_by_id(project_id=project_id,
                                                                    project_version=project_version, cycle_id=cycle_id)
    zephyr_folder_ids = get_folder_ids(z_folders_details)

    ''' Get Zephyr Executions included DIRECTLY in the Test Cycle '''
    z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version,
                                                             cycle_id=cycle_id)
    if not z_executions:
        log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id}")
    else:
        test_keys_list += get_executions_test_keys(z_executions)

    ''' Get Zephyr Executions included in the Test Cycle Folders '''
    for folder_id in zephyr_folder_ids:
        z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version,
                                                                 cycle_id=cycle_id, folder_id=folder_id)
        if not z_executions:
            log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id} folder {folder_id}")
        else:
            test_keys_list += get_executions_test_keys(z_executions)

    return test_keys_list


def zephyr_get_test_keys_from_cycle(jira_project_key, jira_project_version_name, zephyr_test_cycle_name,
                                    jira_session, zephyr_session):
    ''' Initialize variables'''
    return_data = {"ok": False, "test_cycle_id": 0, "test_keys_list": []}

    ''' Get Jira Project ID and Version - needed for Zephyr actions '''
    jira_project_id = __jira_get_project_id(session=jira_session, project_key=jira_project_key)
    jira_project_version_id = __jira_get_project_version_id(session=jira_session, project_key=jira_project_key,
                                                            jira_project_version_name=jira_project_version_name)
    if jira_project_id == 0 or jira_project_version_id == 0:
        log_worker.error(
            f"Failed to identify IDs for project {jira_project_key} with Version name {jira_project_version_name}")
        return return_data

    ''' Get Zephyr Cycle ID '''
    zephyr_cycle_id = __zephyr_get_cycle_id(session=zephyr_session, project_id=jira_project_id,
                                            project_version=jira_project_version_id, cycle_name=zephyr_test_cycle_name)
    if zephyr_cycle_id == 0:
        log_worker.error(f"Failed to identify ID for Test Cycle {zephyr_test_cycle_name}")
        return return_data

    ''' Get Test Keys included in the Zephyr Test Cycle '''
    return_data["ok"] = True
    return_data["test_cycle_id"] = zephyr_cycle_id
    return_data["test_keys_list"] = __zephyr_get_all_cycle_test_keys(session=zephyr_session, project_id=jira_project_id,
                                                                     project_version=jira_project_version_id,
                                                                     cycle_id=zephyr_cycle_id)

    ''' Return the data'''
    return return_data


def __zephyr_create_cycle(session: ZephyrCore, project_id, project_version, cycle_name, build, test_keys_to_include):
    z_cycle_information = session.create_cycle(name=cycle_name, project_id=project_id, project_version=project_version,
                                               build=build)

    if z_cycle_information:
        log_worker.info(f"Created Zephyr cycle {cycle_name}")
        test_cycle_id = z_cycle_information["id"]

        zephyr_job_information = session.add_tests_to_cycle_by_key_list(project_id=project_id,
                                                                        project_version=project_version,
                                                                        cycle_id=test_cycle_id,
                                                                        test_key_list=test_keys_to_include)
        if not zephyr_job_information or "jobProgressToken" not in zephyr_job_information.keys():
            log_worker.error("Failed to start job to add tests to the Test Cycle")
            return 0
        else:
            for time_slot in range(60):
                zephyr_job_details = session.get_job_progress_by_token(
                    job_progress_token=zephyr_job_information["jobProgressToken"])
                if not zephyr_job_details or "progress" not in zephyr_job_details.keys():
                    log_worker.error("Failed to get progress from add tests to Test Cycle job ")
                else:
                    if zephyr_job_details["progress"] == 1:
                        log_worker.info(f"Added Tests to Zephyr cycle {cycle_name}")
                        return test_cycle_id
                time.sleep(2)
            log_worker.error("Failed to complete job to add tests to the Test Cycle - Max timer expired")
            return 0
    else:
        log_worker.error(f"Failed to create Zephyr cycle {cycle_name}")
        return 0


def deploy_runlist_execution(cycle_id, keys_list, runlist_name, jira_project_version_name, jira_project_key,
                             zephyr_test_cycle_name, zephyr_build, velocity_session, topology_id, jira_session,
                             zephyr_session):
    automation_results_data = {}
    testcases_list = []

    # TODO - Identify full path for MONITOR script using Filter and velocity_session.get_automation_assets(filters ={"tags": ["MONITOR"]})
    # save full path for monitor script in a variable named monitor_test_path
    tag = "airtel_monitor"
    filter_set = {"tags": [tag]}
    automation_assets = velocity_session.get_automation_assets(filters=filter_set)
    if len(automation_assets["content"]) != 0:
        monitor_test_path = automation_assets["content"][0]["fullPath"]
    # TODO - Identify full path for HTML GENERATOR script using Filter and velocity_session.get_automation_assets(filters ={"tags": ["REPORTER"]})
    # save full path for monitor script in a variable named html_test_path
    tag = "airtel_reporter"
    filter_set = {"tags": [tag]}
    automation_assets = velocity_session.get_automation_assets(filters=filter_set)
    if len(automation_assets["content"]) != 0:
        reporter_test_path = automation_assets["content"][0]["fullPath"]

    if runlist_name == "N/A":

        '''Get all matching scripts by list of tags'''
        zephyr_create_cycle_flag = 0
        to_exclude = []
        execution_name = cycle_id
        for tag in keys_list:

            filter_set = {"tags": [tag]}
            automation_assets = velocity_session.get_automation_assets(filters=filter_set)
            if len(automation_assets["content"]) != 0:

                log_worker.debug(f"Found {len(automation_assets['content'])} automation assets mathing tag {tag}")

                automation_results_data[tag] = {}
                automation_results_data[tag]["test_name"] = automation_assets["content"][0]["name"]
                log_worker.info(f"Testcase {automation_assets['content'][0]['name']} was found for tag: {tag}")
                testcases_list.append(automation_assets["content"][0]["fullPath"])
                # TODO - Append monitor previous result script
                testcases_list.append(monitor_test_path)
            else:
                log_worker.warning(f"No testcases were found for tag: {tag}")
                to_exclude.append(tag)

        log_worker.warning(f"Testcases for tags {to_exclude} were not found and will be ignored.")
        for tag in to_exclude:
            keys_list.remove(tag)

        if len(automation_results_data.keys()) == 0:
            log_worker.warning(f"No testcases were found for tags {keys_list}, exiting execution.")
            return {"ok": False}

    else:
        log_worker.info(f"Getting the list of runlist test cases for {runlist_name}")
        zephyr_create_cycle_flag = 1
        zephyr_test_cycle_name = runlist_name + "_" + datetime.now().strftime("%d-%m-%Y_%Hh%Mm%Ss")
        keys_list = []
        execution_name = runlist_name

        runlist_info = velocity_session.get_runlist(runlist_name=runlist_name)
        log_worker.debug(f"Runlist info: {runlist_info}")

        topology_id = runlist_info["general"]["topologyId"]
        for i in range(0, len(runlist_info["main"]["items"])):
            full_path = runlist_info["main"]["items"][i]["path"]
            log_worker.info(f"Testcase full path: {full_path}")
            filter_set = {"fullPath": full_path}
            automation_asset_info = velocity_session.get_automation_assets(filters=filter_set)

            if len(automation_asset_info["content"]) == 1:
                log_worker.debug(f"Following testcases were found while using filter: {filter_set}: "
                                 f"{automation_asset_info}")
                tag = automation_asset_info["content"][0]["tags"][0]
                automation_results_data[tag] = {}
                automation_results_data[tag]["test_name"] = automation_asset_info["content"][0]["name"]
                testcases_list.append(full_path)
                # TODO - Append monitor previous result script
                testcases_list.append(monitor_test_path)
                log_worker.debug(f"Current list of testcases: {testcases_list}")
                keys_list.append(tag)
                log_worker.debug(f"Current list of keys: {keys_list}")

            else:
                log_worker.error(f"No testcases were found while using filter: {filter_set}. Request response: "
                                 f"{automation_asset_info}")

    # TODO - Append html reporter script
    testcases_list.append(reporter_test_path)

    # '''Preparing the Zephyr Cycle - identifying or creating a new one'''
    # '''Get Jira Project ID and Version - needed for Zephyr actions '''
    # jira_project_id = __jira_get_project_id(session=jira_session, project_key=jira_project_key)
    # jira_project_version_id = __jira_get_project_version_id(session=jira_session, project_key=jira_project_key,
    #                                                         jira_project_version_name=jira_project_version_name)
    # if jira_project_id == 0 or jira_project_version_id == 0:
    #     log_worker.error(
    #         f"Failed to identify IDs for project {jira_project_key} with Version name {jira_project_version_name}")
    #     return {"ok": False}
    #
    # ''' Create Zephyr Test Cycle if needed '''
    # if zephyr_create_cycle_flag:
    #     zephyr_cycle_id = __zephyr_create_cycle(session=zephyr_session, project_id=jira_project_id,
    #                                             project_version=jira_project_version_id,
    #                                             cycle_name=zephyr_test_cycle_name, build=zephyr_build,
    #                                             test_keys_to_include=keys_list)
    # else:
    #     zephyr_cycle_id = __zephyr_get_cycle_id(session=zephyr_session, project_id=jira_project_id,
    #                                             project_version=jira_project_version_id,
    #                                             cycle_name=zephyr_test_cycle_name)
    # if zephyr_cycle_id == 0:
    #     log_worker.error(f"Failed to identify ID for Test Cycle {zephyr_test_cycle_name}")
    #     return {"ok": False}

    # TODO - Add runlist argument with Test Cycle ID, so that it can be picked up by the Monitor script later on.
    # Try to get the Test Cycle name from a request on the first reportId (as the first reportId is the one creating the Test Cycle)
    # Nx how many arguments we want to add to the runlist (one of them will be Test Cycle ID)
    # runlist["general"]["parameters"].append({'description': '', 'masked': False, 'name': 'zephyr_cycle_id', 'type': 'TEXT','value': '1231321'})
    # TODO - Add all parameters from the initial script to the newly created runlist

    '''Post runlist execution'''
    log_worker.info(f"Creating runlist execution using testcase list: {testcases_list}")

    '''
    HARDCODED stuff
    '''
    zephyr_cycle_id = "123"

    runlist_execution_id = velocity_session.post_runlist_execution(testcase_paths=testcases_list,
                                                                   detail_level="ALL_ISSUES_ALL_STEPS",
                                                                   terminate_on_item_fail=False,
                                                                   execution_name=execution_name,
                                                                   topology_id=topology_id)
                                                                   # zephyr_cycle_id=zephyr_cycle_id)

    if runlist_execution_id:
        log_worker.info(f"Runlist execution ID is: {runlist_execution_id}")
        return {"ok": True}
    else:
        log_worker.error("Failed to create runlist execution, exiting script execution.")
        log_worker.error(f"Finished: FAILED")
        return {"ok": False}


def main():
    """Main procedure"""

    '''Initializing arguments'''
    jira_project_key = ""
    jira_project_release_name = ""
    zephyr_test_cycle_name = ""
    story_key_for_comment = ""
    zephyr_build = ""
    runlist_name = ""
    topology_name = ""

    for i in range(1, len(sys.argv[1:]), 2):
        log_worker.info(f"Argument: {sys.argv[i]}")
        log_worker.info(f"Value: {sys.argv[i + 1]}")
        if sys.argv[i] == "--jira_project_key":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            jira_project_key = sys.argv[i + 1]
        elif sys.argv[i] == "--jira_project_release_name":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            jira_project_release_name = sys.argv[i + 1]
        elif sys.argv[i] == "--zephyr_test_cycle_name":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            zephyr_test_cycle_name = sys.argv[i + 1]
        elif sys.argv[i] == "--keys_list":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            zephyr_build = sys.argv[i + 1]
        elif sys.argv[i] == "--story_key_for_comment":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            story_key_for_comment = sys.argv[i + 1]
        elif sys.argv[i] == "--zephyr_build":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            zephyr_build = sys.argv[i + 1]
        elif sys.argv[i] == "--runlist_name":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            runlist_name = sys.argv[i + 1]
        elif sys.argv[i] == "--topology_name":
            log_worker.info(f"Value for {sys.argv[i]} is {sys.argv[i + 1]}.")
            topology_name = sys.argv[i + 1]
        else:
            log_worker.warning(f"Argument {sys.argv[i]} is not recognized and will not be used.")

    if jira_project_key == "":
        log_worker.error(f"Argument jira_project_key is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if jira_project_release_name == "":
        log_worker.error(f"Argument jira_project_release_name is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if zephyr_test_cycle_name == "":
        log_worker.error(f"Argument zephyr_test_cycle_name is empty, exiting execution. Set as N/A if runlist_name is "
                         f"provided.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if story_key_for_comment == "":
        log_worker.error(f"Argument story_key_for_comment is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if zephyr_build == "":
        log_worker.error(f"Argument zephyr_build is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if runlist_name == "":
        log_worker.error(f"Argument runlist_name is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)
    if topology_name == "":
        log_worker.error(f"Argument topology_name is empty, exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)

    '''Open Sessions'''
    ''' - Velocity'''
    velocity = VELOCITYPARAMS['host']
    velo_user = VELOCITYPARAMS['user']
    velo_password = VELOCITYPARAMS['pass']

    velocity_session = Velocity.API(velocity, velo_user, velo_password)

    # ''' - Jira'''
    # jira_service_name = JIRAPARAMS['service_name_velo']
    # properties_list = ['ipAddress', 'username', 'password']
    # properties_jira = velocity_session.get_resource_property_value(jira_service_name, properties_list)
    # if not properties_jira:
    #     log_worker.error(f"Failed to extract JIRA service information from Velocity")
    #     sys.exit(0)
    # try:
    #     log_worker.info(
    #         f'Opening Jira session on {properties_jira["ipAddress"]} with user {properties_jira["username"]}')
    #     jira_session = JiraCore(properties_jira["ipAddress"], properties_jira["username"], properties_jira["password"])
    # except Exception as e:
    #     log_worker.error(f"Failed to open JIRA sessions\n {e}")
    #     sys.exit(0)
    #
    # ''' - Zephyr'''
    # log_worker.info(f'Opening Zephyr session on {properties_jira["ipAddress"]} with user {properties_jira["username"]}')
    # zephyr_session = ZephyrCore(properties_jira["ipAddress"], properties_jira["username"], properties_jira["password"])
    # if not zephyr_session.login():
    #     log_worker.error("Failed to open Zephyr sessions")
    #     sys.exit(0)
    #
    # '''Retrieve the topology ID'''
    # if topology_name != "N/A":
    #     topology_id = velocity_session.get_topology_id_by_name(topology_name)
    # else:
    #     topology_id = ""
    #
    # '''Retrieve the keys for the specified cycle name'''
    # if runlist_name == "N/A":
    #     test_keys = zephyr_get_test_keys_from_cycle(jira_project_key=jira_project_key,
    #                                                 jira_project_version_name=jira_project_release_name,
    #                                                 zephyr_test_cycle_name=zephyr_test_cycle_name,
    #                                                 jira_session=jira_session, zephyr_session=zephyr_session)
    #
    # else:
    #     test_keys = {"ok": runlist_name, "test_cycle_id": None, "test_keys_list": None}

    '''
    Hardcoded stuff
    '''
    test_keys = {"ok": runlist_name, "test_cycle_id": "Test_Cycle_Id", "test_keys_list": ["airtel_pass","airtel_fail","airtel_pass","airtel_fail"]}
    # Case 2: runlist_name = "New_Runlist"
    topology_id = "77b5d525-f9ce-4c70-81de-8141200ed5f0"
    jira_session = "N/A"
    zephyr_session = "N/A"
    '''
    Hardcoded stuff END
    '''
    if test_keys["ok"]:
        deploy_runlist_response = deploy_runlist_execution(cycle_id=test_keys["test_cycle_id"],
                                                           keys_list=test_keys["test_keys_list"],
                                                           jira_project_key=jira_project_key,
                                                           jira_project_version_name=jira_project_release_name,
                                                           zephyr_test_cycle_name=zephyr_test_cycle_name,
                                                           zephyr_build=zephyr_build,
                                                           runlist_name=runlist_name,
                                                           velocity_session=velocity_session,
                                                           topology_id=topology_id,
                                                           jira_session=jira_session,
                                                           zephyr_session=zephyr_session)
        if not deploy_runlist_response["ok"]:
            log_worker.error(f"Runlist could not be started. Exiting execution.")
            log_worker.error(f"Finished: FAILED")
            sys.exit(0)
    else:
        log_worker.error(f"Test keys could not be obtained. Response: {test_keys}."
                         f" Exiting execution.")
        log_worker.error(f"Finished: FAILED")
        sys.exit(0)


if __name__ == "__main__":
    main()
