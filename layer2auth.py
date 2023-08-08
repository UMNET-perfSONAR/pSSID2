import datetime
import os
import subprocess
import sys
import time

# cleanly stop any running wpa_supplicant process
subprocess.run(['wpa_cli' ,'terminate'])
time.sleep(2)

# file rewritten between consecutive runs
WPA_CONFIG_PATH = '/etc/wpa_supplicant.conf'
# initializes only when wpa_supplicant starts
WPA_CTRL_IFACE_BASE = '/var/run/wpa_supplicant'

# error and diagnostic tracking
error = ''
diags = ''
authenticated = False
need_root = False

# declare local variables
interface = 'wlan0'
username = '' # enter your username
password = '' # enter your password
driver = ''
ssid = 'MWireless'
bssid = ''
key_management = 'WPA-EAP'
timeout = 4000

WPA_CONFIG_PATH = '/tmp/wpa_supplicant.conf'
WPA_CTRL_IFACE_BASE = '/var/run/wpa_supplicant'

# write the config file for reconfiguring the interface
temp = open(WPA_CONFIG_PATH,'w')
temp.writelines(['ctrl_interface=DIR=/var/run/wpa_supplicant\n', 'update_config=1\n', 'country=US\n', 'p2p_disabled=1\n',  'network={\n'])
temp.write('ssid="{}"\n'.format(ssid))
temp.write('scan_ssid=1\n')
if bssid != '':
    temp.write('bssid={}\n'.format(bssid))
temp.write('key_mgmt={}\n'.format(key_management))
temp.write('identity="{}"\n'.format(username))
temp.write('password="{}"\n'.format(password))
temp.write('eap=PEAP\n')
temp.write('phase1="peaplabel=0"\n')
temp.write('phase2="auth=MSCHAPV2"\n')
temp.write('}\n')
temp.close()

start_time = datetime.datetime.now()
os.system(f'wpa_supplicant -Dnl80211 -B -i{interface} -c{WPA_CONFIG_PATH}')


wpa_status = ["wpa_cli", "status"]
res = subprocess.run(wpa_status, capture_output = True, text = True)
if res.returncode != 0:
    succeeded = False
    fail_json = { 'succeeded': succeeded,
              'error': 'failed to run wpa_cli to validate the authentication',
              'diags': diags }
    sys.exit(1)
else:
    succeeded = True

# iteratively checks the wpa state until completion
print(res.stdout)
res = res.stdout.split('\n')
while "wpa_state=COMPLETED" not in res:
    print("debug:" + str(res))
    proc = subprocess.run(wpa_status, timeout=timeout, capture_output = True, text = True)
    res = proc.stdout.split('\n')
    time.sleep(0.3)

# get the end time for wpa_supplicant to be initialized
end_time = datetime.datetime.now()

# organize results into json data
results = {
    'succeeded': succeeded,
    'result': {
        'schema': 1,
        'time': end_time - start_time,
        'succeeded': succeeded,
        'final': res
    },
    'error': error,
    'diags': diags }

print(results)
