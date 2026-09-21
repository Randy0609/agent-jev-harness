"""python -m integrations.kit setup|status|run COMPONENT [arguments ...]."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'integrations'
RUNTIME = ROOT / '.runtime' / 'integrations'
LOCK = json.loads((BASE / 'upstream.lock.json').read_text())


def source(name):
    path = BASE / 'upstream' / name
    expected = LOCK[name]['commit']
    actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected:
        raise ValueError(f'{name}: upstream commit mismatch; run setup again')
    return path


def binary():
    return RUNTIME / 'evaluate'


def verify_binary():
    receipt = json.loads((RUNTIME / 'evaluate.receipt.json').read_text())
    if receipt['release'] != LOCK['typesafe-mcp']['release'] or hashlib.sha256(binary().read_bytes()).hexdigest() != receipt['sha256']:
        raise ValueError('evaluate binary changed; run setup typesafe-mcp')


def setup(name):
    if name == 'json-render':
        subprocess.run(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=BASE / 'dashboard', check=True)
        subprocess.run(['npm', 'run', 'build'], cwd=BASE / 'dashboard', check=True)
        return
    subprocess.run(['git', 'submodule', 'update', '--init', '--depth', '1', '--', f'integrations/upstream/{name}'], cwd=ROOT, check=True)
    src = source(name)
    if name == 'typesafe-mcp':
        system = {'Darwin': 'darwin', 'Linux': 'linux'}.get(platform.system())
        arch = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'amd64', 'AMD64': 'amd64'}.get(platform.machine())
        asset = f'evaluate-{system}-{arch}.tar.gz'
        expected = LOCK[name]['assets'].get(asset)
        if not expected:
            raise ValueError('Supported prebuilt platforms: macOS/Linux arm64/amd64')
        url = f"https://github.com/{LOCK[name]['repo']}/releases/download/{LOCK[name]['release']}/{asset}"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(40_000_001)
        if len(data) > 40_000_000 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Release archive checksum mismatch')
        RUNTIME.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            members = [m for m in archive.getmembers() if Path(m.name).name == 'evaluate' and m.isfile()]
            if len(members) != 1 or members[0].size > 100_000_000:
                raise ValueError('Invalid binary archive')
            body = archive.extractfile(members[0]).read()
        binary().write_bytes(body)
        binary().chmod(0o700)
        (RUNTIME / 'evaluate.receipt.json').write_text(json.dumps({'release': LOCK[name]['release'], 'sha256': hashlib.sha256(body).hexdigest()}))
    elif name == 'jev-mcp':
        subprocess.run(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=src, check=True)
        subprocess.run(['npm', 'run', 'build'], cwd=src, check=True)
    # Canny ships compiled dist, and SemDecide has no runtime dependencies.


def command(name):
    if name == 'json-render':
        return ['npm', '--prefix', str(BASE / 'dashboard'), 'run', 'dev', '--']
    src = source(name)
    if name == 'canny':
        return ['node', str(src / 'dist' / 'cli.js')]
    if name == 'typesafe-mcp':
        verify_binary()
        return [str(binary())]
    if name == 'jev-mcp':
        path = src / 'dist' / 'index.js'
        if not path.exists():
            raise ValueError('Run setup jev-mcp first')
        return ['node', str(path)]
    if name == 'semdecide':
        return [sys.executable, '-m', 'integrations.semdecide_cli']
    raise ValueError('Unknown component')


def status():
    result = {}
    for name in LOCK:
        try:
            cmd = command(name)
            ready = shutil.which(cmd[0]) is not None
            if name == 'json-render':
                ready = ready and (BASE / 'dashboard' / 'node_modules' / '@json-render' / 'react').exists()
            result[name] = {'installed': ready, 'source': LOCK[name]['repo']}
        except (OSError, ValueError, subprocess.CalledProcessError):
            result[name] = {'installed': False, 'next': f'python -m integrations.kit setup {name}'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'status', 'run'])
    parser.add_argument('component', nargs='?', choices=[*LOCK, 'all'])
    args, rest = parser.parse_known_args()
    if args.action == 'status':
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return
    if not args.component:
        parser.error('component required')
    if args.action == 'setup':
        if rest:
            parser.error('unexpected setup arguments')
        for name in LOCK if args.component == 'all' else [args.component]:
            setup(name)
    else:
        if args.component == 'all':
            parser.error('run requires one component')
        forwarded = rest[1:] if rest[:1] == ['--'] else rest
        if args.component == 'canny' and forwarded == ['--help']:
            forwarded = ['help']
        cmd = command(args.component) + forwarded
        os.execvp(cmd[0], cmd)


if __name__ == '__main__':
    main()
