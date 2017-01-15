from django_ztask.decorators import task
from system import services


@task()
def restart_rockstor(ip, port):
    services.update_nginx(ip, port)
