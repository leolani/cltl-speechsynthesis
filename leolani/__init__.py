import os

import leolani

# TODO Get rid of the need for the root_dir
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(leolani.__file__)))

environment = {"GOOGLE_APPLICATION_CREDENTIALS": "/config/google_cloud_key.json"}
for key, value in environment.items():
    os.environ[key.upper()] = root_dir + value
