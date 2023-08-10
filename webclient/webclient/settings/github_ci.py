import socket

from .dev import *

TEST_RUNNER = "core.tests.runner.AMCGithubTestRunner"
SKIP_SELENIUM_TESTS = True

LOGGING["handlers"]["logstash"]["tags"] = "gitlab_ci"
