import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import libs.libs_velocity.Velocity as Velocity
from parameters.global_parameters import Velocity as VELOCITYPARAMS


def main():
    velocity = VELOCITYPARAMS['host']
    veloUser = VELOCITYPARAMS['user']
    veloPassword = VELOCITYPARAMS['pass']

    velocity = "vel-5gc-qa.spirenteng.com"
    veloUser = "spirent"
    veloPassword = "spirent"

    velocitySession = Velocity.API(velocity, veloUser, veloPassword)

    '''Get all matching scripts by list of tags'''
    tag_list = ['H-2TS', 'P-4TS', 'T-2TS']
    # tag_list = ['VELO-3', 'VELO-5', 'VELO-5']
    automation_results_data = {}
    testcases_list = []
    testcase_stats = {}
    for tag in tag_list:
        filter_set = {"tags": [tag]}
        automation_assets = velocitySession.get_automation_assets(filters=filter_set)
        if len(automation_assets["content"]) != 1:
            automation_results_data[tag] = {}
            automation_results_data[tag]["test_name"] = automation_assets["content"][0]["name"]
            testcases_list.append(automation_assets["content"][0]["fullPath"])
            testcase_stats[automation_assets["content"][0]["fullPath"]] = {}

    '''Post runlist execution'''
    execution_name = "Test cycle name"
    # list_of_paths = velocitySession.extract_testcase_paths(testcases_list)
    runlist_execution_id = velocitySession.post_runlist_execution(testcase_paths=testcases_list,
                                                                  detail_level="ALL_ISSUES_ERROR_STEPS",
                                                                  terminate_on_item_fail=False,
                                                                  execution_name=execution_name)

    '''Monitor runlist execution'''
    is_finished = 0
    not_processed = testcases_list
    while not_processed:
        processed = []
        temp_results = {}
        execution_status = velocitySession.get_runlist_execution(runlist_execution_id)
        execution_status = json.loads(execution_status)[0]
        if len(execution_status["executions"]) > 0:
            for testcase in not_processed:
                test_index = ''
                try:
                    test_index = [i for i in range(0, len(execution_status["executions"])) if testcase == execution_status["executions"][i]["testPath"]][0]
                except Exception as e:
                    if e == "list index out of range":
                        pass
                if test_index != '':
                    if execution_status["executions"][test_index]["executionState"] in ["COMPLETED", "START_FAILED", "ABORTED",
                                                                                                    "AGENT_NOT_RESPONDING"]:
                        for tag in automation_results_data.keys():
                            if automation_results_data[tag]["test_name"] in testcase:
                                break
                        temp_results[tag] = {}
                        temp_results[tag]["test_name"] = automation_results_data[tag]["test_name"]
                        temp_results[tag]["result"] = execution_status["executions"][test_index]["result"]
                        testcase_execution_id = execution_status['executions'][test_index]['executionID']
                        temp_results[tag]["execution_link"] = f"https://{velocity}/ito/executions/v1/executions/{testcase_execution_id}"
                        execution_id_response = json.loads(velocitySession.get_execution_id(testcase_execution_id))
                        failure_reason = execution_id_response["failureReason"]
                        if failure_reason is None:
                               failure_reason = velocitySession.get_execution_failure_reason(testcase_execution_id)
                               temp_results[tag]["failure_reason"] = failure_reason
                        else:
                            temp_results[tag]["failure_reason"] = failure_reason
                        processed.append(testcase)
            for testcase in processed:
                not_processed.remove(testcase)
        if(temp_results != {}):
            temp_results["runlist_execution_link"] = f"https://{velocity}/ito/executions/v1/executions/{execution_status['guid']}"
            print(temp_results)

if __name__ == "__main__":
    main()
