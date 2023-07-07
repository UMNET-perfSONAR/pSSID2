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
            with open('./pSSID_config.json', 'r') as conf:
                self.config_file = json.load(conf)
        except json.JSONDecodeError:
            sys.exit('Json file failed to unpack')
    
    def verify_hostname(self):
        count = 0
        for host in self.config_file["hosts"]:
            if host["name"] == self.hostname:
                count += 1
        if count == 1:
            print('passed hosts test')
        else:
            sys.exit('Hosts must have one and only one host.')
    
    def verify_profile(self, name):
        for profile in self.config_file["SSID_profiles"]:
            if profile["name"] == name:
                return True
        return False
    
    def verify_single_batch(self, batch):
        # check SSID profile
        for profile in batch["SSID-profiles"]:
            if not self.verify_profile(profile):
                sys.exit('SSID profile name does not match')
        print('profile name in batch {} is verified'.format(batch["name"]))
    

# name is unique
# batch is well defined

if __name__ == "__main__":
    verifier = JSON_Verifier()
    verifier.load_json()
    verifier.verify_hostname()

