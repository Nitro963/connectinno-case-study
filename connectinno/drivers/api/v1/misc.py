from fastapi import APIRouter

router = APIRouter()


@router.post('/health', status_code=204)
def health():
    return


@router.post('/ping', response_model=str)
def ping():
    return 'pong'
