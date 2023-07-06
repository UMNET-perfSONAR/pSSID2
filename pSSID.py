#!/usr/bin/env python
# pSSID algorithm for job dispatching
import sys
import json
import queue
import re
from datetime import datetime

class pSSID:
    def __init__(self):
        self.hostname = "rpi1"
        self.config_file = None
        self.job_queue = queue.PriorityQueue()
        self.batch_set = set()
        self.data_block = {}
        self.host_data_dict = open('./host-data-dict', 'a')
    
    def __del__(self):
        self.host_data_dict.close()
    
    # identify the host name of the machine
    def find_hostname(self):
        try:
            with open('/etc/hostname', 'r') as f:
                self.hostname = f.readline().strip()
        except FileNotFoundError:
            sys.exit('host name file not found')
    
    # load the json object to local storage 
    def load_json(self):
        try:
            with open('./pSSID_config.json', 'r') as conf:
                self.config_file = json.load(conf)
                print(self.config_file['hosts'])
        except json.JSONDecodeError:
            sys.exit('Json file failed to unpack')
        now = datetime.now()
        self.host_data_dict.write(now.strftime("%H:%M:%S")+ '\n')
    
    # load schedule queue and data dictionary from host stanza
    def load_hosts(self):
        for host in self.config_file['hosts']:
            if self.hostname == host["name"]:
                # process batches
                for batch in host['batches']:
                    self.job_queue.put((batch["priority"], batch))
                    self.batch_set.add(batch["name"])
                
                # process data
                for d in host['data']:
                    self.data_block[d] = host['data'][d]
                
                # add stanza to host-data-dict
                self.host_data_dict.write(str(host)+'\n')

        # print(self.job_queue)
        # print(self.data_block)
        print(self.batch_set)

    def regex_match(self, pattern_li):
        for x in pattern_li:
            if re.match(x, self.hostname) != None:
                return True
        return False
    
    def load_host_group(self):
        host_group = sorted(self.config_file['host_groups'], key=lambda x: x["name"])
        all_group = None
        for host in host_group:
            # extract ALL group
            if (host["name"].upper()) == "ALL":
                all_group = host
            else:
                if self.regex_match(host['hosts_regex']) or self.hostname in host['hosts']:
                    # skip duplicate batch
                    for batch in host['batches']:
                        if batch["name"] not in self.batch_set:
                            self.job_queue.put((batch["priority"], batch))
                            self.batch_set.add(batch["name"])
                    
                    # skip duplicate data block
                    for d in host['data']:
                        if d not in self.data_block:
                            self.data_block[d] = host['data'][d]
                    
                    # add stanza to host-data-dict
                    self.host_data_dict.write(str(host)+'\n')
        
        if all_group:
            for batch in all_group['batches']:
                if batch["name"] not in self.batch_set:
                    self.job_queue.put((batch["priority"], batch))
                    self.batch_set.add(batch["name"])
            for d in all_group['data']:
                if d not in self.data_block:
                    self.data_block[d] = all_group['data'][d]

            # add stanza to host-data-dict
                self.host_data_dict.write(str(all_group)+'\n')

        print(self.job_queue.get())
        print(self.job_queue.get())
        print(self.data_block)
        print(self.batch_set)

    
    

if __name__ == "__main__":
    dispatcher = pSSID()
    # dispatcher.find_hostname()
    dispatcher.load_json()
    dispatcher.load_hosts()
    dispatcher.load_host_group()
