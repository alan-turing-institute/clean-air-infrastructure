from run_on_cluster import cluster_config, max_settings
import subprocess
import os

cluster_settings = max_settings[cluster_config['cluster']]

script_str = """
ssh  -i "{SSH_KEY}" "{USER}@{IP}" -o StrictHostKeyChecking=no 'bash -s' << HERE
   squeue -u {USER}
HERE
""".format(
    SSH_KEY=cluster_settings['ssh_key'],
    USER=cluster_settings['user'],
    IP=cluster_settings['ip'],
)

cmd = os.system(script_str)
print(cmd)