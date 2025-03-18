import pytest
from os import environ
from subprocess import run
from pathlib import Path


@pytest.mark.parametrize("module_string", [
 #   "rds_idle-cli_out",
    # "rds_idle-json_out",
    # "rds_idle-text_out",
    # "rds_idle-jira_out",
    # "rds_idle-pagerduty_out",
    # "rds_idle-email_out",
    # "rds_idle-github_out",
    "rds_idle-azure_out",
])
def test_all_rego_checks(module_string):
    # get `OPSBOX_PATH`, `TEST_CONF_PATH` from environment
    OPSBOX_PATH = Path(environ.get('OPSBOX_PATH', '../opsbox-core'))
    TEST_CONF_PATH = Path(environ.get('TEST_CONF_PATH', 'test.json'))
    PLUGIN_PATH = Path(__file__).parent.parent

    cmd = ['uv', 'run', 'opsbox', '--modules', module_string, '--config', str(TEST_CONF_PATH), '--log_level', 'TRACE',"--verbose", '--plugin_dir', str(PLUGIN_PATH)]

    try:
        process = run(
            cmd, text=True, capture_output=True, check=True, cwd=OPSBOX_PATH
        )
    except Exception as e:
        if hasattr(e, 'stdout'):
            print(e.stdout)
            if "missing arguments" in e.stdout:
                pytest.skip("Missing arguments")

        if hasattr(e, 'stderr'):
            print(e.stderr)
            if "missing arguments" in e.stderr:
                pytest.skip("Missing arguments")
        raise e