"""Disposable test junctions only; never reads business data or credentials."""
import subprocess


def create_directory_junction(link, target):
    """Use separately rendered arguments; preserve diagnostics as raw-byte hex."""
    link_text, target_text = str(link), str(target)
    # cmd.exe still interprets its command line. Reject shell metacharacters;
    # spaces and non-ASCII names remain supported and exercised by real fixtures.
    if any(c in link_text + target_text for c in '"%!&|<>^\r\n'):
        raise RuntimeError("UNSAFE_FIXTURE_PATH")
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", link_text, target_text],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=15,
    )
    if result.returncode:
        stdout = result.stdout if result.stdout is not None else b""
        stderr = result.stderr if result.stderr is not None else b""
        if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
            raise TypeError("JUNCTION_DIAGNOSTICS_MUST_BE_RAW_BYTES")
        raise RuntimeError(
            "JUNCTION_FIXTURE_CREATION_FAILED "
            f"exit={result.returncode} "
            f"stdout_present={result.stdout is not None} "
            f"stderr_present={result.stderr is not None} "
            f"stdout_hex={stdout.hex()} stderr_hex={stderr.hex()}"
        )
    return result
