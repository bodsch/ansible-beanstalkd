
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    cwd = os.getcwd()
    pp.pprint(cwd)
    pp.pprint(os.listdir(cwd))

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """

    """
    base_dir, molecule_dir = base_directory()

    pp.pprint(" => '{}' / '{}'".format(base_dir, molecule_dir))

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


@pytest.mark.parametrize("dirs", [
    "/var/lib/beanstalkd"
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


def test_files(host):

    distribution = host.system_info.distribution

    files = []
    files.append("/usr/bin/beanstalkd")

    if(distribution in ['redhat', 'centos', 'ol']):
        files.append("/etc/sysconfig/beanstalkd")
    else:
        files.append("/etc/default/beanstalkd")

    for fi in files:
        f = host.file(fi)
        assert f.exists
        assert f.is_file


def test_user(host):
    assert host.user("beanstalkd").exists
    assert host.group("beanstalkd").exists


def test_service(host):
    service = host.service("beanstalkd")

    if(service.__class__.__name__ != 'SysvService'):
        assert service.is_enabled is True

    assert service.is_running is True


@pytest.mark.parametrize("ports", [
    '127.0.0.1:11300'
])
def test_open_port(host, ports):
    for i in host.socket.get_listening_sockets():
        print(i)

    socket = host.socket("tcp://{}".format(ports))
    assert socket.is_listening
