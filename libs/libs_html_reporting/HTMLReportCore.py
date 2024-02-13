#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Cosmin-Florin Stanuica
# Created Date: 05.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used to generate HTML Reports """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import jinja2
import os
import sys
from jinja2 import Environment, select_autoescape
import helpers.Logger as Local_logger
from parameters.global_parameters import Reporting as REPORTINGPARAMS

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], "html_reporting_core_log.txt")

env = Environment(
    loader=jinja2.FileSystemLoader('%s/templates/' % os.path.dirname(__file__)),
    autoescape=select_autoescape(['html', 'xml'])
)


class HTMLGenerator:
    def __init__(self, template_name):
        self.this_class_name = self.__class__.__name__
        this_method_name = sys._getframe().f_code.co_name
        self.template = env.get_template(template_name)
        log_worker.info(f"{self.this_class_name} - {this_method_name} - Loaded template {template_name}")

    def airtel_report_generator(self, output_file, test_cycle, build, runlist_link, time_date, pass_fail_summary,
                                results_data, not_run_list):
        """ Method used to create the directory location and render the HTML report based on the provided arguments
         :param output_file: File Path for the output HTML Report
         :param test_cycle: Test Cycle name
         :param build: Build information for the build used at the execution time
         :param runlist_link: Link to the Velocity RunList
         :param time_date: Information on TimeDate associated to the execution
         :param pass_fail_summary: JSON containing number of tests associated with the results (as keys) pass, fail,
                total, indeterminate, not_run
         :param results_data: JSON containing test execution information, where Test Jira Key is the first Key. Each
                execution information is composed of test_name, result, execution_link, failure_reason
         :param not_run_list: List of not executed Test Jira Keys
         :return: item_raw data
        """

        this_method_name = sys._getframe().f_code.co_name
        not_run_list = str(not_run_list)[1:-1]
        if not os.path.exists(os.path.split(output_file)[0]):
            try:
                os.makedirs(os.path.split(output_file)[0])
                log_worker.info(
                    f"{self.this_class_name} - {this_method_name} - Created directory to hold "
                    f"{os.path.split(output_file)[0]} reports")
            except Exception as e:
                log_worker.error(
                    f"{self.this_class_name} - {this_method_name} - Exception occurred while attempting to create "
                    f"folder: {os.path.split(output_file)[0]}\n<{e}>")
                return False
        if len(results_data):
            try:
                html_data = self.template.render(test_cycle=test_cycle, build=build, runlist_link=runlist_link,
                                                 time_date=time_date, pass_fail_summary=pass_fail_summary,
                                                 results_data=results_data, not_run_list=not_run_list)
                f = open(output_file, "w")
                f.write(html_data)
                f.close()
                log_worker.info(f"{self.this_class_name} - {this_method_name} - Created HTML report {output_file}")
                return True
            except Exception as e:
                log_worker.error(
                    f"{self.this_class_name} - {this_method_name} - Exception occurred while creating HTML report: "
                    f"{output_file}\n<{e}>")
                return False
        else:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - Cannot create HTML automation report as provided "
                f"results_data is empty")
            return False
