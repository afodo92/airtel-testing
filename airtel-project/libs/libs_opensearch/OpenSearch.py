#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : George Popovici
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" Module used as a wrapper on the opensearchpy package """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from opensearchpy import OpenSearch
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import OpenSearch as OPENSEARCHPARAMS
import helpers.Logger as Local_logger
import sys

log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["session_log_path"], f"OpenSearch_session_log.txt")


class API:
    def __init__(self, host, user, password):
        self.this_class_name = self.__class__.__name__
        this_method_name = sys._getframe().f_code.co_name

        port = OPENSEARCHPARAMS['port']
        self.index_name = OPENSEARCHPARAMS["index_name"]
        auth = (user, password)

        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - initiating instance for {host}")

        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth= auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )

    def create_document(self, doc):
        """
        Method used to create a document entry in opensearch database
        :param doc: Document to be written
        :return: True
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - writing document {doc}")

        return_val = True

        try:
            response = self.client.index(
                index=self.index_name,
                body=doc,
                refresh=True
            )
            log_worker.debug(
                f"{self.this_class_name} - {this_method_name} - received {response}")
        except Exception as e:
            log_worker.error(
                f"{self.this_class_name} - {this_method_name} - could not write document {doc}"
                f"Exception {e}"
            )
            return_val = False

        return return_val

    def delete_index(self):
        """
        Method used to delete an index from opensearch database
        :return: True
        """
        this_method_name = sys._getframe().f_code.co_name
        log_worker.debug(
            f"{self.this_class_name} - {this_method_name} - deleting index {self.index_name}")

        return_val = True

        try:
            response = self.client.indices.delete(
                index=self.index_name,
            )
            log_worker.debug(
                f"{self.this_class_name} - {this_method_name} - received {response}")
        except Exception as e:
            log_worker.warning(
                f"{self.this_class_name} - {this_method_name} - Could not delete index {self.index_name}"
                f"Exception {e}"
            )
            return_val = False

        return return_val
