#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from time import sleep
from telnetlib import Telnet

ip = "10.0.3.209"

ping_cmd = "ping -c 1 -W 3 " + ip
ping_ip = os.system(ping_cmd)

if ping_ip == 0:
    # Success returns exit code: 0
    print("up", ping_ip)
    telnet_obj = Telnet(ip,8899,3)

    tn_data_good = None
    while True:
        tn_data = telnet_obj.read_until(b"EOT").decode("ascii")
        if str(tn_data).find("V0") != -1:
            tn_data_good = tn_data
            break
        else:
            sleep(1)
    print(tn_data_good)

else:
    # Fail returns exit code 256
    print("down", ping_ip)

exc_cor = 123456

sanitized_data = str(tn_data_good).strip()
sanitized_data = sanitized_data.replace("b'","")
sanitized_data = sanitized_data.replace("T'","T")
sanitized_data = sanitized_data.replace(" EOT","")
sanitized_data = sanitized_data.replace("\\n","")
sanitized_data = sanitized_data.replace("\\r","")
sanitized_data = sanitized_data.replace("\n","")
sanitized_data = sanitized_data.replace("\r","")
print("\n\n")
print(sanitized_data)
print("\n\n")
data_split_list = sanitized_data.split(" ")
print(data_split_list)
print("\n\n")

data_split_key_value = {}
for data_key_value in data_split_list:
    if data_key_value.find(":") != -1:
        split_map = data_key_value.split(":")
        print(split_map)
        data_split_key_value[split_map[0]] = split_map[1]
print(data_split_key_value)

exc_old = data_split_key_value["exc"]
print(exc_old)
data_split_key_value["exc"] = exc_cor
print(data_split_key_value)
exc_new = data_split_key_value["exc"]
print(exc_new)
