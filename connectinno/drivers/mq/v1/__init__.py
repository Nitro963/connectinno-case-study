from faststream.rabbit import RabbitRouter

from .misc import router as misc_router

router = RabbitRouter()
router.include_router(misc_router)
