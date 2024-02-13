from parameters.global_parameters import Jira as JIRAPARAMS
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from libs.libs_zephyr.ZephyrCore import ZephyrCore
from libs.libs_jira.JiraCore import JiraCore
import sys
import time
import helpers.Logger as Local_logger


log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"], REPORTINGPARAMS["session_log_path"], "s_zephyr_upload_automation_results.txt")


def __jira_get_project_id(session:JiraCore, project_key):
    j_project_details = session.get_project_details(project_key=project_key)
    if not j_project_details:
        log_worker.error("Failed to get Jira Project details")
        sys.exit(1)
    else:
        if "id" not in j_project_details.keys() or "versions" not in j_project_details.keys():
            log_worker.error("Failed to identify Jira Project ID or Version")
            sys.exit(1)
    log_worker.info(f"Identified Jira Project ID for project {project_key}")
    return j_project_details["id"]


def __jira_get_project_version_id(session:JiraCore, project_key, jira_project_version_name):
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
                return version["id"]
    return 0


def __zephyr_get_cycle_id(session:ZephyrCore, project_id, project_version, cycle_name):
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


def __zephyr_create_cycle(session:ZephyrCore, project_id, project_version, cycle_name, build, test_keys_to_include):
    z_cycle_information = session.create_cycle(name=cycle_name,project_id=project_id,project_version=project_version,build=build)

    if z_cycle_information:
        log_worker.info(f"Created Zephyr cycle {cycle_name}")
        test_cycle_id = z_cycle_information["id"]
        
        zephyr_job_information = session.add_tests_to_cycle_by_key_list(project_id=project_id, project_version=project_version,cycle_id=test_cycle_id,test_key_list=test_keys_to_include)
        if not zephyr_job_information or "jobProgressToken" not in zephyr_job_information.keys():
            log_worker.error("Failed to start job to add tests to the Test Cycle")
            return 0
        else:
            for time_slot in range(60):
                zephyr_job_details = session.get_job_progress_by_token(job_progress_token=zephyr_job_information["jobProgressToken"])
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


def __zephyr_get_all_cycle_test_keys_with_execution_ids(session:ZephyrCore, project_id, project_version, cycle_id):

    def get_folder_ids(z_folders_details):
        folder_ids = []

        if z_folders_details and len(z_folders_details):
            for folder in z_folders_details:
                if "folderId" not in folder:
                    continue
                log_worker.debug(f"Identified Zephyr folder {folder['folderId']}")
                folder_ids.append(folder["folderId"])

        return folder_ids

    def get_executions_test_key_to_id_data(z_executions):
        executions_data = {}
        if "executions" in z_executions.keys():
            for execution in z_executions["executions"]:
                if "issueKey" not in execution.keys() or "id" not in execution.keys():
                    continue
                log_worker.debug(f"Identified Zephyr execution {execution['issueKey']} with ID {execution['id']}")
                executions_data[execution["issueKey"]]=execution["id"]

        return executions_data

    executions_complete_data = {}

    ''' Get Zephyr Folders included in the Test Cycle '''
    z_folders_details = session.get_cycle_folders_information_by_id(project_id=project_id, project_version=project_version, cycle_id=cycle_id)
    zephyr_folder_ids = get_folder_ids(z_folders_details)

    ''' Get Zephyr Executions included DIRECTLY in the Test Cycle '''
    z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version, cycle_id=cycle_id)
    if not z_executions:
        log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id}")
        sys.exit(1)
    else:
        executions_complete_data.update(get_executions_test_key_to_id_data(z_executions))

    ''' Get Zephyr Executions included in the Test Cycle Folders '''
    for folder_id in zephyr_folder_ids:
        z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version, cycle_id=cycle_id, folder_id=folder_id)
        if not z_executions:
            log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id} folder {folder_id}")
            sys.exit(1)
        else:
            executions_complete_data.update(get_executions_test_key_to_id_data(z_executions))

    return executions_complete_data


def __zephyr_update_test_executions(session:ZephyrCore, update_data):
    update_pass = []
    update_fail = []

    for test_key, test_data in update_data.items():
        if test_data["result"] is not None and test_data["execution_id"] is not None:
            z_execution_update_information = session.update_test_execution_status_by_id(execution_id=test_data["execution_id"], execution_status=test_data["result"])
            if z_execution_update_information:
                log_worker.info(f"Updated Zephyr Execution with ID {test_data['execution_id']} and result {test_data['result']}")
                update_pass.append(test_key)
            else:
                log_worker.warning(f"Failed to Update Zephyr Execution with ID {test_data['execution_id']} and result {test_data['result']}")
                update_fail.append(test_key)

    return {"update_pass":update_pass, "update_fail":update_fail}


