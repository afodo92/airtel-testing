from parameters.global_parameters import Jira as JIRAPARAMS
from libs.libs_zephyr.ZephyrCore import ZephyrCore

if __name__ =="__main__":
    execution_id_to_update = None

    zephyr = ZephyrCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    print(zephyr.login())

    ''' GET Cycles from the JIRA Project and print Cycle information '''
    # print(zephyr.get_cycles(project_id=17404,project_version=16719))
    print(zephyr.get_cycles(project_id=17404,project_version=-1))

    # print(zephyr.get_cycle_information_by_id(cycle_id=14188))

    ''' UPDATE Cycles and print Cycle information '''
    # print(zephyr.update_cycle_information_by_id(cycle_id=13807,name="Rel 1 updated cycle",build="1.1.updated"))
    # print(zephyr.get_cycle_information_by_id(cycle_id=13807))

    ''' GET Test Executions, identify the one from the Cycle that we want, change Execution status and print Execution details '''

    # test_executions = zephyr.get_test_executions_by_test_key("VELO-3")
    # for execution in test_executions["executions"]:
    #     if execution["execution"]["testCycle"] == "auto_cycle_1":
    #         execution_id_to_update = execution["execution"]["id"]
    # print(execution_id_to_update)
    #
    # print(zephyr.update_test_execution_status_by_id(execution_id=execution_id_to_update,execution_status="pass"))
    # print(zephyr.get_test_executions_by_test_key("VELO-3"))

    ''' Create Cycle '''
    # print(zephyr.create_cycle(name="auto_cycle_1",project_id=17404,project_version=16719,build="10.1.1",environment="Airtel",description="automation test"))

    ''' Add Folder to Cycle and verify Folders information '''
    # print(zephyr.add_folder_to_cycle(name="auto_folder_1",project_id=17404,project_version=16719,cycle_id=14188))
    # print(zephyr.get_cycle_folders_information_by_id(cycle_id=14188,project_id=17404,project_version=16719))

    ''' Delete Folder from Cycle and verify Folders information '''
    # print(zephyr.delete_folder_from_cycle(folder_id=9917,cycle_id=14188,project_id=17404,project_version=16719))
    # print(zephyr.get_job_progress_by_token(job_progress_token="0001646835701833-5056b645f8-0001"))
    # print(zephyr.get_cycle_folders_information_by_id(cycle_id=14188,project_id=17404,project_version=16719))

    ''' Add Tests to Cycle '''
    # print(zephyr.add_tests_to_cycle_by_key_list(test_key_list=["VELO-3"],project_id=17404,project_version=16719,cycle_id=14188,folder_id=9917))
    # print(zephyr.get_job_progress_by_token(job_progress_token="0001646903921438-5056b645f8-0001"))

    ''' Get Execitons based on Zephyr IDs'''
    # print(zephyr.get_test_executions_by_zephyr_ids(project_id=17404,project_version=16719,cycle_id=14188,folder_id=9917))