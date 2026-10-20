# laws fixtures

`fake-bend/bend` is a POSIX shell stand-in for the Bend CLI used by
`tests/test_run_verification_proof.py`. The real `bend` is never installed in
CI (the repository has no npm/node dependency either); the proof gate's
subprocess path is exercised by prepending this directory to `PATH` and
switching the script's behavior with `FAKE_BEND_MODE` (see the header comment
in the script). Minimal `LAWS.bend` / `PROOF.bend` / `main.bend` files are
written by the tests themselves into `tmp_path`.
