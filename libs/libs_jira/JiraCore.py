#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Cosmin-Florin Stanuica
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used to enable communication with Jira Service """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from jira import JIRA
import helpers.Logger as Local_logger
from parameters.global_parameters import Reporting as REPORTINGPARAMS
import sys

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], "jira_core_log.txt")


class JiraCore(object):
    def __init__(self, server, username, password):
        self.this_class_name = self.__class__.__name__
        this_method_name = sys._getframe().f_code.co_name
        server = "https://" + server.lower().replace("https://", "")

        self.jira = JIRA(basic_auth=(username, password), options={"server": server})
        log_worker.info(f"{self.this_class_name} - {this_method_name} - Opened session to server {server}")

    def get_item_details(self, item_key):
        """ Method used to extract Jira Item details based on item key
        :param item_key: Jira Item Key
        :return: item_raw data
        """
        this_method_name = sys._getframe().f_code.co_name

        try:
            item_details = self.jira.issue(item_key).raw
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Extracted item details for item {item_key}")

            return item_details
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred during getting "
                             f"{item_key} item details\nException: {e}")
            return False

    def add_comment(self, item_key, content):
        """ Method used to add comment to a Jira item
        :param item_key: Jira Item Key
        :param content: Comment body, or content
        :return: False or comment
        """
        this_method_name = sys._getframe().f_code.co_name

        try:
            comment = self.jira.add_comment(item_key, content)
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Added Comment to {item_key} item")
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred during adding comment "
                             f"to {item_key} item\nException: {e}")
            return False

        return comment

    def change_state(self, item_key, new_state=False):
        """Method used to change Jira item status
        IDs for changing status
            Backlog - 11
            Selected for Development - 21
            In Progress - 31
            Done - 41
            Under Review - 51
        :param item_key: Jira Item Key
        :param new_state: New Jira state
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        state_mapping = {"backlog": "11",
                         "selected for development": "21",
                         "in progress": "31",
                         "done": "41",
                         "under review": "51"}

        if new_state:
            if new_state not in state_mapping.keys():
                log_worker.error(f"{self.this_class_name} - {this_method_name} - State {new_state} was not understood. "
                                 f"Cannot change {item_key} item status")
                return False

            try:
                self.jira.transition_issue(item_key, state_mapping[new_state])
                log_worker.info(f"{self.this_class_name} - {this_method_name} - Changed state for {item_key} item")

            except Exception as e:
                log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred during the "
                                 f"transition of {item_key} item\nException: {e}")
                return False

        return True

    def attach_file(self, item_key, file_path):
        """ Method used to attach file to Jira item
        :param item_key: Jira Item Key
        :param file_path: Path to the file to be uploaded
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        try:
            issue = self.jira.issue(item_key)
        except Exception as e:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - Exception occurred while trying to get issue with key "
                f"{item_key}\nException: {e}")

        try:
            with open(file_path, 'rb') as upload_file:
                try:
                    self.jira.add_attachment(issue=issue, attachment=upload_file)
                except Exception as e:
                    log_worker.error(
                        f"{self.this_class_name} - {this_method_name} - Exception occurred while uploading attachment "
                        f"file {file_path} to {item_key}\nException: {e}")
                    return False
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred while opening file "
                             f"{file_path}\nException: {e}")
            return False

        return True

    def open_defect(self, project_key, summary, description, priority_id=3, labels_list=["reported_by_automation"]):
        """ Method used to open Jira defect
        :param project_key: Jira project Key (example: VELO)
        :param summary: Defect summary string
        :param description: Defect description data
        :param priority_id: 1 to 5
        :param labels_list: List of String labels
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Bug'},
            'priority': {'id': str(priority_id)},
            'labels': labels_list
        }

        log_worker.debug(f"Creation Jira issue using the following dictionary: {issue_dict}")
        try:
            new_issue = self.jira.create_issue(fields=issue_dict)
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Opened new Jira item")
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred during creation of "
                             f"Jira ticket\nException: {e}")
            return False
        return new_issue

    def link_item(self, item_key, to_link_item_key, link_type):
        """ Method used to link Jira items to one another using specific relationships
        :param item_key: (Issue to add link to)
        :param to_link_item_key: (Issue to link)
        :param link_type: One of Cloners, Duplicate, Relates
        :return: True or False
        """
        this_method_name = sys._getframe().f_code.co_name

        if link_type.lower() not in ["cloners", "duplicate", "relates"]:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Unsupported Link Type.{link_type}")
            return False

        link_type_to_send = ""
        if link_type.lower() == "cloners":
            link_type_to_send = "Cloners"
        elif link_type.lower() == "duplicate":
            link_type_to_send = "Duplicate"
        elif link_type.lower() == "relates":
            link_type_to_send = "Relates"

        try:
            self.jira.create_issue_link(link_type_to_send, item_key, to_link_item_key)
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Linked {item_key} to {to_link_item_key} "
                            f"using type {link_type_to_send}")
            return True
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Exception occurred when trying to link "
                             f"{item_key} to {to_link_item_key} using type {link_type_to_send}\nException: {e}")
            return False

    def get_project_details(self, project_key):
        """ Method used to get project details
        :param project_key: Jira project key
        :return: False or Project Information json
        """
        this_method_name = sys._getframe().f_code.co_name

        try:
            project_details = self.jira.project(project_key).raw
            log_worker.info(f"{self.this_class_name} - {this_method_name} - Extracted project details for project "
                            f"{project_key}")
            return project_details
        except Exception as e:
            log_worker.error(f"{self.this_class_name} - {this_method_name} - Failed to extract project details \n"
                             f"Exception: {e}")
            return False
