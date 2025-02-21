import strawberry
import strawberry_django
from .user import UserType
from typing import Optional

@strawberry.type
class GoogleAuthType:
    user: Optional[UserType]
    is_created: bool
