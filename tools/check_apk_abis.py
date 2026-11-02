#!/usr/bin/env python3
"""Check that the release APK contains only the intended native ABI and ELF type."""
import argparse
import struct
import sys
import zipfile

EXPECTED_ABI = 'arm64-v8a'
EXPECTED_LIBS = {'libmain.so', 'libSDL3.so', 'libc++_shared.so'}


def verify(path):
    with zipfile.ZipFile(path) as apk:
        libs = [name for name in apk.namelist() if name.startswith('lib/') and name.endswith('.so')]
        if not libs:
            raise ValueError('APK contains no native libraries')
        found = set()
        for name in libs:
            parts = name.split('/')
            if len(parts) != 3 or parts[1] != EXPECTED_ABI:
                raise ValueError(f'unexpected native library path: {name}')
            found.add(parts[2])
            with apk.open(name) as entry:
                header = entry.read(20)
            if (len(header) < 20 or header[:4] != b'\x7fELF' or header[4] != 2
                    or header[5] != 1 or struct.unpack_from('<H', header, 18)[0] != 183):
                raise ValueError(f'not a 64-bit little-endian AArch64 ELF: {name}')
        missing = EXPECTED_LIBS - found
        if missing:
            raise ValueError(f'missing libraries: {", ".join(sorted(missing))}')
        print(f'OK: {len(libs)} native libraries, all {EXPECTED_ABI} / AArch64')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk')
    args = parser.parse_args()
    try:
        verify(args.apk)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'APK verification failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
