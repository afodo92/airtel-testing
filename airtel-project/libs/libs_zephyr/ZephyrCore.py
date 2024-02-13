#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Cosmin-Florin Stanuica
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used to enable communication with Zephyr Service """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import base64
import sys
from parameters.global_parameters import Reporting as REPORTINGPARAMS
import helpers.Logger as Local_logger
from helpers.RequestsWrapper import APISession

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], "zephyr_core_log.txt")


class ZephyrCore(object):
    def __init__(self, server, username, password, repeat_step=1):
        this_method_name = sys._getframe().f_code.co_name
        self.this_class_name = self.__class__.__name__
        server = "https://" + server.lower().replace("https://", "").replace("http://", "")
        self.base_url = server + "/rest/zapi/latest/"
        self.username = username
        self.password = password
        self.api_session = None
        self.user_token = None
        self.repeat_step = repeat_step
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Opened session to server {server}")

    def login(self):
        """ Method used to create the Authorization Token and Provision the API session with all needed headers.
        :return: Boolean True or False
        LOCALLY STORES: user_token
        """
        this_method_name = sys._getframe().f_code.co_name
        self.user_token = None

        try:
            credentials_data = self.username + ":" + self.password
            self.user_token = str(base64.b64encode(credentials_data.encode("ascii")), "utf-8")
            log_worker.info(
                f"{self.this_class_name} - {this_method_name} - Converted credentials {self.username}:provided_pssword "
                f"to base64.")
        except Exception as err:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - Could not convert credentials to base64 {err}.")
            return False

        self.api_session = APISession(repeat_step=self.repeat_step)
        self.api_session.headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + self.user_token}
        return True

    def get_cycles(self, project_id, project_version):
        """ Method used to get all cycles information.
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :return: False or Cycles information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get cycles information.")

        url = self.base_url + f"cycle?projectId={project_id}&versionId={project_version}"
        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Cycles information")

    def get_cycle_information_by_id(self, cycle_id):
        """ Method used to get Cycle information for specific cycle, identified by id.
        :param cycle_id: (obtain it using get_cycles)
        :return: False or Cycle information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to get cycle information for cycle with id "
            f"{cycle_id}")

        url = self.base_url + f"cycle/{str(cycle_id)}"
        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Cycles information by ID")

    def get_cycle_folders_information_by_id(self, cycle_id, project_id, project_version, limit=100, offset=0):
        """ Method used to get Cycle information for specific cycle, identified by id.
        :param cycle_id: (obtain it using get_cycles)
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param limit: (integer)
        :param offset: (integer)
        :return: False or List of Folders information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to get cycle folders information for cycle with id "
            f"{cycle_id}")

        url = self.base_url + f"cycle/{str(cycle_id)}/folders?projectId={project_id}&versionId={project_version}" \
                              f"&limit={limit}&offset={offset}"
        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Cycle folders information")

    def create_cycle(self, name, project_id, project_version, cloned_cycle_id=None, build=None, environment=None,
                     description=None, start_date=None, end_date=None):
        """ Method used to create Cycle.
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param cloned_cycle_id: (obtain it using get_cycles)
        :param name: (name to be added to the cycle information)
        :param build: (build to be added to the cycle information)
        :param environment: (environment to be added to the cycle information)
        :param description: (description to be added to the cycle information)
        :param start_date: (start date to be added to the cycle information - format 8/Aug/13
        :param end_date: (end date to be added to the cycle information - format 8/Aug/13
        :return: False or Cycle information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to create cycle {name}.")

        url = self.base_url + f"cycle"

        json_message_body = {"name": name, "projectId": project_id, "versionId": project_version}
        if cloned_cycle_id is not None:
            json_message_body["clonedCycleId"] = cloned_cycle_id
        if build is not None:
            json_message_body["build"] = build
        if environment is not None:
            json_message_body["environment"] = environment
        if description is not None:
            json_message_body["description"] = description
        if start_date is not None:
            json_message_body["startDate"] = start_date
        if end_date is not None:
            json_message_body["endDate"] = end_date

        return self.api_session.send_request(request_type="post", url=url, json_data=json_message_body,
                                             method_name=this_method_name, log_worker=log_worker,
                                             request_description="Create Cycle")

    def update_cycle_information_by_id(self, cycle_id, name=None, build=None, environment=None, description=None,
                                       start_date=None, end_date=None):
        """ Method used to update Cycle information for specific cycle, identified by id.
        :param cycle_id: (obtain it using get_cycles)
        :param name: (new name to be added to the cycle information)
        :param build: (new build to be added to the cycle information)
        :param environment: (new environment to be added to the cycle information)
        :param description: (new description to be added to the cycle information)
        :param start_date: (new start date to be added to the cycle information - format 8/Aug/13
        :param end_date: (new end date to be added to the cycle information - format 8/Aug/13
        :return: False or Cycle information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to update cycle information account for cycle with "
            f"id {cycle_id}.")
        url = self.base_url + f"cycle"

        json_message_body = {"id": str(cycle_id)}
        if name is not None:
            json_message_body["name"] = name
        if build is not None:
            json_message_body["build"] = build
        if environment is not None:
            json_message_body["environment"] = environment
        if description is not None:
            json_message_body["description"] = description
        if start_date is not None:
            json_message_body["startDate"] = start_date
        if end_date is not None:
            json_message_body["endDate"] = end_date

        return self.api_session.send_request(request_type="put", url=url, json_data=json_message_body,
                                             method_name=this_method_name, log_worker=log_worker,
                                             request_description="Update Cycle")

    def add_folder_to_cycle(self, name, project_id, project_version, cycle_id, cloned_folder_id=None, description=None):
        """ Method used to create Cycle.
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param name: (folder name)
        :param cycle_id: (obtain it using get_cycles)
        :param cloned_folder_id: (obtain it using get get_cycle_folders_information_by_id)
        :param description: (description to be added to the folder information)
        :return: False or Folder information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to add folder {name} to cycle {cycle_id}.")
        url = self.base_url + f"folder/create"

        json_message_body = {"name": name, "projectId": project_id, "versionId": project_version, "cycleId": cycle_id}
        if description is not None:
            json_message_body["description"] = description
        if cloned_folder_id is not None:
            json_message_body["clonedFolderId"] = cloned_folder_id

        return self.api_session.send_request(request_type="post", url=url, json_data=json_message_body,
                                             method_name=this_method_name, log_worker=log_worker,
                                             request_description="Add Folder to Cycle")

    def delete_folder_from_cycle(self, folder_id, project_id, project_version, cycle_id):
        """ Method used to create Cycle.
        :param folder_id: (obtain it using get_cycle_folders_information_by_id)
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param cycle_id: (obtain it using get_cycles)
        :return: False or Folder information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to delete folder with id {folder_id} from cycle "
            f"{cycle_id}.")
        url = self.base_url + f"folder/{folder_id}?projectId={project_id}&versionId={project_version}" \
                              f"&cycleId={cycle_id}"

        return self.api_session.send_request(request_type="delete", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Remove Folder from Cycle")

    def add_tests_to_cycle_by_key_list(self, test_key_list, project_id, project_version, cycle_id, folder_id=None):
        """ Method used to create Cycle.
        :param test_key_list: (Jira Key List - ['VELO-5', ... ,'VELO-100'])
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param cycle_id: (obtain it using get_cycles)
        :param folder_id: (obtain it using get get_cycle_folders_information_by_id)
        :return: False or Test information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to add tests {test_key_list} to cycle {cycle_id}.")
        url = self.base_url + f"execution/addTestsToCycle"

        json_message_body = {"method": "1", "issues": test_key_list, "projectId": project_id,
                             "versionId": project_version, "cycleId": cycle_id, "assigneeType": None}
        if folder_id is not None:
            json_message_body["folderId"] = folder_id

        return self.api_session.send_request(request_type="post", url=url, json_data=json_message_body,
                                             method_name=this_method_name, log_worker=log_worker,
                                             request_description="Add Tests to Cycle")

    def get_test_executions_by_test_key(self, test_key):
        """ Method used to get Test Execution information for specific test, identified by the Jira Key.
        :param test_key: (Jira Key - VELO-5)
        :return: False or Test Execution information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to get test execution information for test with "
            f"key {test_key}")

        url = self.base_url + f"traceability/executionsByTest?testIdOrKey={str(test_key)}"
        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Test Execution information")

    def get_test_executions_by_zephyr_ids(self, issue_id=None, project_id=None, project_version=None, cycle_id=None,
                                          folder_id=None, limit=1000, offset=0):
        """ Method used to get Test Execution information from project, cycle, folder or based on issue_id.
        :param issue_id: (Obtain it using Jira API get_item_details starting from Jira Key - VELO-5)
        :param project_id: (obtain it using Jira API starting from the Project key)
        :param project_version: (obtain it using Jira API starting from the Project key)
        :param cycle_id: (obtain it using get_cycles)
        :param folder_id: (obtain it using get get_cycle_folders_information_by_id)
        :param limit: (integer)
        :param offset: (integer)
        :return: False or Test Execution information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to get test execution information based on "
            f"Zephyr IDs")

        url = self.base_url + f"execution?"
        need_and = 0

        if issue_id:
            url = url + f"issueId={issue_id}"
            need_and = 1
        if project_id:
            url = url + ("&" if need_and else "") + f"projectId={project_id}"
            need_and = 1
        if project_version:
            url = url + ("&" if need_and else "") + f"versionId={project_version}"
            need_and = 1
        if cycle_id:
            url = url + ("&" if need_and else "") + f"cycleId={cycle_id}"
            need_and = 1
        if folder_id:
            url = url + ("&" if need_and else "") + f"folderId={folder_id}"
            need_and = 1
        if limit:
            url = url + ("&" if need_and else "") + f"limit={limit}"
            need_and = 1
        if offset:
            url = url + ("&" if need_and else "") + f"offset={offset}"
            need_and = 1

        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Test Execution information")

    def update_test_execution_status_by_id(self, execution_id, execution_status):
        """ Method used to update Test Execution status for an execution identified by id.
        :param execution_id: (obtain it using get_test_executions_by_ methods)
        :param execution_status: (supporting: "unexecuted", "pass", "fail", "wip", "blocked")
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        execution_status = execution_status.lower()
        status_mapping = {"unexecuted": "-1", "pass": "1", "fail": "2", "wip": "3", "blocked": "4"}
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - Trying to update execution status for execution with "
            f"id {execution_id}.")

        if execution_status in ["abort", "cancel", "error"]:
            execution_status = "blocked"

        if execution_status not in ["unexecuted", "pass", "fail", "wip", "blocked"]:
            log_worker.warning(
                f"{self.this_class_name} - {this_method_name} - Status {execution_status} is not supported. "
                f"Use one of: \"unexecuted\", \"pass\", \"fail\", \"wip\", \"blocked\" .")
            return False

        url = self.base_url + f"execution/{execution_id}/execute"
        json_message_body = {"status": status_mapping[execution_status]}
        return self.api_session.send_request(request_type="put", url=url, json_data=json_message_body,
                                             method_name=this_method_name, log_worker=log_worker,
                                             request_description="Test Execution Update")

    def get_job_progress_by_token(self, job_progress_token):
        """ Method used to get all cycles information.
        :param job_progress_token: (obtain it using delete methods)
        :return: False or Job Execution information in JSON format
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(f"{self.this_class_name} - {this_method_name} - Trying to get job execution information.")

        url = self.base_url + f"execution/jobProgress/{job_progress_token}"
        return self.api_session.send_request(request_type="get", url=url, method_name=this_method_name,
                                             log_worker=log_worker, request_description="Job Execution information")
