from __future__ import annotations

import strawberry
import strawberry_django
from strawberry import LazyType
from strawberry.types import Info
from typing import List, Optional

from users.types.user import UserType
from notebook.models import Notebook


@strawberry_django.type(Notebook)
class NotebookType:
    id: strawberry.ID
    slug: str
    name: str
    overview: str | None
    created_at: str
    user: UserType

    @strawberry.field
    def cover(self, info: Info) -> str:
        if self.cover:
            return self.cover.url
        return ""
    
    @strawberry.field
    def pages_count(self, info: Info) -> int:
        """Return the number of pages in this notebook"""
        from notebook.models import Page
        return Page.objects.filter(notebook=self).count()
    
    @strawberry.field
    def has_pages(self, info: Info) -> bool:
        """Check if notebook has any pages"""
        from notebook.models import Page
        return Page.objects.filter(notebook=self).exists()
    
    @strawberry.field
    def root_pages(self, info: Info) -> List[LazyType["PageType", "notebook.types.page"]]:
        """Return root pages (no parent) ordered by index"""
        from notebook.models import Page
        return list(Page.objects.filter(notebook=self, parent=None).order_by('index'))
    
    @strawberry.field
    def index_page(self, info: Info) -> Optional[LazyType["PageType", "notebook.types.page"]]:
        """Return the index page (first root page)"""
        return self.get_index_page()