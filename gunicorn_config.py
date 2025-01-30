import multiprocessing

# Bind to a Unix socket instead of a network port
bind = "unix:/var/www/ScrapeMatic.sock"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout in seconds
timeout = 120

# Logging
accesslog = "/var/www/ScrapeMatic/logs/gunicorn_access.log"
errorlog = "/var/www/ScrapeMatic/logs/gunicorn_error.log"
loglevel = "info"

# Daemonization
daemon = False