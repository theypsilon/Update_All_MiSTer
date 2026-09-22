from update_all.other import Defer


class DeferTester(Defer):
    def __init__(self):
        self.cleanup_calls = 0
        super().__init__(self._cleanup)

    def _cleanup(self):
        self.cleanup_calls += 1
