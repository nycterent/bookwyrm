""" bookwyrm settings and configuration """
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from bookwyrm.settings import *

CELERY_BROKER_URL = "redis://:{}@redis_broker:{}/0".format(
    requests.utils.quote(env("REDIS_BROKER_PASSWORD", "")), env("REDIS_BROKER_PORT")
)
CELERY_RESULT_BACKEND = "redis://:{}@redis_broker:{}/0".format(
    requests.utils.quote(env("REDIS_BROKER_PASSWORD", "")), env("REDIS_BROKER_PORT")
)

CELERY_DEFAULT_QUEUE = "low_priority"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
FLOWER_PORT = env("FLOWER_PORT")

INSTALLED_APPS = INSTALLED_APPS + [
    "celerywyrm",
]

ROOT_URLCONF = "celerywyrm.urls"

WSGI_APPLICATION = "celerywyrm.wsgi.application"

USE_SENTRY = env.bool("USE_SENTRY", False)
if USE_SENTRY:
   import sentry_sdk
   from sentry_sdk.integrations.celery import CeleryIntegration 
   from sentry_sdk.integrations.redis import RedisIntegration

   sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE"),
    integrations=[CeleryIntegration(), RedisIntegration()]
   )
