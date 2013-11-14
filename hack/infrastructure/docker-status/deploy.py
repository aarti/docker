'''Deploy docker-status and initialize it with docker registry service

      python deploy.py

'''
import oauth2 as oauth
import json
import urllib
import random
import shutil
import requests
import tempfile
import os
import time
from fabric import api
from fabric.api import run, sudo, warn_only
from subprocess import call

app_id = "docker-status"    # Stashboard application id
docker_status_server = 'docker-ci-report.dotcloud.com'
repository = 'mzdaniel/{}'.format(app_id)
data_repository = 'mzdaniel/{}'.format('data')
#dockerfile_url = ( 'http://raw.github.com/dotcloud/docker/master/hack/'
#    'infrastructure/docker-status/Dockerfile' )
dockerfile_url = ( 'https://raw.github.com/mzdaniel/docker/{}/'
    'hack/infrastructure/docker-status/Dockerfile'.format(app_id) )
data_dockerfile_url = ( 'http://raw.github.com/dotcloud/docker/master/'
    'contrib/desktop-integration/data/Dockerfile' )

# OAuth keys
consumer_key = 'anonymous'
consumer_secret = 'anonymous'
oauth_key = 'ACCESS_TOKEN'
oauth_secret = 'ACCESS_SECRET'
admin_login = 'test@example.com'

# Prepare fabric
api.env.host_string = docker_status_server
api.env.user = 'root'
api.env.key_filename = '/home/daniel/.ssh/dotcloud-dev.pem'


def retry(func,args=[],kwargs={},sleep=0,count=5,hide_exc=False,
 func_success=lambda x:True):
    '''Return func(args) after count tries if not exception and func_success'''
    for i in range(count):
        if i: time.sleep(sleep)
        try:
            retval = func(*args,**kwargs)
            if func_success(retval):
                return retval
        except Exception, exc:
            pass
    if not hide_exc: raise exc


def init_docker_status():
    '''Initialize docker-status with docker registry service'''


    # Create your consumer with the proper key/secret.
    # If you register your application with google, these values won't be
    # anonymous and anonymous.
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth.Token(oauth_key, oauth_secret)

    # Create our client.
    client = oauth.Client(consumer, token=token)

    # Base url for all rest requests
    #base_url = "https://%s.appspot.com/admin/api/v1" % app_id
    base_url = "http://{}:8080/admin/api/v1".format(docker_status_server)

    # Login as admin prompts stashboard to initialize itself
    r = requests.session()

    login_str = ( 'http://{}:8080/_ah/login?email={}&admin=True&action=Login&'
        'continue=http://localhost:8080/admin'.format(
        docker_status_server, admin_login) )
    retry(r.get, [login_str], sleep=1, hide_exc=True)
    r.get('http://{}:8080/admin'.format(docker_status_server))
    r.post('http://{}:8080/admin/setup'.format(docker_status_server))

    # CREATE a new service
    data = urllib.urlencode({
        "name": "registry",
        "description": "Docker registry service",
    })

    resp, content = client.request(base_url + "/services",
                                   "POST", body=data)
    service = json.loads(content)

    # GET the list of possible status images
    resp, content = client.request(base_url + "/status-images", "GET")
    data = json.loads(content)
    images = data["images"]

    # Pick a random image for our status
    image = random.choice(images)

    # POST to the Statuses Resources to create a new Status
    data = urllib.urlencode({
        "name": "Maintenance",
        "description": "The web service is under-going maintenance",
        "image": image["name"],
        "level": "WARNING",
    })

    resp, content = client.request(base_url + "/statuses", "POST", body=data)
    status = json.loads(content)

    # Ensure the new maintenance status gets updated
    retry(client.request, [base_url + '/statuses/maintenance', 'GET'], sleep=1,
        func_success=lambda x: x[0].get('status') == '200')

    # Create a new event with the given status and given service
    data = urllib.urlencode({
        "message": "Our first event! So exciting",
        "status": status["id"].lower(),
    })

    resp, content = client.request(service["url"] + "/events", "POST", body=data)

# Build docker-status container
tmp_dir = tempfile.mkdtemp(dir='.')
os.chdir(tmp_dir)
call('wget {}'.format(dockerfile_url), shell=True)
call('docker build -t {} .'.format(repository), shell=True)
call('wget {}'.format(data_dockerfile_url), shell=True)
call('docker build -t {} .'.format(data_repository), shell=True)
os.chdir('..')
shutil.rmtree(tmp_dir)

# Push container and data container to the index
call('docker push {}'.format(repository), shell=True)
call('docker push {}'.format(data_repository), shell=True)

# pull container
run('docker pull {}'.format(repository))
run('docker pull {}'.format(data_repository))

# Create data container
with warn_only():
    run('docker run -name {}-data {} true'.format(app_id, data_repository))

# Launch docker-status server
container_id = run('docker run -d -u 1000 -volumes-from {0}-data'
' -p 8080:8080 -p 8000:8000 {1}'.format(app_id, repository))

# initialize docker-status
init_docker_status()

# setup container
sudo('cat >/etc/init/docker-status.conf <<-EOF\n'
    '#!/bin/sh\n'
    'description docker-status\n'
    'author Daniel Mizyrycki\n'
    'start on filesystem and started lxc-net and started docker\n'
    'stop on runlevel [!2345]\n'
    'respawn\n'
    'exec /usr/bin/docker start -a "{}"\n'
    'EOF\n'.format(container_id))
