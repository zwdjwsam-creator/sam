"""Read-only null stdin under the existing audit policy; no device exemptions."""
import os
import subprocess


def run_readonly_stdin(argv, **kwargs):
    if 'stdin' in kwargs:
        raise ValueError('STDIN_IS_FIXED_READ_ONLY_NULL')
    # subprocess.DEVNULL opens os.devnull O_RDWR internally. Passing an already
    # opened read-only handle avoids that write-mode open on both Windows/POSIX.
    with open(os.devnull, 'rb') as null_input:
        return subprocess.run(argv, stdin=null_input, **kwargs)
