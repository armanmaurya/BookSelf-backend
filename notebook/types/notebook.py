from notebook.models import Notebook
from typing import List
import strawberry_django
import strawberry
from users.types.user import UserType

@strawberry_django.type(Notebook)
class NotebookType:
    slug: str
    name: str
    overview: str | None
    created_at: str
    user: UserType
    
    @strawberry.field
    def cover_url(self) -> str:
        if self.cover:
            return self.cover.url
        return ""