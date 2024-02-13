import requests
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class APISession(requests.Session):
    def __init__(self, repeat_step=1):
        self.this_class_name = self.__class__.__name__
        self.repeat_step = repeat_step
        super().__init__()

    def send_request(self, request_type, url, method_name, log_worker, json_data=None, request_description=""):
        ''''
        Method used to send and validate requests sent to the API Service.
        :param request_type: (Type of REST API request: GET, POST, PUT, DELETE)
        :param url: (APIv2 endpoint to send the request to)
        :param method_name: (Name of the method that is calling send_request)
        :param log_worker: (Logging session object)
        :param json_data: (JSON body to be sent as part of the request when using POST or PUT Request Types)
        :param request_description: (Informative data that is used in log details)
        :return: False or Return information in JSON format
        '''

        # TODO ADD RETRY MECHANISM (argument - number of retries)
        current_try = 0

        while current_try < self.repeat_step:
            current_try = current_try + 1

            try:
                if request_type.lower() == "get":
                    response = self.get(url)
                elif request_type.lower() == "post":
                    response = self.post(url, json=json_data)
                elif request_type.lower() == "put":
                    response = self.put(url, json=json_data)
                elif request_type.lower() == "delete":
                    response = self.delete(url, json=json_data)
                else:
                    log_worker.error(
                        f"{self.this_class_name} - {method_name} - {request_type.upper()} Request type is not supported.")
                    return False
                log_worker.info(
                    f"{self.this_class_name} - {method_name} - {request_type.upper()} Request with data={json_data} on {url} completed.")
            except Exception as e:
                log_worker.error(
                    f"{self.this_class_name} - {method_name} - {request_type.upper()} Request  with data={json_data} on {url} failed, {e}")
                continue
            if response.status_code in [200, 201, 204]:
                log_worker.info(
                    f"{self.this_class_name} - {method_name} - {request_type.upper()} Request on {request_description} was successful. Status Code: {response.status_code}.")
                try:
                    return response.json()
                except ValueError:
                    if response.text == '':
                        return True
                    else:
                        return response.text
                except Exception as e:
                    log_worker.debug(
                        f"{self.this_class_name} - {method_name} - {request_type.upper()} Failed to return response, error: {e}.")
                    return False
            else:
                try:
                    log_worker.warning(
                        f"{self.this_class_name} - {method_name} - {request_type.upper()} Request on {request_description} failed. Status Code: {response.status_code} (Expecting 200) and error: {response.text}")
                except:
                    log_worker.warning(
                        f"{self.this_class_name} - {method_name} - {request_type.upper()} Request on {request_description} failed. Status Code: {response.status_code}.")

                continue

        return False
