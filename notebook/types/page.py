from __future__ import annotations

import strawberry
import strawberry_django
from strawberry import LazyType
from strawberry.types import Info
from typing import List, Optional

from users.types.user import UserType
from notebook.models import Page


@strawberry_django.type(Page)
class PageType:
    id: strawberry.ID
    slug: str
    title: str
    content: str | None
    created_at: str
    updated_at: str
    index: int
    has_children: bool

    @strawberry.field
    def notebook(self, info: Info) -> LazyType["NotebookType", "notebook.types.notebook"]:
        return self.notebook
    
    @strawberry.field
    def parent(self, info: Info) -> Optional[LazyType["PageType", "notebook.types.page"]]:
        return self.parent
    
    @strawberry.field
    def children(self, info: Info) -> List[LazyType["PageType", "notebook.types.page"]]:
        """Return child pages ordered by index"""
        return list(self.children.all().order_by('index'))
    
    @strawberry.field
    def siblings(self, info: Info) -> List[LazyType["PageType", "notebook.types.page"]]:
        """Return sibling pages (same parent) ordered by index"""
        from notebook.models import Page
        return list(Page.objects.filter(
            notebook=self.notebook,
            parent=self.parent
        ).exclude(id=self.id).order_by('index'))
    
    @strawberry.field
    def path(self, info: Info) -> str:
        """Return the full path of this page"""
        path_parts = []
        current_page = self
        
        # Build path from current page up to root
        while current_page:
            path_parts.append(current_page.title)
            current_page = current_page.parent
        
        # Reverse to get root-to-leaf order
        path_parts.reverse()
        
        # Join with slashes
        return "/" + "/".join(path_parts) if path_parts else "/"