def __build_update_data(automation_results_data, execution_key_id_data):
    update_data_structure = {}
    for test_key in set(list(automation_results_data.keys()) + list(execution_key_id_data.keys())):
        update_data_structure[test_key] = {}
        if test_key in automation_results_data.keys():
            update_data_structure[test_key]["test_name"] = automation_results_data.get(test_key).get("test_name")
            update_data_structure[test_key]["result"] = automation_results_data.get(test_key).get("result")
        else:
            update_data_structure[test_key]["test_name"] = None
            update_data_structure[test_key]["result"] = None

        if test_key in execution_key_id_data.keys():
            update_data_structure[test_key]["execution_id"] = execution_key_id_data.get(test_key)
        else:
            update_data_structure[test_key]["execution_id"] = None

    return(update_data_structure)


def __jira_add_comment(session:JiraCore, story_key, project_key, project_version_name, cycle_name, runlist_link, update_data, update_pass_list = [], update_fail_list= [], more=None):
    def extract_pass_fail_summary(update_data):
        pass_count = 0
        fail_count = 0
        indeterminate_count = 0
        for test_key, test_data in update_data.items():
            if test_data["result"] is not None and test_data["result"].lower() == "pass":
                pass_count += 1
                continue
            if test_data["result"] is not None and test_data["result"].lower() == "fail":
                fail_count += 1
                continue
            indeterminate_count += 1

        return {"pass": pass_count, "fail": fail_count, "indeterminate": indeterminate_count}

    pass_fail_summary = extract_pass_fail_summary(update_data=update_data)
    test_count_pass = pass_fail_summary["pass"]
    test_count_fail = pass_fail_summary["fail"]
    test_count_indeterminate = pass_fail_summary["indeterminate"]
    test_count_total = test_count_pass + test_count_fail + test_count_indeterminate
    
    comment = f"Test Execution results were added to Jira project: {project_key}, version: {project_version_name} in Zephyr Test Cycle: {cycle_name}\n"
    comment += f"RunList details available here: {runlist_link}\n"
    comment += f"PASS PERCENTAGE: {str(round(float(100 * test_count_pass/test_count_total),2))}% ({test_count_pass} pass, {test_count_fail} fail, {test_count_indeterminate} indeterminate)\n\n"
    comment += f"- Tests for which the result was logged successfully: {', '.join(update_pass_list)}\n"
    comment += f"- Tests for which the result was NOT logged successfully: {', '.join(update_fail_list)}"

    if more and isinstance(more,str):
        comment += f"\n\n{more}"

    return session.add_comment(item_key=story_key,content=comment)


