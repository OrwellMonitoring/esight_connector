import json
import time
import logging
import requests
from datetime import datetime, timezone

from config import config
from devices import Device, Slot
from kafka_connector import Kafka_Connector
from esight_connector import Esight_Connector

if __name__ == '__main__':
    logging.basicConfig(format='[%(levelname)s] - %(asctime)s -> %(message)s', level=logging.INFO, datefmt='%d-%m-%Y %H:%M:%S')
    
    logging.info("Starting at " + datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M:%S"))

    esight = Esight_Connector(config.ESIGHT_LOCATION, config.ESIGHT_USERNAME, config.ESIGHT_PASSWORD)

    interfaces_tasks = {}
    slots_tasks = {}
    tasks_ids = {}
    
    # --- INTERFACES ---
    
    # GET INTERFACES LIST
    interfaces_list = esight.get_interfaces_list()

    # CREATE INTERFACES' TASKS
    for interface in interfaces_list:

        if interface["operstatus"] != 3:
            logging.info(interface["name"])

            interfaces_tasks[interface['name']] = {}
            
            task_id = f"orwell-{interface['name']}-out"
            if esight.create_task(
                task_id,
                interface["nedn"],
                interface["name"],
                'interface',
                'ifXTrafficStat',
                '[{"indicatorKey":"ifHCOutOctetsSpeed","symbol":"","thresholdValue":""}]',
                4
            ):
                interfaces_tasks[interface['name']][task_id] = {
                    "friendly_name": "sending_rate",
                    "interface": interface
                }
                tasks_ids[task_id] = {
                    "measUnitKey": "ifXTrafficStat",
                    "measTypeKey": "ifHCOutOctetsSpeed"
                }


            task_id = f"orwell-{interface['name']}-in"                        
            if esight.create_task(
                task_id,
                interface["nedn"],
                interface["name"],
                'interface',
                'ifXTrafficStat',
                '[{"indicatorKey":"ifHCInOctetsSpeed","symbol":"","thresholdValue":""}]',
                4
            ):
                interfaces_tasks[interface['name']][task_id] = {
                    "friendly_name": "receiving_rate",
                    "interface": interface
                }
                tasks_ids[task_id] = {
                    "measUnitKey": "ifXTrafficStat",
                    "measTypeKey": "ifHCInOctetsSpeed"
                }
    
    # --- SLOTS ---
    network_devices_list = esight.get_network_devices_list()

    # CREATE SLOTS' TASKS
    for device in network_devices_list:
        slots_tasks[device["nedn"]] = {}

        if device["necategory"] == Device.ROUTER.value:
            slots_list = esight.get_slots_list(device["nedn"])

            for slot in slots_list:

                if slot["operstatus"] in [3, 11, 13, 15, 16]:

                    if slot['physicalclass'] == Slot.BOARD.value and "IPU" in slot["slotname"]:
                        # CPU
                        # get cpu usage
                        logging.info(f'{slot["slotname"]}-cpu')
                        task_id = f"orwell-{slot['serialnum']}-cpu"                   
                        if esight.create_task(
                            task_id,
                            slot["nedn"],
                            "Slot:"+slot["slotname"].replace(" ", "%20"),
                            'slot',
                            'CpuState',
                            '[{"indicatorKey":"cpuUsage","symbol":"","thresholdValue":""}]',
                            4
                        ):
                            slots_tasks[device["nedn"]][task_id] = {
                                "friendly_name": "cpu_usage",
                                "slot": slot
                            }
                            tasks_ids[task_id] = {
                                "measUnitKey": "CpuState",
                                "measTypeKey": "cpuUsage"
                            }

                        # get mem usage
                        logging.info(f'{slot["slotname"]}-mem')
                        task_id = f"orwell-{slot['serialnum']}-mem"                    
                        if esight.create_task(
                            task_id,
                            slot["nedn"],
                            "Slot:"+slot["slotname"].replace(" ", "%20"),
                            'slot',
                            'MemState',
                            '[{"indicatorKey":"memUsage","symbol":"","thresholdValue":""}]',
                            4
                        ):
                            slots_tasks[device["nedn"]][task_id] = {
                                "friendly_name": "mem_usage",
                                "slot": slot
                            }
                            tasks_ids[task_id] = {
                                "measUnitKey": "MemState",
                                "measTypeKey": "memUsage"
                            }

                    elif slot['physicalclass'] == Slot.FAN.value:

                        # get fan speed
                        logging.info(f'{slot["slotname"]}-fan')
                        task_id = f"orwell-{slot['serialnum']}-fan"
                        if esight.create_task(
                            task_id,
                            slot["nedn"],
                            "Slot:"+slot["slotname"].replace(" ", "%20"),
                            'slot',
                            'hwEnvMainFan',
                            '[{"indicatorKey":"hwEntityFanSpeed","symbol":"","thresholdValue":""}]',
                            4
                        ):
                            slots_tasks[device["nedn"]][task_id] = {
                                "friendly_name": "fan_speed",
                                "slot": slot
                            }
                            tasks_ids[task_id] = {
                                "measUnitKey": "hwEnvMainFan",
                                "measTypeKey": "hwEntityFanSpeed"
                            }
                    
                    elif slot['physicalclass'] == Slot.POWER.value:

                        # get voltage
                        logging.info(f'{slot["slotname"]}-volt')
                        task_id = f"orwell-{slot['serialnum']}-volt"
                        if esight.create_task(
                            task_id,
                            slot["nedn"],
                            "Slot:"+slot["slotname"].replace(" ", "%20"),
                            'slot',
                            'hwEntityExtentMIB',
                            '[{"indicatorKey":"hwEntityVoltage","symbol":"","thresholdValue":""}]',
                            4
                        ):
                            slots_tasks[device["nedn"]][task_id] = {
                                "friendly_name": "voltage",
                                "slot": slot
                            }
                            tasks_ids[task_id] = {
                                "measUnitKey": "hwEntityExtentMIB",
                                "measTypeKey": "hwEntityVoltage"
                            }

    # we have to wait more or less 20 minutes so everything is up and running

    start = int(datetime.now(timezone.utc).timestamp()*1e3)

    time.sleep(20 * 60)

    response = requests.get(url=config.KAFKA_LOCATION).text
    kafka_producer = Kafka_Connector(response)
    
    counter = 1
    while True:

        # GET METRICS
        end = int(datetime.now(timezone.utc).timestamp()*1e3)
        
        # Interfaces
        for interface_name, tasks in interfaces_tasks.items():
            if len(tasks) > 0:
                msg = {
                    interface_name: {}
                }

                for task_id, task_info in tasks.items():

                    metrics = esight.get_task_metrics(
                        task_info["interface"]["nedn"], 
                        task_info["interface"]["name"],
                        'interface',
                        tasks_ids[task_id]["measUnitKey"],
                        tasks_ids[task_id]["measTypeKey"],
                        start,
                        end
                    )
                    msg[interface_name][task_info["friendly_name"]] = metrics

                kafka_producer.send_message('esight_interface', msg)

                with open(f'outputs/esight_interfaces_{counter}.txt', 'a+') as f:
                    f.write(json.dumps(msg, indent=4))
        
        # Slots
        for slot_nedn, tasks in slots_tasks.items():
            if len(tasks) > 0:
                msg = {}

                for task_id, task_info in tasks.items():
                    
                    if task_info["slot"]["slotname"] not in msg.keys():
                        msg[task_info["slot"]["slotname"]] = {}

                    metrics = esight.get_task_metrics(
                        task_info["slot"]["nedn"], 
                        "Slot:"+task_info["slot"]["slotname"].replace(" ", "%20"),
                        'slot',
                        tasks_ids[task_id]["measUnitKey"],
                        tasks_ids[task_id]["measTypeKey"],
                        start,
                        end
                    )

                    if task_info["friendly_name"] not in msg[task_info["slot"]["slotname"]].keys():
                        msg[task_info["slot"]["slotname"]][task_info["friendly_name"]] = []

                    msg[task_info["slot"]["slotname"]][task_info["friendly_name"]].append(metrics)                       

                kafka_producer.send_message('esight_slot', msg)

                with open(f'outputs/esight_slots_{counter}.txt', 'a+') as f:
                    f.write(json.dumps(msg, indent=4))
                    f.write('\n')

        start = end
        time.sleep(15*60)

        counter += 1

    # DELETE TASKS
    # this step is optional, we do it to avoid having tasks running when they are not needed
    for id in tasks_ids.keys():
        esight.delete_task(id)

