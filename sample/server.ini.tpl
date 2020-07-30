[app:main]
use = egg:pypicloud

pypi.fallback = none

# We need this since the docker will most-likely be running 
# behind some form of HTTPs proxy
# https://pypicloud.readthedocs.io/en/latest/topics/deploy.html#https-and-reverse-proxies
# filter-with = proxy-prefix

pyramid.reload_templates = False
pyramid.debug_authorization = false
pyramid.debug_notfound = false
pyramid.debug_routematch = false
pyramid.default_locale_name = en

pypi.default_read =
    authenticated

# Set up GCS storage
pypi.storage = outcome.pypicloud_storage_gcs.ThreadsafeGoogleCloudStorage
storage.bucket = otc-registry-pypicloud

# https://pypicloud.readthedocs.io/en/latest/topics/storage.html#google-cloud-storage
storage.gcp_use_iam_signer=true

# Local cache
db.url = sqlite:///%(here)s/db.sqlite

# Github-based authentication 
pypi.auth = outcome.pypicloud_access_github.Poetry

auth.otc.github.organization = <GITHUB ORG>
auth.otc.github.token = <GITHUB TOKEN>

# Stores cookies etc. for the pypicloud UI
session.encrypt_key = FFpoaaM3LAJm8wc9qNQDUoC28hrwumyRJPzMA9X0wgA=
session.validate_key = hVW5NHQFlDm+iuycdE/TyzcDyTJtfyg5K+XxyKcxBWc=
session.secure = false
session.invalidate_corrupt = true

###
# wsgi server configuration
###

# https://pypicloud.readthedocs.io/en/latest/topics/deploy.html#https-and-reverse-proxies
; [filter:proxy-prefix]
; use = egg:PasteDeploy#prefix
; scheme = https

[server:main]
use = egg:waitress#main
host = 0.0.0.0
port = 8000

[uwsgi]
paste = config:%p
paste-logger = %p
master = true
processes = 5
reload-mercy = 15
worker-reload-mercy = 15
max-requests = 1000
enable-threads = true
http = 0.0.0.0:8000


###
# logging configuration
# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html
###

[loggers]
keys = root

# We're running in a docker, so we want to output all the logs to the console, not to files
[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)s %(asctime)s [%(name)s] %(message)s
