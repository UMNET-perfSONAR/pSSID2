# verifying the json file
import json
import sys

class JSON_Verifier:
    def __init__(self):
        self.config_file = None
        self.hostname = "rpi2"
    
    def find_hostname(self):
        try:
            with open('/etc/hostname', 'r') as f:
                self.hostname = f.readline().strip()
        except FileNotFoundError:
            sys.exit('host name file not found')

    def load_json(self):
        try:
            with open('/tmp/config.json', 'r') as conf:
                self.config_file = json.load(conf)
        except json.JSONDecodeError:
            sys.exit('Json file failed to unpack')
    
    def find_batch_name(self, name):
        for batch in self.config_file["batches"]:
            if batch["name"] == name:
                return True
        return False
    
    def verify_host_stanza(self):
        host_set = set()
        for host in self.config_file["hosts"]:
            host_set.add(host["name"])
            for batch_name in host['batches']:
                if not self.find_batch_name(batch_name):
                    sys.exit("Batch name does not find a match")
        if len(host_set) == len(self.config_file['hosts']):
            print('all names are unique in host')
        else:
            sys.exit('Hosts must have unique names.')
    
    def verify_profile(self, name):
        for profile in self.config_file["ssid_profiles"]:
            if profile["name"] == name:
                return True
        return False
    
    def verify_host_group_stanza(self):
        host_group_set = set()
        for host_group in self.config_file["host_groups"]:
            host_group_set.add(host_group["name"])
            for batch_name in host_group['batches']:
                if not self.find_batch_name(batch_name):
                    sys.exit("Batch name does not find a match")
        if len(host_group_set) == len(self.config_file['host_groups']):
            print('all names are unique in host group')
        else:
            sys.exit('Hosts group must have unique names.')
    
    # helper functions for batch verification
    def verify_schedule(self, name):
        for schedule in self.config_file["schedules"]:
            if schedule["name"] == name:
                return True
        return False

    def verify_jobs(self, name):
        for test in self.config_file["jobs"]:
            if test["name"] == name:
                return True
        return False

    def verify_archivers(self, name):
        for archiver in self.config_file["archivers"]:
            if archiver["name"] == name:
                return True
        return False
    
    def verify_single_batch(self, batch):
        # check SSID profile
        for profile in batch["ssid_profiles"]:
            if not self.verify_profile(profile):
                sys.exit('SSID profile name does not match')
        print('profile name in batch {} is verified'.format(batch["name"]))

        # check schedule
        for schedule in batch["schedules"]:
            if not self.verify_schedule(schedule):
                sys.exit('Schedule name does not match') 
        print('schedule name in batch {} is verified'.format(batch["name"]))

        # check jobs
        for job in batch["jobs"]:
            if not self.verify_jobs(job):
                sys.exit('Job name does not match ' + job) 
        print('Job name in batch {} is verified'.format(batch["name"]))

        # check archivers
        for archiver in batch["archivers"]:
            if not self.verify_archivers(archiver):
                sys.exit('Archiver name does not match')
        print('Archiver name in batch {} is verified'.format(batch["name"]))

    def find_test_name(self, name):
        for test in self.config_file["tests"]:
            if test["name"] == name:
                return True
        return False
    
    def verify_job_stanza(self):
        job_set = set()
        for job in self.config_file["jobs"]:
            for test_name in job["tests"]:
                if not self.find_test_name(test_name):
                    sys.exit("Test name does not find a match " + test_name)
            job_set.add(job["name"])
        if len(job_set) == len(self.config_file["jobs"]):
            print("all names are unique in jobs")
        else:
            sys.exit("Jobs must have unique names.")


    def verify_batches_stanza(self):
        batch_set = set()
        for batch in self.config_file["batches"]:
            self.verify_single_batch(batch)
            batch_set.add(batch["name"])
        if len(batch_set) == len(self.config_file["batches"]):
            print("all names are unique in batches")
        else:
            sys.exit("Batches must have unique names.")

    # check for unique names in archivers
    def verify_archivers_stanza(self):
        archivers_set = set()
        for archiver in self.config_file["archivers"]:
            archivers_set.add(archiver["name"])
        if len(archivers_set) == len(self.config_file["archivers"]):
            print("all names are unique in archivers")
        else:
            sys.exit("archivers must have unique names.")
    
    def verify_tests_stanza(self):
        tests_set = set()
        for test in self.config_file["tests"]:
            tests_set.add(test["name"])
        if len(tests_set) == len(self.config_file["tests"]):
            print("all names are unique in tests")
        else:
            sys.exit("tests must have unique names.")
    
    def verify_schedules_stanza(self):
        schedules_set = set()
        for schedule in self.config_file["schedules"]:
            schedules_set.add(schedule["name"])
        if len(schedules_set) == len(self.config_file["schedules"]):
            print("all names are unique in schedules")
        else:
            sys.exit("schedules must have unique names.")
    
    def verify_ssid_stanza(self):
        ssid_set = set()
        for ssid in self.config_file["ssid_profiles"]:
            ssid_set.add(ssid["name"])
        if len(ssid_set) == len(self.config_file["ssid_profiles"]):
            print("all names are unique in ssid profiles")
        else:
            sys.exit("ssid profiles must have unique names.")

if __name__ == "__main__":
    verifier = JSON_Verifier()
    print('=====Loading json:')
    verifier.load_json()
    print('=====Verifiying host stanza:')
    verifier.verify_host_stanza()
    print('=====Verifying host group stanza:')
    verifier.verify_host_group_stanza()
    print('=====Verifying jobs stanza:')
    verifier.verify_job_stanza()
    print('=====Verifying batches stanza:')
    verifier.verify_batches_stanza()
    print('=====Verifying archivers stanza:')
    verifier.verify_archivers_stanza()
    print('=====Verifying tests stanza:')
    verifier.verify_tests_stanza()
    print('=====Verifying schedulers stanza:')
    verifier.verify_schedules_stanza()
    print('=====Verifying ssid profile stanza:')
    verifier.verify_ssid_stanza()
    print('=====ALL TESTS PASSED=====')


