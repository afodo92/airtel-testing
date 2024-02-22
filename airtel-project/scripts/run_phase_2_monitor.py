import json
import os
import sys
import time

# sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import helpers.Logger as Local_logger
import libs.libs_velocity.Velocity as Velocity
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import Jira as JIRAPARAMS
from parameters.global_parameters import Velocity as VELOCITYPARAMS


# from datetime import datetime
# from libs.libs_html_reporting.HTMLReportCore import HTMLGenerator
# from libs.libs_jira.JiraCore import JiraCore
# from libs.libs_zephyr.ZephyrCore import ZephyrCore

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_run_zephyr_automation_cycle.txt")


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

    # TODO: Update the list of needed parameters and also include zephyr_cycle_key
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-zephyr_test_cycle_id', required=True, dest="ZEPHYR_TEST_CYCLE_ID")
    # zephyr_test_cycle_id = parser.parse_known_args()[0].ZEPHYR_TEST_CYCLE_ID


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

    velocity = VELOCITYPARAMS['host']
    velo_user = VELOCITYPARAMS['user']
    velo_password = VELOCITYPARAMS['pass']
    '''Open Velocity Session'''
    velocity_session = Velocity.API(velocity, velo_user, velo_password)

    # TODO: Investigate and decide how to pass the input parameters from above
    # Change to argparse

    # TODO: Extract runlist ID for the runlist running this monitor script
    monitor_report_id = os.environ['VELOCITY_PARAM_REPORT_ID']
    monitor_execution_report = velocity_session.get_execution_id(monitor_report_id)
    monitor_runlist_item_number = monitor_execution_report["runlistItemId"]
    runlist_guid = monitor_execution_report["runlistGuid"]

    # TODO: Extract Test Cycle ID
    # We will extract it from the RunList arguments (it will be added as an RunList argument when the RunList is created)

    # TODO: Identify the previously executed script

    runlist_summary = velocity_session.get_runlist_execution(runlist_guid)[0]["executions"]
    test_case_summary = [i for i in runlist_summary if i["runlistItemId"] == str(int(monitor_runlist_item_number) - 1)]
    test_case_report_id = test_case_summary[0]["executionID"]
    test_case_result = test_case_summary[0]["result"]
    print('Report Id for previous test: ', test_case_report_id)
    print('Result for previons test: ', test_case_result)

    # TODO: Identify the result for the previously exected script
    # TODO: If test result is failed, open Jira defect ID
    # failure_reason = execution_id_response["failureReason"]
    # if failure_reason is None:
    #     failure_reason = velocity_session.get_execution_failure_reason(testcase_execution_id)
    #     temp_results[tag]["failure_reason"] = failure_reason
    # else:
    #     temp_results[tag]["failure_reason"] = failure_reason
    # processed.append(testcase)
    # if failure_reason:
    #     log_worker.info(f"Execution of {automation_results_data[tag]['test_name']} failed, opening "
    #                     f"Jira issue.")
    #     failure_reason = failure_reason.replace('"', '')
    #     open_defect = jira.open_defect(jira_project_key, summary=f"{temp_results[tag]['test_name']}"
    #                                                              f" has failed.",
    #                                    description="Link to the Velocity execution report: " + temp_results[tag][
    #                                        "execution_link"])
    #     if open_defect is not False:
    #         log_worker.info(f"Jira issue {open_defect} has been opened.")
    #         link_result = jira.link_item(open_defect, story_key_for_comment, "relates")
    #         if link_result is not False:
    #             log_worker.info(
    #                 f"Jira issue {open_defect} has been linked to {story_key_for_comment}.")
    #         else:
    #             log_worker.error(
    #                 f"Failed to link Jira issue {open_defect} to {story_key_for_comment}.")
    #     else:
    #         log_worker.error(f"Failed to open Jira issue.")

    # TODO: Update Zephyr result for the test with specific Tag and result from above




if __name__ == "__main__":
    main()
