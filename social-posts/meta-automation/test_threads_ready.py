import unittest
from unittest.mock import patch
import publish_due as publisher


class ThreadsReadyTests(unittest.TestCase):
    def test_waits_until_ready(self):
        with patch.object(publisher, 'get_graph', side_effect=[{'status': 'IN_PROGRESS'}, {'status': 'FINISHED'}]) as get, patch.object(publisher.time, 'sleep') as sleep:
            publisher.wait_for_threads_container('123', 'secret')
            self.assertEqual(get.call_count, 2)
            sleep.assert_called_once_with(60)

    def test_terminal_states_fail_closed(self):
        for status in ['ERROR', 'EXPIRED', 'PUBLISHED']:
            with self.subTest(status=status), patch.object(publisher, 'get_graph', return_value={'status': status}), patch.object(publisher.time, 'sleep') as sleep:
                with self.assertRaises(RuntimeError):
                    publisher.wait_for_threads_container('123', 'secret')
                sleep.assert_not_called()

    def test_timeout_is_bounded(self):
        with patch.object(publisher, 'get_graph', return_value={'status': 'IN_PROGRESS'}) as get, patch.object(publisher.time, 'sleep') as sleep:
            with self.assertRaises(RuntimeError):
                publisher.wait_for_threads_container('123', 'secret')
            self.assertEqual(get.call_count, 5)
            self.assertEqual(sleep.call_count, 4)


if __name__ == '__main__':
    unittest.main()
