import threading
import unittest

from src.config_parser import parse_config
from src.fly_in import Fly_in


class RunTerminationTest(unittest.TestCase):
    def test_run_terminates_on_easy_map(self) -> None:
        graph = parse_config('maps/easy/01_linear_path.txt')
        fly_in = Fly_in(graph)
        result: dict[str, bool] = {}

        def runner() -> None:
            fly_in.run()
            result['done'] = True

        worker = threading.Thread(target=runner, daemon=True)
        worker.start()
        worker.join(5)

        self.assertTrue(result.get('done', False))

    def test_run_terminates_on_circular_loop_map(self) -> None:
        graph = parse_config('maps/medium/02_circular_loop.txt')
        fly_in = Fly_in(graph)
        result: dict[str, bool] = {}

        def runner() -> None:
            fly_in.run()
            result['done'] = True

        worker = threading.Thread(target=runner, daemon=True)
        worker.start()
        worker.join(15)

        self.assertTrue(result.get('done', False))


if __name__ == '__main__':
    unittest.main()
