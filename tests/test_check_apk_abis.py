import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('check_apk_abis', Path(__file__).parents[1] / 'tools/check_apk_abis.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def elf(bits=2, machine=183):
    data = bytearray(20)
    data[:4] = b'\x7fELF'
    data[4:6] = bytes([bits, 1])
    data[18:20] = machine.to_bytes(2, 'little')
    return data


class ApkAbiTest(unittest.TestCase):
    def check(self, libraries):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'test.apk')
            with zipfile.ZipFile(path, 'w') as archive:
                for name, data in libraries.items():
                    archive.writestr(name, data)
            checker.verify(path)

    def valid(self):
        return {f'lib/arm64-v8a/{name}': elf() for name in checker.EXPECTED_LIBS}

    def test_valid(self):
        self.check(self.valid())

    def test_missing_library(self):
        libs = self.valid()
        del libs['lib/arm64-v8a/libmain.so']
        with self.assertRaisesRegex(ValueError, 'missing libraries'):
            self.check(libs)

    def test_wrong_abi(self):
        libs = self.valid()
        libs['lib/armeabi-v7a/libmain.so'] = elf(1, 40)
        with self.assertRaisesRegex(ValueError, 'unexpected native library path'):
            self.check(libs)

    def test_wrong_elf(self):
        libs = self.valid()
        libs['lib/arm64-v8a/libmain.so'] = elf(1, 40)
        with self.assertRaisesRegex(ValueError, 'not a 64-bit'):
            self.check(libs)

    def test_empty(self):
        with self.assertRaisesRegex(ValueError, 'no native libraries'):
            self.check({})


if __name__ == '__main__':
    unittest.main()
