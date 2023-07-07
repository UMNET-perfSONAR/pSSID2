#!/usr/bin/env python
# pSSID algorithm for job dispatching
import sys
import json
import heapq
import re
from datetime import datetime
from croniter import croniter

class PSSID:
    """ The pSSID scheduler. """
    def __init__(self):
        self.hostname = "rpi1"
        self.config_file = None
        self.job_queue = []
        self.batch_set = set()
        self.data_block = {}
        self.host_data_dict = open('./host-data-dict', 'a')
        self.queue_info = open('./queue-info', 'w')
    
    def __del__(self):
        self.host_data_dict.close()
        self.queue_info.close()
    
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
        self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format("Host/Host Group", 'B/D', "Batch Name/Data Block Pair"))
        
    # load schedule queue and data dictionary from host stanza
    def load_hosts(self):
        for host in self.config_file['hosts']:
            if self.hostname == host["name"]:
                # process batches
                for batch in host['batches']:
                    for single_schedule in batch['schedule']:
                        next_time = self.get_next_time(datetime.now(), single_schedule)
                        heapq.heappush(self.job_queue,(next_time, batch["priority"], batch))
                    self.batch_set.add(batch["name"])
                    self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format(host["name"], 'B', batch["name"]))
                
                # process data
                for d in host['data']:
                    self.data_block[d] = host['data'][d]
                    self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format(host["name"], 'D', "{}:{}".format(d, host['data'][d])))
    
                # add stanza to host-data-dict
                # self.host_data_dict.write(str(host)+'\n')

        # print(self.job_queue)
        # print(self.data_block)
        print(self.batch_set)

    def regex_match(self, pattern_li):
        for x in pattern_li:
            try:
                if re.match(x, self.hostname) != None:
                    return True
            except re.error:
                print('Regex matching error.')
                pass
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
                            for single_schedule in batch['schedule']:
                                next_time = self.get_next_time(datetime.now(), single_schedule)
                                heapq.heappush(self.job_queue,(next_time, batch["priority"], batch))
                            self.batch_set.add(batch["name"])
                            self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format(host["name"], 'B', batch["name"]))
                    
                    # skip duplicate data block
                    for d in host['data']:
                        if d not in self.data_block:
                            self.data_block[d] = host['data'][d]
                            self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format(host["name"], 'D', "{}:{}".format(d, host['data'][d])))
                    
                    # add stanza to host-data-dict
                    # self.host_data_dict.write(str(host)+'\n')
        
        if all_group:
            for batch in all_group['batches']:
                if batch["name"] not in self.batch_set:
                    for single_schedule in batch['schedule']:
                        next_time = self.get_next_time(datetime.now(), single_schedule)
                        heapq.heappush(self.job_queue,(next_time, batch["priority"], batch))
                    self.batch_set.add(batch["name"])
                    self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format("ALL", 'B', batch["name"]))
            for d in all_group['data']:
                if d not in self.data_block:
                    self.data_block[d] = all_group['data'][d]
                    self.host_data_dict.write('{: <20} {: <5} {: <30}\n'.format("ALL", 'D', "{}:{}".format(d, all_group['data'][d])))

            # add stanza to host-data-dict
            # self.host_data_dict.write(str(all_group)+'\n')

        print(self.job_queue)
        print(self.data_block)
        print(self.batch_set)

    def get_next_time(self, baseline, cronkey):
        for schedule in self.config_file["schedules"]:
            print(cronkey, schedule["name"])
            if schedule["name"] == cronkey:
                sche = croniter(schedule["repeat"], baseline)
                return sche.get_next(datetime).timestamp()
        return None

    # print queue information in external log
    def print_queue_info(self):
        now = datetime.now()
        self.queue_info.write(now.strftime("%H:%M:%S")+ '\n')
        self.queue_info.write('{: <20} {: <10} {: <30}\n'.format("Next Run Time", "Priority", "Batch Name"))
        for timestamp, _, batch in heapq.nsmallest(len(self.job_queue), self.job_queue):
            future_time = datetime.fromtimestamp(timestamp)
            future_time_str = future_time.strftime("%H:%M:%S")
            self.queue_info.write('{: <20} {: <10} {: <30}\n'.format(future_time_str, batch['priority'], batch["name"]))


if __name__ == "__main__":
    dispatcher = PSSID()
    # dispatcher.find_hostname()
    # verify schedule, hostname
    # write the temp file
    dispatcher.load_json()
    dispatcher.load_hosts()
    dispatcher.load_host_group()
    dispatcher.print_queue_info()
