
def main():
    global run
    global proxy
    print('starting proxy')
    proxy.enable_client_endpoint('0.0.0.0', 8443)
    listener = threading.Thread(target=client_listener)
    status = threading.Thread(target=status_printer)
    status.start()
    listener.start()
    input('')
    run = False
    listener.join()
    print('listener done')
    status.join()
    print('status done')
    proxy.disable_client_endpoint()
    proxy.delete_all_pipes()


class DisconnectedHandle(disconnected_handle.DisconnectedHandle):
    def __init__(self, name):
        self.name = name

    def disconnected(self) -> None:
        print(self.name + ' has disconnected')
        proxy.delete_pipe(self.name)


class PrintActionHook(payload_handle.PayloadHandle):
    def __init__(self, prefix, next_action):
        self.prefix = prefix
        self.next_action = next_action

    def execute(self, payload: bytes) -> bytes:
        print(self.prefix + str(payload))
        return self.next_action.execute(payload)



if __name__ == '__main__':
    main()
