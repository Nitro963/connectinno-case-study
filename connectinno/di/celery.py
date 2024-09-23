import functools

from dishka.integrations.base import wrap_injection

from celery import current_app, Task
from dishka import Scope


def inject(func):
    wrapper = wrap_injection(
        func=func,
        is_async=False,
        remove_depends=False,
        additional_params=[],
        container_getter=lambda _, kwargs: kwargs.get('_dishka_container', None),
    )
    functools.update_wrapper(wrapper, func)
    return wrapper


def with_di_container(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        task = args[0]
        if not isinstance(task, Task):
            task = None
        with current_app.dishka_container(scope=Scope.REQUEST) as container:
            if task:
                task.dishka_container = container
            return func(*args, _dishka_container=container, **kwargs)

    return wrapper
