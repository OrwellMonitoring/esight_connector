# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Gonçalo Leal (goncalolealsilva@ua.pt)
# Date: 28-05-2022

# Description:
# eSight Adapter to get 5G Core metrics

import time
import json
import logging
import requests

from esight_exceptions import CouldNotLoginOnEsight, UnexpectedError

class Esight_Connector:
    auth_token = ""
    expires_at = ""
    system_id = "NMSinfo3"

    def __init__(self, address, username, password):
        logging.basicConfig(format='[%(levelname)s] - %(asctime)s -> %(message)s', level=logging.INFO, datefmt='%d-%m-%Y %H:%M:%S')

        self.address = address
        self.username = username
        self.password = password
        self.authenticate()

    # DECORATORS
    # Auth Decorator
    def requires_auth(func, *args, **kwargs):
        def wrapper(self, *args, **kwargs):
            try:
                self.update_auth_token()
                return func(self, *args, **kwargs)
            except Exception as e:
                logging.exception("Auth Required: To call this function you need to be authenticated in eSight! - " + str(e))
                raise UnexpectedError("Auth Required: To call this function you need to be authenticated in eSight! - " + str(e))
        return wrapper

    def update_auth_token(self):
        # Avoid getting "Adding certificate verification is strongly advised" warnings
        requests.packages.urllib3.disable_warnings()

        response = requests.get(
            f"https://{self.address}/network/port",
            headers = {
                "openid": f"{self.auth_token}"
            },
            timeout = 5,
            verify = False
        )

        # check response status
        response.raise_for_status()

        # get data
        response_data = json.loads(response.text)

        if response_data["description"] == "openid auth failed.":
            self.authenticate()
        elif response_data["description"] != "Operation success":
            raise UnexpectedError("Something happened, check your connection.")

    def authenticate(self):
        try:

            data = json.dumps({
                "userid": self.username,
                "value": self.password,
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.put(
                f"https://{self.address}/sm/session",
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["description"] == "Operation success.":
                self.auth_token = response_data["data"]
            else:
                raise CouldNotLoginOnEsight()

        except:
            raise CouldNotLoginOnEsight()

    @requires_auth
    def get_interfaces_list(self):
        try:

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.get(
                f"https://{self.address}/network/port",
                headers = {
                    'openid': f'{self.auth_token}'
                },
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_interfaces_list: Something happened, could not get sending rate for interface {name}.")
                raise UnexpectedError(f"Something happened, could not get sending rate for interface {name}.")
                return []

            logging.info("get_interfaces_list: OK")
            return response_data["data"]

        except:
            logging.exception(f"get_interfaces_list: Error")
            raise CouldNotLoginOnEsight()
            return []

    @requires_auth
    def create_task(self, task_id, nedn, name, resource_type, group_key, indicators_data, period):
        try:
            data = json.dumps({
                'systemID': self.system_id,
                'taskID': task_id,
                'neDN': nedn,
                'subResourceName': name,
                'subResourceType': resource_type,
                'indicatorsGroupKey': group_key,
                'indicatorsData': indicators_data,
                'periodType': period
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.put(
                f"https://{self.address}/pm/realtimePerformance",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)
            
            if response_data["code"] != 0:
                logging.info(response_data)
                logging.exception(f"create_task: Something happened, could not create task for {name}.")

                return False

            logging.info("create_task: OK")
            return True

        except:
            logging.exception(f"create_task: Error")
            raise UnexpectedError(f"Something happened, could not create task for {name}.")
            return False

    @requires_auth
    def delete_task(self, task_id):
        try:

            data = json.dumps({
                'systemID': self.system_id,
                'taskID': task_id
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.delete(
                f"https://{self.address}/pm/realtimePerformance",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)
            
            if response_data["code"] != 0:
                logging.info(f"delete_task: Something happened, could not create task for {name}.")
                raise UnexpectedError(f"Something happened, could not create task for {name}.")

            logging.info("delete_task: OK")
        except:
            logging.exception("delete_task: Error")
            raise UnexpectedError(f"Something happened, could not create task for {name}.")

    def get_interface_sending_rate(self, nedn, name, start, finish):
        try:

            data = json.dumps({
                'mos': '[{"dn": "'+ nedn +'", "displayValue": "'+ name +'"}]',
                'indexKeys': '[{"resourceType":"interface","measUnitKey":"ifXTrafficStat","measTypeKey":"ifHCOutOctetsSpeed"}]',
                'beginTime': start,
                'endTime': finish
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.post(
                f"https://{self.address}/pm/historyByIndexKeys",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_interface_sending_rate: Something happened, could not get sending rate for interface {name}.")
                raise UnexpectedError(f"Something happened, could not get sending rate for interface {name}.")
                return json.loads({})

            logging.info("get_interface_sending_rate: OK")
            return response_data

        except:
            logging.exception("get_interface_sending_rate: Error")
            raise UnexpectedError(f"Something happened, could not get sending rate for interface {name}.")
            return json.loads({})

    def get_interface_receiving_rate(self, nedn, name, start, finish):
        try:

            data = json.dumps({
                'mos': '[{"dn": "'+ nedn +'", "displayValue": "'+ name +'"}]',
                'indexKeys': '[{"resourceType":"interface","measUnitKey":"ifXTrafficStat","measTypeKey":"ifHCInOctetsSpeed"}]',
                'beginTime': start,
                'endTime': finish
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.post(
                f"https://{self.address}/pm/historyByIndexKeys",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_interface_receiving_rate: Something happened, could not get receiving rate for interface {name}.")
                raise UnexpectedError(f"Something happened, could not get receiving rate for interface {name}.")
                return json.loads({})

            logging.info("get_interface_receiving_rate: OK")
            return response_data

        except:
            logging.exception("get_interface_receiving_rate: Error")
            raise UnexpectedError(f"Something happened, could not get receiving rate for interface {name}.")
            return json.loads({})

    @requires_auth
    def get_network_devices_list(self):
        try:

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.get(
                f"https://{self.address}/network/nedevice",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_network_devices_list: Something happened, could not get receiving rate for interface {name}.")
                raise UnexpectedError(f"Something happened, could not get receiving rate for interface {name}.")
                return []

            logging.info("get_network_devices_list: OK")
            return response_data["data"]

        except:
            logging.exception("get_network_devices_list: Error")
            raise CouldNotLoginOnEsight()
            return []

    @requires_auth
    def get_slots_list(self, nedn):
        try:

            data = json.dumps({
                'nedn': nedn
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.get(
                f"https://{self.address}/network/slot",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_slots_list: Something happened, could not get receiving rate for interface {name}.")
                raise UnexpectedError(f"Something happened, could not get receiving rate for interface {name}.")
                return []

            logging.info("get_slots_list: OK")
            return response_data["data"]

        except:
            logging.exception("get_slots_list: Error")
            raise CouldNotLoginOnEsight()
            return []

    def get_task_metrics(self, nedn, name, resource_type, unit_key, type_key, start, finish):
        try:

            data = json.dumps({
                'mos': '[{"dn": "'+ nedn +'", "displayValue": "'+ name +'"}]',
                'indexKeys': '[{"resourceType":"'+ resource_type +'","measUnitKey": "'+ unit_key +'","measTypeKey":"'+ type_key +'"}]',
                'beginTime': start,
                'endTime': finish
            })

            # Avoid getting "Adding certificate verification is strongly advised" warnings
            requests.packages.urllib3.disable_warnings()

            response = requests.post(
                f"https://{self.address}/pm/historyByIndexKeys",
                headers = {
                    'openid': f'{self.auth_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data = data,
                timeout = 5,
                verify = False
            )

            # check response status
            response.raise_for_status()

            # get data
            response_data = json.loads(response.text)

            if response_data["code"] != 0:
                logging.info(f"get_task_metrics: Something happened, could not get task metrics {name}.")
                raise UnexpectedError(f"Something happened, could not get task metrics {name}.")
                return json.loads({})

            logging.info("get_task_metrics: OK")
            return response_data["data"]

        except:
            logging.exception("get_task_metrics: Error")
            raise UnexpectedError(f"Something happened, could not get task metrics {name}.")
            return json.loads({})        


