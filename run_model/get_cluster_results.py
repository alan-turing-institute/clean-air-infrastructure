from run_on_cluster import cluster_config, max_settings
import subprocess

cluster_settings = max_settings[cluster_config['cluster']]

call_array = [
    "sudo", 
    "sh", "cluster_templates/get_results.sh",
    "--user", cluster_settings['user'],
    "--ip", cluster_settings['ip'],
    "--ssh_key", cluster_settings['ssh_key'],
    "--basename", cluster_config['base_name'],
    "--cluster_folder",cluster_config['cluster_tmp_folder'],
]

subprocess.call(call_array)