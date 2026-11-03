from typing import Callable
from .connection import connection_manager, connection_driver
from .handle import payload_handle, disconnected_handle


class NetProxy:
    def __init__(self, manager: connection_manager.ConnectionManager):
        self._connection_manager = manager
        self._pipes = {}

    def enable_client_endpoint(self, address: str, port: int) -> None:
        self._connection_manager.enable_server(address, port)

    def disable_client_endpoint(self) -> None:
        self._connection_manager.disable_server()

    def create_pipe(self, name: str) -> bool:
        if name in self._pipes:
            return False
        self._pipes[name] = self._Pipe()
        return True

    def delete_pipe(self, name: str) -> None:
        pipe = self._pipes.pop(name, self._Pipe())
        pipe.disconnect_client()
        pipe.disconnect_host()

    def delete_all_pipes(self) -> None:
        keys = [k for k, v in self._pipes.items()]
        for key in keys:
            self.delete_pipe(key)

    def pipe_count(self) -> int:
        return len(self._pipes)

    def connect_pending_client(self, pipe_name: str, timeout_s: int) -> bool:
        pipe = self._pipes.get(pipe_name, None)
        if pipe is None:
            return False
        pipe.disconnect_client()
        connection = self._connection_manager.listen_for_client(timeout_s)
        pipe.set_client(connection)
        return connection is not None

    def connect_host(self, pipe_name: str, hostname: str, port: int, timeout_s: int) -> bool:
        pipe = self._pipes.get(pipe_name, None)
        if pipe is None:
            return False
        pipe.disconnect_host()
        connection = self._connection_manager.connect_host(hostname, port, timeout_s)
        pipe.set_host(connection)
        return connection is not None

    def enable_routing(self, pipe_name: str) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.enable()

    def set_client_routing_action(self, pipe_name: str, action: payload_handle.PayloadHandle) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.set_client_action(action)

    def on_client_disconnected(self, pipe_name: str, cb: disconnected_handle.DisconnectedHandle) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.set_on_client_disconnected(cb)

    def disconnect_client(self, pipe_name: str) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.disconnect_client()

    def set_host_routing_action(self, pipe_name: str, action: payload_handle.PayloadHandle) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.set_host_action(action)

    def on_host_disconnected(self, pipe_name: str, cb: disconnected_handle.DisconnectedHandle) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.set_on_host_disconnected(cb)

    def disconnect_host(self, pipe_name: str) -> None:
        pipe = self._pipes.get(pipe_name, self._Pipe())
        pipe.disconnect_host()

    class _Pipe:
        def __init__(self):
            self._client = self._DummyDriver()
            self._host = self._DummyDriver()
            self._client_action = self._DummyAction()
            self._host_action = self._DummyAction()
            self._client_disconnected_handle = self._DisconnectHandle()
            self._host_disconnected_handle = self._DisconnectHandle()

        def set_client(self, client):
            self._client = client or self._DummyDriver()
            self._client.on_disconnected(self._client_disconnected_handle)

        def set_host(self, host):
            self._host = host or self._DummyDriver()
            self._host.on_disconnected(self._host_disconnected_handle)

        def disconnect_client(self):
            self._client.on_disconnected(self._DisconnectHandle())
            self._client.disconnect()

        def disconnect_host(self):
            self._host.on_disconnected(self._DisconnectHandle())
            self._host.disconnect()

        def set_client_action(self, action):
            self._client_action = action or self._DummyAction()

        def set_host_action(self, action):
            self._host_action = action or self._DummyAction()

        def set_on_client_disconnected(self, cb):
            self._client_disconnected_handle.set_composite_handle(cb)

        def set_on_host_disconnected(self, cb):
            self._host_disconnected_handle.set_composite_handle(cb)

        def enable(self):
            self._client.on_receive(self._PayloadRouter(self._client_action, self._host))
            self._host.on_receive(self._PayloadRouter(self._host_action, self._client))

        class _DummyAction(payload_handle.PayloadHandle):
            def execute(self, payload: bytes) -> bytes:
                return payload

        class _DummyDriver(connection_driver.ConnectionDriver):
            def send(self, payload: bytes) -> None:
                pass

            def disconnect(self) -> None:
                pass

            def on_receive(self, cb: Callable[[bytes], None]) -> None:
                pass

            def on_disconnected(self, cb: Callable[[None], None]) -> None:
                pass

        class _PayloadRouter:
            def __init__(self, action_hooks, endpoint):
                self._hooks = action_hooks
                self._endpoint = endpoint

            def __call__(self, packet):
                self._endpoint.send(self._hooks.execute(packet))

        class _DisconnectHandle:
            def __init__(self):
                self._client_handle = self._DummyDisconnectCb()

            def set_composite_handle(self, handle):
                self._client_handle = handle or self._DummyDisconnectCb()

            def __call__(self):
                self._client_handle.disconnected()

            class _DummyDisconnectCb(disconnected_handle.DisconnectedHandle):
                def disconnected(self) -> None:
                    pass
