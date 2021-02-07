from huey.contrib.djhuey import task
from system import services


@task(name="ztask_helpers.restart_rockstor")
def restart_rockstor(ip, port):
    services.update_nginx(ip, port)
