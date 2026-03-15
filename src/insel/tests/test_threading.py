"""
Threading stress test for libInselEngine.

Calls inselEngine() from multiple threads simultaneously, replicating what
inselBridge does in the GUI (multiple SwingWorker threads calling startInsel()).

The engine serialises concurrent calls with a mutex (inselEngine.cpp), so all
threads should complete cleanly with no exceptions and no ASAN errors.

ASAN could catch errors, but a SEGFAULT would also appear randomly without it,
before the engine was fixed.
"""

import contextlib
import ctypes
import os
import platform
import tempfile
import threading
import unittest
from pathlib import Path

import insel

N_THREADS = 20
N_REPEATS = 20

SIMPLE_MODEL = """\
s 1 CONST
p 1
\t1200.0
s 2 CONST
p 2
\t34.0
s 3 SUM 1.1 2.1
s 4 SCREEN 3.1
"""


@contextlib.contextmanager
def _suppress_c_stdout():
    """Redirect C-level stdout (fd 1) to /dev/null.

    Python's redirect_stdout only affects sys.stdout; this also silences
    printf() and Fortran WRITE(*,...) calls from the engine and block libs.
    fflush(NULL) drains all C/Fortran buffers before restoring the fd so
    buffered output doesn't leak onto the real stdout after the context exits.
    """
    libc = ctypes.CDLL('msvcrt' if platform.system() == 'Windows' else None)
    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.close(devnull)
    try:
        yield
    finally:
        libc.fflush(None)  # flush all C/Fortran buffered streams
        os.dup2(saved, 1)
        os.close(saved)


def _lib_path() -> Path:
    system = platform.system()
    if system == 'Windows':
        name = 'libInselEngine.dll'
    elif system == 'Darwin':  # no longer supported, but kept for completeness
        name = 'libInselEngine.dylib'
    else:
        name = 'libInselEngine.so'
    return insel.Insel.dirname / name


def _load_engine():
    lib = ctypes.CDLL(str(_lib_path()))
    lib.inselEngine.restype = ctypes.c_int
    lib.inselEngine.argtypes = [
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    return lib


class TestThreading(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not _lib_path().exists():
            raise unittest.SkipTest(f"Engine library not found: {_lib_path()}")
        cls.lib = _load_engine()

    def _run_models(self, model_path: str, thread_id: int,
                    results: list, errors: list, lock: threading.Lock):
        for i in range(N_REPEATS):
            try:
                run_bit = ctypes.c_int(1)
                argv = (ctypes.c_char_p * 3)(
                    b"insel",
                    model_path.encode(),
                    b"-c",
                )
                rc = self.lib.inselEngine(ctypes.byref(run_bit), 3, argv)
                with lock:
                    results.append((thread_id, i, rc))
            except Exception as e:
                with lock:
                    errors.append((thread_id, i, str(e)))

    def test_concurrent_engine_calls(self):
        """N_THREADS threads each run N_REPEATS models: no exceptions, no crashes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.insel',
                                         delete=False) as f:
            f.write(SIMPLE_MODEL)
            model_path = f.name

        results, errors = [], []
        lock = threading.Lock()

        threads = [
            threading.Thread(
                target=self._run_models,
                args=(model_path, i, results, errors, lock)
            )
            for i in range(N_THREADS)
        ]
        with _suppress_c_stdout():
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        Path(model_path).unlink(missing_ok=True)

        self.assertEqual(errors, [],
                         f"Exceptions in threads: {errors}")
        self.assertEqual(len(results), N_THREADS * N_REPEATS,
                         f"Expected {N_THREADS * N_REPEATS} runs, got {len(results)}")


if __name__ == '__main__':
    unittest.main()
