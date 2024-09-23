import abc


class INotifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def publish(self, recipients, content):
        pass

    @abc.abstractmethod
    async def apublish(self, recipients, content):
        pass
