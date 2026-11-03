import unittest.mock
from netproxy import netproxy
from netproxy.connection import connection_manager, connection_driver
from netproxy.handle import payload_handle, disconnected_handle


class TestNetProxy(unittest.TestCase):
    def setUp(self):
        self.mock_connection_manager = unittest.mock.Mock(spec_set=connection_manager.ConnectionManager)
        self.test_proxy = netproxy.NetProxy(self.mock_connection_manager)

    def test_proxy_enables_client_connections_endpoint(self):
        self.test_proxy.enable_client_endpoint('', -1)
        self.assertEqual(1, self.mock_connection_manager.enable_server.call_count)

    def test_enables_client_connections_endpoint_with_address(self):
        test_address = 'some_address'
        self.test_proxy.enable_client_endpoint(test_address, -1)
        self.assertEqual(test_address, self.mock_connection_manager.enable_server.call_args.args[0])

    def test_enables_client_connections_endpoint_with_port(self):
        test_port = 8080
        self.test_proxy.enable_client_endpoint('', test_port)
        self.assertEqual(test_port, self.mock_connection_manager.enable_server.call_args.args[1])

    def test_disables_client_connections_endpoint(self):
        self.test_proxy.disable_client_endpoint()
        self.assertEqual(1, self.mock_connection_manager.disable_server.call_count)

    def test_proxy_starts_with_zero_pipes_created(self):
        self.assertEqual(0, self.test_proxy.pipe_count())

    def test_creating_pipe_increase_pipe_count(self):
        self.test_proxy.create_pipe('')
        self.assertEqual(1, self.test_proxy.pipe_count())

    def test_creating_pipe_with_distinct_name_succeed(self):
        self.assertTrue(self.test_proxy.create_pipe('name'))

    def test_creating_pipes_with_same_name_not_allowed(self):
        test_name = 'test'
        self.test_proxy.create_pipe(test_name)
        self.assertFalse(self.test_proxy.create_pipe(test_name))

    def test_create_several_pipes(self):
        self.test_proxy.create_pipe('one')
        self.test_proxy.create_pipe('two')
        self.test_proxy.create_pipe('three')
        self.assertEqual(3, self.test_proxy.pipe_count())

    def test_deleted_pipe_is_removed(self):
        pipe_name = 'pipe'
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.delete_pipe(pipe_name)
        self.assertEqual(0, self.test_proxy.pipe_count())

    def test_delete_all_created_pipes(self):
        self.test_proxy.create_pipe('p1')
        self.test_proxy.create_pipe('p2')
        self.test_proxy.delete_all_pipes()
        self.assertEqual(0, self.test_proxy.pipe_count())

    def test_listen_successful_client_connection_with_created_pipe(self):
        pipe_name = 'pipe1'
        self.mock_connection_manager.listen_for_client.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.test_proxy.create_pipe(pipe_name)
        self.assertTrue(self.test_proxy.connect_pending_client(pipe_name, 0))

    def test_listen_client_with_created_pipe_failed_outcome(self):
        pipe_name = 'pipe'
        self.mock_connection_manager.listen_for_client.return_value = None
        self.test_proxy.create_pipe(pipe_name)
        self.assertFalse(self.test_proxy.connect_pending_client(pipe_name, 0))

    def test_listen_client_with_no_active_pipes_will_fail(self):
        self.mock_connection_manager.listen_for_client.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.assertFalse(self.test_proxy.connect_pending_client('some_name', 0))

    def test_listen_client_with_invalid_pipe_name_will_fail(self):
        self.mock_connection_manager.listen_for_client.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.test_proxy.create_pipe('right')
        self.assertFalse(self.test_proxy.connect_pending_client('wrong', 0))

    def test_connecting_client_will_disconnect_old_connection(self):
        pipe_name = 'pipe'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.assertEqual(1, mock_client.disconnect.call_count)

    def test_listen_client_pass_maximum_wait_time(self):
        test_timeout = 500
        pipe_name = 'p'
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, test_timeout)
        self.assertEqual(test_timeout, self.mock_connection_manager.listen_for_client.call_args.args[0])

    def test_establish_successful_host_connection_with_created_pipe(self):
        pipe_name = 'pipe1'
        self.mock_connection_manager.listen_for_client.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.test_proxy.create_pipe(pipe_name)
        self.assertTrue(self.test_proxy.connect_host(pipe_name, '', 0, 0))

    def test_establish_host_connection_with_passed_hostname(self):
        pipe_name = 'a1'
        test_host_name = 'test.test'
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, test_host_name, 0, 0)
        self.assertEqual(test_host_name, self.mock_connection_manager.connect_host.call_args.args[0])

    def test_establish_host_connection_with_port_number(self):
        pipe_name = 'a1'
        test_port = 1234
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', test_port, 0)
        self.assertEqual(test_port, self.mock_connection_manager.connect_host.call_args.args[1])

    def test_establish_host_connection_with_connection_max_timeout(self):
        pipe_name = 'a1'
        test_timeout = 60
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, test_timeout)
        self.assertEqual(test_timeout, self.mock_connection_manager.connect_host.call_args.args[2])

    def test_connecting_host_will_disconnect_old_connection(self):
        pipe_name = 'pipe'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.assertEqual(1, mock_host.disconnect.call_count)

    def test_connecting_host_with_no_active_pipes_will_fail(self):
        self.mock_connection_manager.connect_host.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.assertFalse(self.test_proxy.connect_host('some_name', '', 0, 0))

    def test_connecting_host_with_invalid_pipe_name_will_fail(self):
        self.mock_connection_manager.connect_host.return_value = \
            unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.test_proxy.create_pipe('right')
        self.assertFalse(self.test_proxy.connect_host('wrong', '', 0, 0))

    def test_deleted_pipe_disconnects_client(self):
        pipe_name = 'p1'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.delete_pipe(pipe_name)
        self.assertEqual(1, mock_client.disconnect.call_count)

    def test_deleted_pipe_disconnects_host(self):
        pipe_name = 'p1'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.delete_pipe(pipe_name)
        self.assertEqual(1, mock_host.disconnect.call_count)

    def test_enable_pipe_listen_client_incoming_traffic(self):
        pipe_name = 'p1'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.enable_routing(pipe_name)
        self.assertEqual(1, mock_client.on_receive.call_count)

    def test_enable_pipe_does_not_listen_client_connection(self):
        pipe_name = 'p'
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.enable_routing(pipe_name)
        self.assertEqual(0, self.mock_connection_manager.listen_for_client.call_count)

    def test_enable_pipe_listen_host_incoming_traffic(self):
        pipe_name = 'p'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.enable_routing(pipe_name)
        self.assertEqual(1, mock_host.on_receive.call_count)

    def test_enable_pipe_does_not_create_host_connection(self):
        pipe_name = 'p'
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.enable_routing(pipe_name)
        self.assertEqual(0, self.mock_connection_manager.connect_host.call_count)

    def test_client_received_payload_routed_to_host(self):
        pipe_name = 'pipe'
        test_payload = b'123456789'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_client.on_receive.call_args.args[0](test_payload)
        self.assertEqual(test_payload, mock_host.send.call_args.args[0])

    def test_host_received_packet_routed_to_client(self):
        pipe_name = 'a'
        test_payload = b'some_test_data'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_host.on_receive.call_args.args[0](test_payload)
        self.assertEqual(test_payload, mock_client.send.call_args.args[0])

    def test_client_action_executed_on_packet_received(self):
        pipe_name = 'b'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_client_action = unittest.mock.Mock(spec_set=payload_handle.PayloadHandle)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.set_client_routing_action(pipe_name, mock_client_action)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_client.on_receive.call_args.args[0](b'12345')
        self.assertEqual(1, mock_client_action.execute.call_count)

    def test_client_action_hook_receive_correct_amount_of_data(self):
        test_data = b'1234567890'
        pipe_name = 'b'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_client_action = unittest.mock.Mock(spec_set=payload_handle.PayloadHandle)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.set_client_routing_action(pipe_name, mock_client_action)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_client.on_receive.call_args.args[0](test_data)
        self.assertEqual(test_data, mock_client_action.execute.call_args.args[0])

    def test_host_action_executed_on_packet_received(self):
        pipe_name = 'C'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_host_action = unittest.mock.Mock(spec_set=payload_handle.PayloadHandle)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.set_host_routing_action(pipe_name, mock_host_action)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_host.on_receive.call_args.args[0](b'15616465465')
        self.assertEqual(1, mock_host_action.execute.call_count)

    def test_host_action_hook_receive_correct_amount_of_data(self):
        test_data = b'123456789016546816'
        pipe_name = 'C'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        mock_host_action = unittest.mock.Mock(spec_set=payload_handle.PayloadHandle)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.set_host_routing_action(pipe_name, mock_host_action)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.enable_routing(pipe_name)
        mock_host.on_receive.call_args.args[0](test_data)
        self.assertEqual(test_data, mock_host_action.execute.call_args.args[0])

    def test_pipe_registers_handler_to_client_disconnect_event(self):
        pipe_name = 'C'
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.assertEqual(1, mock_client.on_disconnected.call_count)

    def test_when_client_disconnected_pipe_sends_notification(self):
        pipe_name = 'P'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.on_client_disconnected(pipe_name, mock_callback)
        mock_client.on_disconnected.call_args.args[0]()
        self.assertEqual(1, mock_callback.disconnected.call_count)

    def test_client_manual_disconnect_does_not_send_notification(self):
        pipe_name = 'pipe'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.on_client_disconnected(pipe_name, mock_callback)
        self.test_proxy.disconnect_client(pipe_name)
        mock_client.on_disconnected.call_args.args[0]()
        self.assertEqual(0, mock_callback.disconnected.call_count)

    def test_client_disconnect_notification_event_persists_after_manual_disconnect(self):
        pipe_name = 'a'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_client = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.listen_for_client.return_value = mock_client
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.on_client_disconnected(pipe_name, mock_callback)
        self.test_proxy.disconnect_client(pipe_name)
        self.test_proxy.connect_pending_client(pipe_name, 0)
        self.test_proxy.on_client_disconnected(pipe_name, mock_callback)
        mock_client.on_disconnected.call_args.args[0]()
        self.assertEqual(1, mock_callback.disconnected.call_count)

    def test_pipe_registers_handler_to_host_disconnect_event(self):
        pipe_name = 'p'
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.assertEqual(1, mock_host.on_disconnected.call_count)

    def test_when_host_disconnected_proxy_sends_notification(self):
        pipe_name = 'p'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.on_host_disconnected(pipe_name, mock_callback)
        mock_host.on_disconnected.call_args.args[0]()
        self.assertEqual(1, mock_callback.disconnected.call_count)

    def test_host_manual_disconnect_does_not_send_notification(self):
        pipe_name = 'pi'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.on_host_disconnected(pipe_name, mock_callback)
        self.test_proxy.disconnect_host(pipe_name)
        mock_host.on_disconnected.call_args.args[0]()
        self.assertEqual(0, mock_callback.disconnected.call_count)

    def test_host_disconnect_notification_event_persists_after_manual_disconnect(self):
        pipe_name = 'pipe'
        mock_callback = unittest.mock.Mock(spec_set=disconnected_handle.DisconnectedHandle)
        mock_host = unittest.mock.Mock(spec_set=connection_driver.ConnectionDriver)
        self.mock_connection_manager.connect_host.return_value = mock_host
        self.test_proxy.create_pipe(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.on_host_disconnected(pipe_name, mock_callback)
        self.test_proxy.disconnect_host(pipe_name)
        self.test_proxy.connect_host(pipe_name, '', 0, 0)
        self.test_proxy.on_host_disconnected(pipe_name, mock_callback)
        mock_host.on_disconnected.call_args.args[0]()
        self.assertEqual(1, mock_callback.disconnected.call_count)


if __name__ == '__main__':
    unittest.main()
