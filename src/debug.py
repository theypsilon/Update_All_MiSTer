#!/usr/bin/env python3
# Copyright (c) 2021-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

import os
import sys
import tempfile
import subprocess
import time
import argparse
import traceback
import shlex
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
def install_rc(**kwargs): send_build(debug='false', build_target='/media/fat/Scripts/update_all_rc.sh', launcher_target=False, **kwargs)
def local_run(env=None): subprocess.run(['python3', './src/__main__.py'], env={**({} if env is None else env), 'LOCATION_STR': '.local_drv'}, check=True)
def local_run_tiny(): subprocess.run(['script', '-q', '/dev/null', '-c', 'stty rows 15 cols 40 && python3 ./src/__main__.py'], env={**os.environ.copy(), 'LOCATION_STR': '.local_drv'}, check=True)
def local_run_small(): subprocess.run(['script', '-q', '/dev/null', '-c', 'stty rows 18 cols 80 && python3 ./src/__main__.py'], env={**os.environ.copy(), 'LOCATION_STR': '.local_drv'}, check=True)
def run_launcher(**kwargs): send_build(**kwargs), exec_ssh(f'/media/fat/Scripts/update_all.sh', **kwargs)
def benchmark_settings_screen_model(**kwargs):
    send_build(env={'SKIP_REMOVALS': 'true'}, **kwargs)
    benchmark_code = '''
import gc
import statistics
import sys
import time

sys.path.insert(0, "/tmp/update_all_model_benchmark.pyz")
from update_all.settings_screen_model import _manual_db_variables, settings_screen_model

gc.collect()
started = time.perf_counter_ns()
model = settings_screen_model()
first_call = time.perf_counter_ns() - started
model = None

for _ in range(5):
    model = settings_screen_model()
    model = None

samples = []
for _ in range(100):
    started = time.perf_counter_ns()
    model = settings_screen_model()
    samples.append(time.perf_counter_ns() - started)
    model = None

ordered = sorted(samples)
to_ms = lambda nanoseconds: nanoseconds / 1_000_000
print("settings_screen_model() on this device")
print(f"First call: {to_ms(first_call):.3f} ms")
print(f"Median:     {to_ms(statistics.median(samples)):.3f} ms")
print(f"Mean:       {to_ms(statistics.mean(samples)):.3f} ms")
print(f"Minimum:    {to_ms(ordered[0]):.3f} ms")
print(f"95th pct:   {to_ms(ordered[94]):.3f} ms")
print(f"Maximum:    {to_ms(ordered[-1]):.3f} ms")
print("Samples:    100")

manual_db_variables = _manual_db_variables()
recreate_samples = []
reuse_samples = []
for _ in range(2000):
    started = time.perf_counter_ns()
    db_ids = list(_manual_db_variables())
    recreate_samples.append(time.perf_counter_ns() - started)
    db_ids = None

    started = time.perf_counter_ns()
    db_ids = list(manual_db_variables)
    reuse_samples.append(time.perf_counter_ns() - started)
    db_ids = None

recreate_median = statistics.median(recreate_samples)
reuse_median = statistics.median(reuse_samples)
saving = recreate_median - reuse_median
print()
print("Caching _manual_db_variables()")
print(f"Recreate:   {to_ms(recreate_median):.3f} ms")
print(f"Reuse:      {to_ms(reuse_median):.3f} ms")
print(f"Saving:     {to_ms(saving):.3f} ms per model ({saving / statistics.median(samples) * 100:.2f}%)")
print("Samples:    2000 paired")
'''
    exec_ssh(
        'set -e\n'
        'tail -n +8 /media/fat/update_all.sh | xzcat -d -c > /tmp/update_all_model_benchmark.pyz\n'
        f'python3 -c {shlex.quote(benchmark_code)}',
        **kwargs,
    )
def store_push(**kwargs): scp_file('update_all.json', '/media/fat/Scripts/.config/update_all/update_all.json', **kwargs)
def store_pull(**kwargs): scp_file('/media/fat/Scripts/.config/update_all/update_all.json', 'update_all.json', **kwargs)
def log_pull(**kwargs): scp_file('/media/fat/Scripts/.config/update_all/update_all.log', 'update_all.log', **kwargs)
def send_linker(**kwargs):
    exec_ssh('mkdir -p /media/fat/Scripts/.config/update_all', **kwargs)
    scp_file('Linker.rbf', '/media/fat/Scripts/.config/update_all/Linker.rbf', **kwargs)

def send_build(env=None, build_target=None, launcher_target=None, debug=None, **kwargs):
    env = {'DEBUG': debug or 'true', **os.environ.copy(), **(env or {}), 'MISTER': 'true'}
    with tempfile.NamedTemporaryFile(delete=False) as tmp: subprocess.run(['./src/build.sh'], stderr=sys.stdout, stdout=tmp, env=env, check=True)
    os.chmod(tmp.name, 0o755)

    scp_file(tmp.name, build_target or '/media/fat/update_all.sh', **kwargs)
    if launcher_target is not False:
        scp_file('update_all.sh', launcher_target or '/media/fat/Scripts/update_all.sh', **kwargs)

    os.remove(tmp.name)

def operations_dict(env=None, retries=False):
    return {
        'store_push': lambda: store_push(retries=retries),
        'store_pull': lambda: store_pull(retries=retries),
        'log_pull': lambda: log_pull(retries=retries),
        'build': lambda: [send_build(env=env, retries=retries), print('OK')],
        'run': lambda: run_build(env=env, retries=retries),
        'launcher': lambda: run_launcher(env=env, retries=retries),
        'send_linker': lambda: [send_linker(retries=retries), print('OK')],
        'copy': lambda: scp_file(sys.argv[2], f'/media/fat/{sys.argv[2]}'),
        'rcopy': lambda: [scp_file(f'/media/fat/{sys.argv[2]}', Path(sys.argv[2]).name), print('OK')],
        'local_run': lambda: local_run(env=env),
        'local_run_tiny': lambda: local_run_tiny(),
        'local_run_small': lambda: local_run_small(),
        'benchmark_settings_screen_model': lambda: benchmark_settings_screen_model(retries=retries),
        'install_rc': lambda: install_rc()
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
