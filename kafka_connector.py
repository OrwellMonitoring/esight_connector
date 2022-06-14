# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Gonçalo Leal (goncalolealsilva@ua.pt)
# Date: 31-05-2022

# Description:
# kafka producer

import json
import logging
from kafka import KafkaProducer

class Kafka_Connector:
    producer = None

    def __init__(self, address):
        logging.basicConfig(format='[%(levelname)s] - %(asctime)s -> %(message)s', level=logging.INFO, datefmt='%d-%m-%Y %H:%M:%S')
        self.producer = KafkaProducer(
            bootstrap_servers=[address],
            value_serializer=lambda x: json.dumps(x).encode("ascii")
        )

    def send_message(self, topic, msg):
        logging.info(f"Sending message to {topic}")

        self.producer.send(topic, value=msg)
