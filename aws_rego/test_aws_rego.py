import pytest
from os import environ
from subprocess import run
from pathlib import Path


@pytest.mark.parametrize("module_string", [
    "ec2_old_snapshots-cli_out", # ec2
    "stray_ebs-cli_out",
    "unattached_eips-cli_out",
    "high_error_rate-cli_out", # elb
    "inactive_load_balancers-cli_out",
    "no_healthy_targets-cli_out",
    "low_request_counts-cli_out",
    "console_access-cli_out", # iam
    "mfa_enabled-cli_out",
    "overdue_api_keys-cli_out",
    'unused_policies-cli_out',
    'empty_zones-cli_out', # route53
    "empty_storage-cli_out", # rds
    "rds_idle-cli_out",
    "rds_old_snapshots-cli_out",
    "scaling_down-cli_out",
    "object_last_modified-cli_out", # s3
    "storage_class_usage-cli_out",
    "unused_buckets-cli_out",
])
def test_all_rego_checks(module_string):
    # get `OPSBOX_PATH`, `TEST_CONF_PATH` from environment
    OPSBOX_PATH = Path(environ.get('OPSBOX_PATH', '../opsbox-core'))
    TEST_CONF_PATH = Path(environ.get('TEST_CONF_PATH', 'test.json'))
    PLUGIN_PATH = Path(__file__).parent.parent

    cmd = ['uv', 'run', 'opsbox', '--modules', module_string, '--config', str(TEST_CONF_PATH), '--log_level', 'TRACE', '--plugin_dir', str(PLUGIN_PATH)]

    try:
        process = run(
            cmd, text=True, capture_output=True, check=True, cwd=OPSBOX_PATH
        )
    except Exception as e:
        process = e

    with open(f'{module_string}.txt', 'w') as f:
        if hasattr(process, 'stdout'):
            f.write(process.stdout)
        else:
            f.write(str(process))
    pass