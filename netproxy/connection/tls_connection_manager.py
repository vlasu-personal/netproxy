import socket
import ssl
import threading
from typing import Optional, Callable
from . import connection_manager, connection_driver


class TlsConnectionManager(connection_manager.ConnectionManager):
    def __init__(self, path_client_cert_chain: str, path_client_key: str, path_host_ca_cert: str):
        self._host_ca_path = path_host_ca_cert
        self._server_socket = None
        self._server_tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self._server_tls_context.load_cert_chain(path_client_cert_chain, path_client_key)
        self._server_tls_context.options |= (ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)

    def enable_server(self, address: str, port: int) -> None:
        self.disable_server()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((address, port))
        self._server_socket.listen()

    def disable_server(self) -> None:
        if self._server_socket:
            self._server_socket.shutdown(socket.SHUT_RDWR)
            self._server_socket = None

    def listen_for_client(self, timeout_s: int) -> Optional[connection_driver.ConnectionDriver]:
        try:
            self._server_socket.settimeout(timeout_s)
            return self._ConnectionDriver(self._server_tls_context.wrap_socket(
                self._server_socket.accept()[0], server_side=True))
        except socket.timeout:
            pass
        except ssl.SSLEOFError:
            pass
        except ConnectionResetError:
            pass
        return None

    def connect_host(self, host: str, port: int, timeout_s: int) -> Optional[connection_driver.ConnectionDriver]:
        tls_context = ssl.create_default_context(cafile=self._host_ca_path)
        return self._ConnectionDriver(
            tls_context.wrap_socket(
                socket.create_connection((host, port), timeout=timeout_s), server_hostname=host))

    class _ConnectionDriver(connection_driver.ConnectionDriver):
        def __init__(self, live_socket):
            self._socket = live_socket
            self._receive_cb = None
            self._on_disconnected = lambda: None
            self._thread = threading.Thread(target=self._receive_worker)

        def disconnect(self) -> None:
            self._socket.shutdown(socket.SHUT_RDWR)

        def send(self, payload: bytes) -> None:
            self._socket.sendall(payload)

        def on_receive(self, cb: Callable[[bytes], None]) -> None:
            temp = self._receive_cb
            self._receive_cb = cb
            if not temp:
                self._thread.start()

        def on_disconnected(self, cb: Callable[[None], None]) -> None:
            self._on_disconnected = cb

        def _receive_worker(self):
            while True:
                chunk = self._socket.recv(65535)
                if chunk == b'':
                    self._on_disconnected()
                    break
                self._receive_cb(chunk)
