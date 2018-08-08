import asyncio
from bluesky.utils import ensure_generator
from bluesky import Msg

def safe_add_plan(a, b):
    yield Msg('print', '{} + {} = ??'.format(a, b))
    try:
        ret = yield Msg('sum', None, a, b)
    except:
        yield Msg('print', 'something wrong')
    else:
        yield Msg('print', 'done')
    finally:
        yield Msg('print', 'finished')


class RE_v4():
    def __init__(self, *, loop=None):
        self.function_map = {'print': self._print,
                            'sum': self._sum}
        
        self.msg_hook = None
        if loop == None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._task = None

    def __call__(self, plan):
        self._task = self.loop.create_task(self._run(plan))
        self.loop.run_until_complete(self._task)

        if self._task.done() and not self._task.cancelled():
            exc = self._task.exception()
            if exc is not None:
                raise exc

    @asyncio.coroutine
    def _run(self, plan):
        plan = ensure_generator(plan)
        last_result = None
        _exception = None
        while True:
            try:
                if _exception is not None:
                    msg = plan.throw(_exception)
                    _exception = None
                else:
                    msg = plan.send(last_result)
            except StopIteration:
                break

            try:
                func = self.function_map[msg.command]
                last_result = yield from func(msg)

            except Exception as e:
                _exception = e

    @asyncio.coroutine
    def _print(self, msg):
        print(msg.obj)

    @asyncio.coroutine
    def _sum(self, msg):
        return sum(msg.args)

RE = RE_v4()
RE(safe_add_plan(2, 3))
