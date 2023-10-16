#  https://docs.gunicorn.org/en/stable/settings.html#config-file

# APP
bind = ["127.0.0.1:8000"]

# WORKERS
workers = 1
worker_class = "gthread"
worker_connections = 100
threads = 2
timeout = 30
graceful_timeout = 30

# LOGS
accesslog = "./var/log/gunicorn.log"
# Default access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
# Add milliseconds (#ms) to end of default access_log_format:
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(M)sms'
errorlog = "./var/log/gunicorn.log"
# loglevel = "debug"
