from celery import shared_task


@shared_task
def hello_world():
    return 'Hello, World'


@shared_task
def add(x, y):
    return x + y


@shared_task
def tsum(numbers):
    return sum(numbers)


__all__ = [
    'hello_world',
    'add',
    'tsum',
]
