"""End-to-end smoke test: runs the real curses app (main.py) attached to a
pty, drives it through the main menu, a few turns of real gameplay, the
inventory/help/character screens, and quits cleanly. This is the only test
that exercises curses itself -- everything else in the game is exercised
headlessly through GameSession.
"""

import os
import pty
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _spawn(extra_env=None):
    master_fd, slave_fd = pty.openpty()
    # A generously sized terminal so the 80x24 layout always fits.
    import fcntl
    import struct
    import termios

    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 100, 0, 0))

    env = dict(os.environ)
    env["TERM"] = "xterm-256color"
    if extra_env:
        env.update(extra_env)

    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=REPO_ROOT,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)
    os.set_blocking(master_fd, False)
    return proc, master_fd


def _send(master_fd, text):
    os.write(master_fd, text.encode())


def _drain(master_fd, duration=0.3):
    """Read whatever output has accumulated so the pty's output buffer
    never fills up and blocks the child. master_fd is non-blocking, so a
    read with nothing pending raises instead of hanging."""
    end = time.time() + duration
    data = b""
    while time.time() < end:
        try:
            chunk = os.read(master_fd, 65536)
        except BlockingIOError:
            time.sleep(0.01)
            continue
        except OSError:
            break
        if not chunk:
            break
        data += chunk
    return data


def _step(master_fd, keys, pause=0.15):
    _send(master_fd, keys)
    return _drain(master_fd, pause)


def test_full_session_smoke():
    proc, master_fd = _spawn()
    try:
        _drain(master_fd, 0.4)  # let the main menu render

        # Start a new game.
        _step(master_fd, "n")
        # Move around a bit, wait, check inventory/help/character screens.
        output = b""
        output += _step(master_fd, "jjllkkhh")
        output += _step(master_fd, "z")  # wait
        output += _step(master_fd, "i")  # inventory (use)
        output += _step(master_fd, "\x1b")  # cancel out
        output += _step(master_fd, "d")  # drop menu
        output += _step(master_fd, "\x1b")  # cancel out
        output += _step(master_fd, "c")  # character screen
        output += _step(master_fd, " ")  # dismiss
        output += _step(master_fd, "?")  # help screen
        output += _step(master_fd, " ")  # dismiss
        output += _step(master_fd, "m")  # message history
        output += _step(master_fd, "\x1b")  # exit history
        output += _step(master_fd, "jjjjhhhhllllkkkk")  # more movement

        assert proc.poll() is None, "process exited unexpectedly during play"

        # Save and quit back through the game, then quit from the main menu.
        output += _step(master_fd, "Q", pause=0.3)
        output += _step(master_fd, "q", pause=0.3)

        for _ in range(20):
            if proc.poll() is not None:
                break
            time.sleep(0.1)

        assert proc.poll() is not None, "process did not exit after quitting"
        assert proc.returncode == 0

        text = output.decode(errors="replace")
        assert "Traceback" not in text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        os.close(master_fd)


def test_terminal_too_small_exits_gracefully():
    proc, master_fd = _spawn()
    try:
        import fcntl
        import struct
        import termios

        # Shrink well below the required 80x24 before the app can read it.
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 10, 20, 0, 0))
        output = _drain(master_fd, 1.0)

        for _ in range(20):
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        output += _drain(master_fd, 0.2)

        assert proc.poll() is not None, "process should exit when terminal is too small"
        text = output.decode(errors="replace")
        assert "Traceback" not in text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        os.close(master_fd)
