

Check connectivity to all hosts

'''
ansible -m ping
'''

'''
ansible \
  all \
  -m ping \
  --become \
  --become-user root \
  --become-method su \
  --ask-become-pass
'''
