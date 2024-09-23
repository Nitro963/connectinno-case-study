import abc
from time import time

from celery import bootsteps
from celery.bootsteps import ConsumerStep, StepType


class Autoscaler(bootsteps.StartStopStep):
    requires = ('celery.worker.autoscaler:Autoscaler',)


class DeadlockDetection(bootsteps.StartStopStep):
    requires = {'celery.worker.components:Timer'}

    def __init__(self, worker, parent, deadlock_timeout=3600, **kwargs):
        super().__init__(parent, **kwargs)
        self.timeout = deadlock_timeout
        self.requests = []
        self.tref = None

    def start(self, worker):
        # run every 30 seconds.
        self.tref = worker.timer.call_repeatedly(
            30.0,
            self.detect,
            (worker,),
            priority=10,
        )

    def stop(self, worker):
        if self.tref:
            self.tref.cancel()
            self.tref = None

    def detect(self, worker):
        # update active requests
        for req in worker.active_requests:
            if req.time_start and time() - req.time_start > self.timeout:
                raise SystemExit()


class AbstractStep(StepType, abc.ABCMeta):
    pass


class RatelimitStepBase(ConsumerStep, metaclass=AbstractStep):
    """Rate limit tasks based on the number of workers in the
    cluster."""

    requires = {'celery.worker.consumer.gossip:Gossip'}

    @property
    @abc.abstractmethod
    def rate_limited_tasks(self) -> dict[str, float]:
        pass

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.tasks = []
        self.last_size = None

    def start(self, c):
        c.gossip.on.node_join.add(self.on_cluster_size_change)
        c.gossip.on.node_leave.add(self.on_cluster_size_change)
        c.gossip.on.node_lost.add(self.on_node_lost)

        self.tasks = [
            self.app.tasks[t]
            for t in self.rate_limited_tasks.keys()  # noqa
        ]
        self.last_size = None

    def on_cluster_size_change(self, c):
        cluster_size = len(list(c.gossip.state.alive_workers()))
        if cluster_size != self.last_size:
            for task, rate_limit in zip(self.tasks, self.rate_limited_tasks.values()):
                task.mx_batch = rate_limit / cluster_size
            c.reset_rate_limits()
            self.last_size = cluster_size

    def on_node_lost(self, c):
        # may have processed heartbeat too late, so wake up soon
        # in order to see if the worker recovered.
        c.timer.call_after(10.0, self.on_cluster_size_change)
