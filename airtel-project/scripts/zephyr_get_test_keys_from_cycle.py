from parameters.global_parameters import Jira as JIRAPARAMS
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from libs.libs_zephyr.ZephyrCore import ZephyrCore
from libs.libs_jira.JiraCore import JiraCore
import helpers.Logger as Local_logger


log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"], REPORTINGPARAMS["session_log_path"], "s_zephyr_get_test_keys_from_cycle.txt")

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
        log_worker.info(f"Identified Jira Project Version ID for project {project_key} with version name {jira_project_version_name}")
        return -1

    j_project_details = session.get_project_details(project_key=project_key)
    if "versions" not in j_project_details.keys():
        log_worker.error("Failed to get Jira Project Version")
        return 0
    for version in j_project_details["versions"]:
            if "name" not in version.keys() or "id" not in version.keys():
                continue
            if version["name"] == jira_project_version_name:
                log_worker.info(f"Identified Jira Project Version ID for project {project_key} with version name {jira_project_version_name}")
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
    z_folders_details = session.get_cycle_folders_information_by_id(project_id=project_id, project_version=project_version, cycle_id=cycle_id)
    zephyr_folder_ids = get_folder_ids(z_folders_details)

    ''' Get Zephyr Executions included DIRECTLY in the Test Cycle '''
    z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version, cycle_id=cycle_id)
    if not z_executions:
        log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id}")
    else:
        test_keys_list += get_executions_test_keys(z_executions)

    ''' Get Zephyr Executions included in the Test Cycle Folders '''
    for folder_id in zephyr_folder_ids:
        z_executions = session.get_test_executions_by_zephyr_ids(project_id=project_id, project_version=project_version, cycle_id=cycle_id, folder_id=folder_id)
        if not z_executions:
            log_worker.error(f"Failed to get executions under Test Cycle with ID {cycle_id} folder {folder_id}")
        else:
            test_keys_list += get_executions_test_keys(z_executions)

    return test_keys_list


def zephyr_get_test_keys_from_cycle(jira_project_key, jira_project_version_name, zephyr_test_cycle_name):
    ''' Initialize variables'''
    jira_project_id = 0
    jira_project_version_id = 0
    zephyr_cycle_id = 0
    test_keys_list = []
    return_data = {"ok": False, "test_cycle_id": 0, "test_keys_list": []}

    ''' Open Sessions '''
    jira = JiraCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    zephyr = ZephyrCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    if not zephyr.login():
        log_worker.error("Failed to open sessions")
        return return_data

    ''' Get Jira Project ID and Version - needed for Zephyr actions '''
    jira_project_id = __jira_get_project_id(session=jira,project_key=jira_project_key)
    jira_project_version_id = __jira_get_project_version_id(session=jira, project_key=jira_project_key,jira_project_version_name=jira_project_version_name)
    if jira_project_id == 0 or jira_project_version_id == 0:
        log_worker.error(f"Failed to identify IDs for project {jira_project_key} with Version name {jira_project_version_name}")
        return return_data

    ''' Get Zephyr Cycle ID '''
    zephyr_cycle_id = __zephyr_get_cycle_id(session=zephyr, project_id= jira_project_id, project_version= jira_project_version_id, cycle_name= zephyr_test_cycle_name)
    if zephyr_cycle_id == 0:
        log_worker.error(f"Failed to identify ID for Test Cycle {zephyr_test_cycle_name}")
        return return_data

    ''' Get Test Keys included in the Zephyr Test Cycle '''
    return_data["ok"] = True
    return_data["test_cycle_id"] = zephyr_cycle_id
    return_data["test_keys_list"] = __zephyr_get_all_cycle_test_keys(session=zephyr, project_id= jira_project_id, project_version= jira_project_version_id, cycle_id= zephyr_cycle_id)

    ''' Return the data'''
    return return_data

# --jira_project_key "VELO" --jira_project_version_name "unscheduled" --zephyr_test_cycle_name "manual_cycle_1"
print(zephyr_get_test_keys_from_cycle(jira_project_key="VELO", jira_project_version_name="unscheduled", zephyr_test_cycle_name="auto_cycle_3"))