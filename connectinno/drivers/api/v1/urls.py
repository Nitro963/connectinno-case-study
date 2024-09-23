from fastapi import APIRouter

from corelib.web.constants import API_V1_STR
from . import misc
from . import image

router = APIRouter(prefix=API_V1_STR)
router.include_router(misc.router, tags=['Miscellaneous'], prefix='/misc')
router.include_router(image.router, tags=['Images'])
