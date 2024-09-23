from fastapi import HTTPException
from starlette import status


async def does_not_exists_exception_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=','.join(exc.args) or 'not_found'
    )


__all__ = ['does_not_exists_exception_handler']
