#!/usr/bin/env python3
# Copyright (c) 2021-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

import os
import sys
import tempfile
import subprocess
import time
import argparse
import traceback
from pathlib import Path


def chdir_root(): os.chdir(str(Path(__file__).parent.parent))
def read_file_or(file, default): return open(file, 'r').read().strip() if os.path.exists(file) else default
def mister_ip(): return os.environ.get('MISTER_IP', read_file_or('mister.ip', None))
def mister_pw(): return read_file_or('mister.pw', '1')
def scp_path(p): return f'root@{mister_ip()}:{p}' if p.startswith('/media') else p
def exports(env=None): return " ".join(f"export {key}={value};" for key, value in (env or {}).items())
def scp_file(src, dest, **kwargs): _ssh_pass('scp', [scp_path(src), scp_path(dest)], **kwargs)
def exec_ssh(cmd, env=None, **kwargs): return _ssh_pass('ssh', [f'root@{mister_ip()}', f'{exports(env)}{cmd}'], **kwargs)
def run_build(**kwargs): send_build(env={"SKIP_REMOVALS": "true"}), exec_ssh(f'/media/fat/update_all.sh --no-continue', **kwargs)
def local_run(env=None): subprocess.run(['python3', './src/__main__.py'], env={**({} if env is None else env), 'LOCATION_STR': '.local_drv'}, check=True)
def run_launcher(**kwargs): send_build(**kwargs), exec_ssh(f'/media/fat/Scripts/update_all.sh', **kwargs)
def store_push(**kwargs): scp_file('update_all.json', '/media/fat/Scripts/.config/update_all/update_all.json', **kwargs)
def store_pull(**kwargs): scp_file('/media/fat/Scripts/.config/update_all/update_all.json', 'update_all.json', **kwargs)
def log_pull(**kwargs): scp_file('/media/fat/Scripts/.config/update_all/update_all.log', 'update_all.log', **kwargs)

def send_build(env=None, **kwargs):
    env = {'DEBUG': 'true', **os.environ.copy(), **(env or {}), 'MISTER': 'true'}
    with tempfile.NamedTemporaryFile(delete=False) as tmp: subprocess.run(['./src/build.sh'], stderr=sys.stdout, stdout=tmp, env=env, check=True)
    os.chmod(tmp.name, 0o755)

    scp_file(tmp.name, '/media/fat/update_all.sh', **kwargs)
    scp_file('update_all.sh', '/media/fat/Scripts/update_all.sh', **kwargs)

    os.remove(tmp.name)

def operations_dict(env=None, retries=False):
    return {
        'store_push': lambda: store_push(retries=retries),
        'store_pull': lambda: store_pull(retries=retries),
        'log_pull': lambda: log_pull(retries=retries),
        'build': lambda: [send_build(env=env, retries=retries), print('OK')],
        'run': lambda: run_build(env=env, retries=retries),
        'launcher': lambda: run_launcher(env=env, retries=retries),
        'copy': lambda: scp_file(sys.argv[2], f'/media/fat/{sys.argv[2]}'),
        'local_run': lambda: local_run(env=env),
    }

def _ssh_pass(cmd, args, out=None, retries=True):
    for i in range(4):
        try: return subprocess.run(['sshpass', '-p', mister_pw(), cmd, '-o', 'StrictHostKeyChecking=no', *args], check=True, stdout=out)
        except subprocess.CalledProcessError as e:
            if not retries or i >= 3: raise e
            traceback.print_exc()
            time.sleep(30 * (i + 1))

def _main():
    operations = operations_dict(env=os.environ.copy())
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=list(operations), nargs='?', default=None)
    parser.add_argument('parameter', nargs='?', default='')
    op = operations.get(parser.parse_args().command, operations['build'])
    op()

if __name__ == '__main__':
    _main()
