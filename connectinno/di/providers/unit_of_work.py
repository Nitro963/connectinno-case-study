from dishka import Provider, provide, Scope, alias

from connectinno.app.unit_of_work import AlchemyUnitOfWork, AbstractUnitOfWork
from sqlalchemy.orm import Session, sessionmaker


class UnitOfWorkProvider(Provider):
    uow = provide(AlchemyUnitOfWork, scope=Scope.REQUEST)

    abstract_uow = alias(source=AlchemyUnitOfWork, provides=AbstractUnitOfWork)

    @provide(scope=Scope.REQUEST)
    def get_session(self, factory: sessionmaker) -> Session:
        return factory()
