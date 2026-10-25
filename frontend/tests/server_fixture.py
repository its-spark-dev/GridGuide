"""Isolated browser fixtures using the frozen production API, with no provider/key.

Normal and insufficient-risk apps share immutable prepared data. Only the latter's
in-memory risk evidence differs; no source files or production endpoints change.
"""
import signal
import socket
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import uvicorn
from backend.api import create_app
from backend.data import prepare_context
from backend.planning import prepare_planning


def main():
    sockets = []
    servers = []
    threads = []
    stop = threading.Event()
    # Reserve both fixture ports before preparation. Never reuse or stop a service
    # that belongs to the user's demo or another teammate.
    try:
        for port in (18080, 18081):
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
            sock.listen(128)
            sockets.append(sock)
        context = prepare_context()
        planning = prepare_planning()
        insufficient = replace(context, facts=context.facts.model_copy(
            update={'historical_circuit_evidence': None}))
        for sock, prepared in zip(sockets, (context, insufficient)):
            app = create_app(lambda prepared=prepared: prepared, lambda: None, lambda: planning)
            server = uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False))
            thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
            servers.append(server)
            threads.append(thread)
            thread.start()
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        while not all(server.started for server in servers):
            if not all(thread.is_alive() for thread in threads):
                raise RuntimeError('Browser fixture API failed to start')
            time.sleep(.05)
        print('Browser fixtures ready: normal 18080; insufficient risk 18081; provider disabled.', flush=True)
        stop.wait()
    finally:
        for server in servers:
            server.should_exit = True
        for thread in threads:
            thread.join(timeout=5)
        for sock in sockets:
            sock.close()


if __name__ == '__main__':
    main()
