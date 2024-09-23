from fastapi import HTTPException
from starlette import status

HTTP_422_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='unprocessable_entity'
)
HTTP_404_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail='not_found'
)
HTTP_504_GATEWAY_TIMEOUT_EXCEPTION = HTTPException(
    status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='gateway_timeout'
)
HTTP_501_NOT_IMPLEMENTED_EXCEPTION = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail='not_implemented'
)

HTTP_503_SERVICE_UNAVAILABLE_EXCEPTION = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='service_unavailable'
)
API_V1_STR = '/api/v1'