def zephyr_upload_automation_results(automation_results_data, jira_project_key, jira_project_version_name, zephyr_create_cycle_flag, zephyr_test_cycle_name, zephyr_build, story_key_for_comment):
    ''' Initialize variables'''
    jira_project_id = 0
    jira_project_version_id = 0
    zephyr_cycle_id = 0
    execution_key_id_data = {}
    try:
        runlist_link = automation_results_data.pop('runlist_execution_link')
    except:
        runlist_link = "Run List link not Identified"
    automation_test_keys_list = list(automation_results_data.keys())

    ''' Open Sessions '''
    jira = JiraCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    zephyr = ZephyrCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    if not zephyr.login():
        log_worker.error("Failed to open sessions")
        return {"ok": False}
    
    ''' Get Jira Project ID and Version - needed for Zephyr actions '''
    jira_project_id = __jira_get_project_id(session=jira,project_key=jira_project_key)
    jira_project_version_id = __jira_get_project_version_id(session=jira, project_key=jira_project_key,jira_project_version_name=jira_project_version_name)
    if jira_project_id == 0 or jira_project_version_id == 0:
        log_worker.error(f"Failed to identify IDs for project {jira_project_key} with Version name {jira_project_version_name}")
        return {"ok": False}
    
    ''' Create Zephyr Test Cycle if needed '''
    if zephyr_create_cycle_flag:
        zephyr_cycle_id = __zephyr_create_cycle(session=zephyr,project_id=jira_project_id,project_version=jira_project_version_id,cycle_name=zephyr_test_cycle_name,build=zephyr_build, test_keys_to_include=automation_test_keys_list)
    else:
        zephyr_cycle_id = __zephyr_get_cycle_id(session=zephyr, project_id=jira_project_id, project_version=jira_project_version_id, cycle_name=zephyr_test_cycle_name)
    if zephyr_cycle_id == 0:
        log_worker.error(f"Failed to identify ID for Test Cycle {zephyr_test_cycle_name}")
        return {"ok": False}
    #
    ''' Get Zephyr Test Cycle Executions - map IDs to Test Keys '''
    execution_key_id_data = __zephyr_get_all_cycle_test_keys_with_execution_ids(session=zephyr, project_id= jira_project_id, project_version= jira_project_version_id, cycle_id= zephyr_cycle_id)
    if not execution_key_id_data:
        log_worker.error("Failed to map execution Keys to IDs")
        return {"ok": False}
    
    ''' Build Update data by joining automation results to the execution keys, as known by Zephyr'''
    update_data = __build_update_data(automation_results_data=automation_results_data, execution_key_id_data=execution_key_id_data)
    
    ''' Upload execution details for each test to Zephyr Test Cycle '''
    update_result_information = __zephyr_update_test_executions(session=zephyr, update_data=update_data)
    update_pass_list = update_result_information["update_pass"]
    update_fail_list = update_result_information["update_fail"]
    if not update_pass_list and not update_fail_list:
        log_worker.error("Failed to attempt Zephyr Test results update - No successful or failure update")
        return {"ok": False}
    
    ''' Add comment in Jira '''
    if story_key_for_comment:
        comment_result = __jira_add_comment(session=jira,story_key=story_key_for_comment, project_key= jira_project_key,
                                          project_version_name=jira_project_version_name, cycle_name=zephyr_test_cycle_name,
                                          runlist_link= runlist_link, update_data= update_data,
                                          update_pass_list=update_pass_list, update_fail_list=update_fail_list, more="<automated message>")
        if not comment_result:
            log_worker.error(f"Failed to add comment in Jira story {story_key_for_comment}")
            return {"ok": False}
    
    print(jira.get_item_details("VELO-1"))
    return {"ok": True}

''' To Receive as Input from Velo'''
automation_results_data = {
    'VELO-3': {
        'test_name': 'E-5GC-8-PF-UserPlane-vs-Xn-HO-Decoupling.fftc',
        'result': 'PASS',
        'execution_link': 'https://vel-5gc-qa.spirenteng.com/ito/executions/v1/executions/cc83abe2-088e-40cb-82b7-177cbf8bd0f3',
        'failure_reason': "Could not find 'https://vel-5gc-qa.spirenteng.com/ito/repository/v2/repository/spirent/ai_SUT_Library' resource in repository.\nDetails: null"
    },
    'VELO-4': {
        'test_name': 'A-SMF-UPF-3-PF-ControlPlane_vs_UserPlane-Decoupling.fftc',
        'result': 'ERROR',
        'execution_link': 'https://vel-5gc-qa.spirenteng.com/ito/executions/v1/executions/1bafd466-d3d4-419d-9c2e-187bd942bb74',
        'failure_reason': "Could not find 'https://vel-5gc-qa.spirenteng.com/ito/repository/v2/repository/spirent/ai_SUT_Library' resource in repository.\nDetails: null"
    },
    'VELO-5': {
        'test_name': 'I-AMF-38-CO_EpsFallbackOnN26WithREgistrationAndPduSessPrereq.fftc',
        'result': 'FAIL',
        'execution_link': 'https://vel-5gc-qa.spirenteng.com/ito/executions/v1/executions/5484f415-8a54-41bc-8bba-08a558a8150d',
        'failure_reason': 'Parameter TC_parameters/Expected_CPU_Threshold does not exist'
    },
    'runlist_execution_link': 'https://vel-5gc-qa.spirenteng.com/ito/executions/v1/executions/79f44f0e-4acc-4d1f-b13b-9aecc58ad590'
}

# --jira_project_key "VELO" --jira_project_version_name "unscheduled" --zephyr_create_cycle_flag 0 --zephyr_test_cycle_name "auto_cycle_3" --zephyr_build "a.2" --story_key_for_comment "VELO-1"
zephyr_upload_automation_results(automation_results_data=automation_results_data, jira_project_key="VELO",
                                 jira_project_version_name="unscheduled", zephyr_create_cycle_flag=0,
                                 zephyr_test_cycle_name="auto_cycle_3", zephyr_build="a.2",
                                 story_key_for_comment="VELO-1")