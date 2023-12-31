#!/usr/bin/env python
# pSSID algorithm for job dispatching
import sys
import json
import re
from datetime import datetime
import argparse
import sched
import time
import pscheduler
from croniter import croniter
from layer2scan import scan
from multiprocessing import Process

class PSSID:
    """ The pSSID scheduler. """
    def __init__(self, mode):
        self.hostname = "rpi1"
        self.config_file = None
        self.job_queue = []
        self.batch_set = set()
        self.data_block = {}
        self.scheduler = sched.scheduler(time.time,time.sleep)
        self.host_data_dict = open('./host-data-dict', 'a', encoding='utf-8')
        self.queue_info = open('./queue-info', 'a', encoding='utf-8')
        if mode == "d" or mode == "daemon":
            self.daemon_mode = True
        else:
            self.daemon_mode = False

    def __del__(self):
        self.host_data_dict.close()
        self.queue_info.close()

    def find_hostname(self):
        """ identify the host name of the machine running pSSID """
        try:
            with open('/etc/hostname', 'r', encoding='utf-8') as file:
                self.hostname = file.readline().strip()
            print("hostname: " + self.hostname)
        except FileNotFoundError:
            sys.exit('host name file not found')


    def load_json(self):
        """ load the json object to local storage """
        try:
            with open('./pSSID_config.json', 'r', encoding="utf-8") as conf:
                self.config_file = json.load(conf)
        except json.JSONDecodeError:
            sys.exit('Json file failed to unpack')
        now = datetime.now()
        self.host_data_dict.write(now.strftime("%H:%M:%S")+ '\n')
        self.host_data_dict.write(
            f'{"Host/Host Group": <20} {"B/D": <5} {"Batch Name/Data Block Pair": <30}\n'
        )


    def find_batch(self, name):
        """ find the batch json object given the name """
        for batchobj in self.config_file["batches"]:
            if batchobj["name"] == name:
                return batchobj
        return None


    def load_hosts(self):
        """ load schedule queue and data dictionary from host stanza """
        for host in self.config_file['hosts']:
            if self.hostname == host["name"]:
                # process batches
                for batch_name in host['batches']:
                    batch = self.find_batch(batch_name)
                    for single_schedule in batch['schedules']:
                        next_time = self.get_next_time(datetime.now(), single_schedule)
                        self.job_queue.append((next_time, batch["priority"], json.dumps(batch)))
                    self.batch_set.add(batch["name"])
                    self.host_data_dict.write(
                        f'{host["name"]: <20} {"B": <5} {batch["name"]: <30}\n'
                    )

                # process data
                for key in host['data']:
                    if key not in self.data_block: 
                        self.data_block[key] = host['data'][key]
                        pair_str = f'{key}:{host["data"][key]}'
                        self.host_data_dict.write(
                            f'{host["name"]: <20} {"D": <5} {pair_str: <30}\n'
                        )
        # debug purpose
        self.print_data_structure()

    def regex_match(self, pattern_li):
        """ match regex to selected hostname """
        for pattern in pattern_li:
            try:
                if re.match(pattern, self.hostname) is not None:
                    return True
            except re.error:
                print('Regex matching error.')
        return False
    
    def load_host_group(self):
        """ load jobs from host group configuration """
        host_group = sorted(self.config_file['host_groups'], key=lambda x: x["name"])
        all_group = None
        for host in host_group:
            # extract ALL group
            if (host["name"].upper()) == "ALL":
                all_group = host
            else:
                if self.regex_match(host['hosts_regex']) or self.hostname in host['hosts']:
                    for batch_name in host['batches']:
                        # skip duplicate batch
                        if batch_name not in self.batch_set:
                            batch = self.find_batch(batch_name)
                            for single_schedule in batch['schedules']:
                                next_time = self.get_next_time(datetime.now(), single_schedule)
                                # dump batch json object into job queue
                                self.job_queue.append(
                                    (next_time, batch["priority"], json.dumps(batch))
                                )
                            self.batch_set.add(batch_name)
                            self.host_data_dict.write(
                                f'{host["name"]: <20} {"B": <5} {batch["name"]: <30}\n'
                            )

                    for key in host["data"]:
                        # skip duplicate data block
                        if key not in self.data_block:
                            self.data_block[key] = host['data'][key]
                            pair_str = f'{key}:{host["data"]}'
                            self.host_data_dict.write(
                                f'{host["name"]: <20} {"D": <5} {pair_str: <30}\n'
                            )

        if all_group:
            for batch_name in all_group['batches']:
                if batch_name not in self.batch_set:
                    batch = self.find_batch(batch_name)
                    for single_schedule in batch['schedules']:
                        next_time = self.get_next_time(datetime.now(), single_schedule)
                        self.job_queue.append((next_time, batch["priority"], json.dumps(batch)))
                    self.batch_set.add(batch_name)
                    self.host_data_dict.write(
                        f'{"ALL": <20} {"B": <5} {batch["name"]: <30}\n'
                    )

            for key in all_group['data']:
                if key not in self.data_block:
                    self.data_block[key] = all_group['data'][key]
                    pair_str = f'{key}:{all_group["data"][key]}'
                    self.host_data_dict.write(
                        f'{"ALL": <20} {"D": <5} {pair_str: <30}\n'
                    )
        self.print_data_structure()

    def print_data_structure(self):
        """ printing global data structures for debugging purpose """
        print("="*10 + 'job queue' + "="*10)
        print(self.job_queue)
        print("="*10 + 'data block' + "="*10)
        print(self.data_block)
        print("="*10 + 'batch set' + "="*10)
        print(self.batch_set)

    def get_next_time(self, baseline, cronkey):
        """ get next timestamp (absolute time) given the schedule string """
        for schedule in self.config_file["schedules"]:
            if schedule["name"] == cronkey:
                sche = croniter(schedule["repeat"], baseline)
                return sche.get_next(datetime).timestamp()
        return None

    def print_queue_info(self):
        """ traverse queue and print information on queue log """
        now = datetime.now()
        self.queue_info.write(now.strftime("%H:%M:%S")+ '\n')
        self.queue_info.write(
            f'{"Next Run Time": <20} {"Priority": <10} {"Batch Name": <30}\n'
        )
        for timestamp, _, batch in self.job_queue:
            batch = json.loads(batch)
            future_time = datetime.fromtimestamp(timestamp)
            future_time_str = future_time.strftime("%H:%M:%S")
            self.queue_info.write(
                f'{future_time_str: <20} {batch["priority"]: <10} {batch["name"]: <30}\n'
            )

    def run(self):
        """ start running the scheduler """
        for task in self.job_queue:
            timestamp, pirority_num, batch = task
            self.scheduler.enterabs(timestamp, pirority_num, self.run_batch, argument=(batch,))
        self.print_queue_info()
        if self.daemon_mode:
            print("starting daemon process")
            process = Process(target=self.scheduler.run(), daemon=True)
            process.start()
            process.join()
        else:
            self.scheduler.run()
    
    def transform_task(self, transform_field, gen_task_obj):
        """ transform test spec """
        if transform_field in gen_task_obj["spec"]:
            match = re.match(r"^JQ\.(.*)", gen_task_obj["spec"][transform_field])
            if match:
                gen_task_obj["spec"][transform_field] = self.data_block[match.group(1).strip()]

    def run_batch(self, batch):
        """ main run function for each batch """
        extracted_batch = json.loads(batch)
        extracted_batch["BSSID-scan-interface"] = self.data_block["interface_wifi"] if "interface_wifi" in self.data_block else 'wlan0'

        # transform archivers
        for archiver in extracted_batch["archivers"]:
            for archiver_obj in self.config_file["archivers"]:
                if archiver_obj["name"] == archiver:
                    gen_archiver_obj = archiver_obj
                    for data_item in archiver_obj["data"]:
                        match = re.match(r"^JQ\.(.*)", archiver_obj["data"][data_item])
                        if match:
                            gen_archiver_obj["data"][data_item] = self.data_block[match.group(1).strip()]
                    print(gen_archiver_obj)

        print("scanning for entry points...")
        scan_res = json.loads(scan())
        print(scan_res)
        print("filtering list result based on SSID profile")
        res = []
        for bssid, info in scan_res.items():
            for each_profile in extracted_batch["ssid_profiles"]:
                for profile in self.config_file["ssid_profiles"]:
                    if profile["name"] == each_profile:
                        if info["Essid"] == profile["SSID"] and profile["min_signal"] < int(info["Signal_level"]):
                            res.append((profile["SSID"], bssid))
        print(res)
        
        # generating batch object
        batch_obj = {
            "jobs": []
        }

        print("process bssid list")
        for ssid, bssid in res:
            # updating data block
            if ssid not in self.data_block:
                self.data_block["ssid"] = ssid
            self.data_block["ssid"] = ssid
            if bssid not in self.data_block:
                self.data_block["bssid"] = bssid
            self.data_block["bssid"] = bssid
            
            # generating job object for batch
            for job in extracted_batch['jobs']:
                print("Executing job " + job)
                gen_job = {
                    "label:": extracted_batch['name'],
                    "iterations": self.data_block["iterations"] if "iterations" in self.data_block else 3,
                    "parallel": not self.data_block["sync-start"] if "sync-start" in self.data_block else False,
                    "task": [],
                    "task-transform": {
                        "script": [x for x in self.data_block["task-transform"]] if "task-transform" in self.data_block else []
                        }
                    }
                for single_job in self.config_file["jobs"]:
                    if single_job["name"] == job:
                        # gen job info
                        for single_test_str in single_job["tests"]:
                            for test_obj in self.config_file["tests"]:
                                if test_obj["name"] == single_test_str:
                                    # transform task
                                    gen_task_obj = test_obj

                                    self.transform_task("interface", gen_task_obj)
                                    self.transform_task("ssid", gen_task_obj)
                                    self.transform_task("bssid", gen_task_obj)

                                    print("Test obj: " + str(gen_task_obj))
                                    gen_job["task"].append(gen_task_obj)
                batch_obj["jobs"].append(gen_job)
        print("Batch obj" + str(batch_obj))
        if self.daemon_mode:
            processor = pscheduler.batchprocessor.BatchProcessor(batch_obj)
            res = processor()

        # reschedule soonest (only one time)
        next_time = min([self.get_next_time(datetime.now(), x) for x in extracted_batch['schedules']])
        future_time = datetime.fromtimestamp(next_time)
        future_time_str = future_time.strftime("%H:%M:%S")
        print(f"{extracted_batch['name']} is rescheduled to {future_time_str}")
        self.scheduler.enterabs(
            next_time,
            extracted_batch["priority"],
            self.run_batch,
            argument=(batch,)
        )
        self.print_queue_info()

if __name__ == "__main__":
    # command line parsing for mode specification
    parser = argparse.ArgumentParser(
        description='Choose which mode to run: Mock(M) or Daemon(D). Default would be Mock.'
        )
    parser.add_argument('--mode', '-m', type=str,
        help='A required argument for mode selection',
        choices=['m', 'mock', 'd', 'daemon'],
        required=True)

    # setup before entering the main loop
    args = parser.parse_args()
    dispatcher = PSSID(args.mode)
    dispatcher.find_hostname()
    dispatcher.load_json()
    dispatcher.load_hosts()
    dispatcher.load_host_group()
    dispatcher.print_queue_info()

    # execute scheduler
    dispatcher.run()
