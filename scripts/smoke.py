#!/usr/bin/env python3
"""Exercise CLI and an isolated FPM master over a private Unix socket."""
import argparse
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from common import ROOT


def record(kind, content):
    if len(content) > 65535:
        raise ValueError('FastCGI record too long')
    return struct.pack('!BBHHBB', 1, kind, 1, len(content), 0, 0) + content


def length(value):
    return bytes([value]) if value < 128 else struct.pack('!I', value | 0x80000000)


def request(path, script):
    params = {'GATEWAY_INTERFACE': 'CGI/1.1', 'REQUEST_METHOD': 'GET',
              'SCRIPT_FILENAME': str(script), 'SCRIPT_NAME': '/smoke.php',
              'REQUEST_URI': '/smoke.php', 'SERVER_PROTOCOL': 'HTTP/1.1',
              'SERVER_NAME': 'localhost', 'SERVER_PORT': '80',
              'REMOTE_ADDR': '127.0.0.1', 'CONTENT_LENGTH': '0'}
    body = b''
    for name, value in params.items():
        name, value = name.encode(), value.encode()
        body += length(len(name)) + length(len(value)) + name + value
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(15)
        connection.connect(str(path))
        connection.sendall(record(1, struct.pack('!HB5x', 1, 0)) + record(4, body)
                           + record(4, b'') + record(5, b''))

        def exact(count):
            result = b''
            while len(result) < count:
                block = connection.recv(count - len(result))
                if not block:
                    raise RuntimeError('Unexpected end of FastCGI response')
                result += block
            return result

        output, errors = b'', b''
        while True:
            version, kind, ident, size, padding, reserved = struct.unpack('!BBHHBB', exact(8))
            if version != 1 or ident != 1:
                raise RuntimeError('Unexpected FastCGI response header')
            content = exact(size)
            exact(padding)
            if kind == 6:
                output += content
            elif kind == 7:
                errors += content
            elif kind == 3:
                if len(content) != 8 or struct.unpack('!IB3x', content) != (0, 0):
                    raise RuntimeError('FastCGI request failed')
                break
        if errors:
            raise RuntimeError(errors.decode(errors='replace'))
    headers, separator, payload = output.partition(b'\r\n\r\n')
    if not separator or b'Status: 500' in headers:
        raise RuntimeError('Invalid FPM HTTP response: ' + output.decode(errors='replace'))
    return json.loads(payload.decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'build')
    args = parser.parse_args()
    if not hasattr(socket, 'AF_UNIX') or not hasattr(os, 'geteuid') or os.geteuid() == 0:
        raise SystemExit('Run as an unprivileged Linux user after the build.')
    work = args.work.resolve()
    script = ROOT / 'tests/smoke.php'
    cli = json.loads(subprocess.check_output([str(work / 'run-php'), str(script)]).decode())
    process = None
    with tempfile.TemporaryDirectory(prefix='stretch-fpm-') as temp:
        folder = Path(temp)
        template = (ROOT / 'config/fpm-smoke.conf.in').read_text()
        config = folder / 'fpm.conf'
        # FPM quotes paths; reject characters that could break its configuration syntax.
        for path in (folder, ROOT):
            if any(c in str(path) for c in ('"', '\n', '\r', '\\')):
                raise ValueError('Unsupported configuration path')
        config.write_text(template.replace('@RUNTIME@', str(folder)))
        with open(str(folder / 'fpm-output.log'), 'wb') as output:
            try:
                process = subprocess.Popen([str(work / 'run-fpm'), '-F', '-y', str(config)],
                                           stdout=output, stderr=output)
                deadline = time.time() + 20
                while not (folder / 'fpm.sock').exists():
                    if process.poll() is not None or time.time() >= deadline:
                        raise RuntimeError('FPM failed to start: ' + (folder / 'fpm-output.log').read_text())
                    time.sleep(0.1)
                fpm = request(folder / 'fpm.sock', script)
                if cli['sapi'] != 'cli' or fpm['sapi'] != 'fpm-fcgi' or not cli['ok'] or not fpm['ok']:
                    raise RuntimeError('Unexpected CLI/FPM test result')
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        report = {'status': 'passed', 'cli': cli, 'fpm': fpm,
                  'scope': 'Synthetic functional smoke tests; not an exploit or application test'}
        (work / 'smoke-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
