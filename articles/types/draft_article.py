import strawberry
import strawberry_django
from typing import Optional
from strawberry.types import Info
from articles.models import ArticleDraft
from articles.types.article import ArticleType

@strawberry_django.type(ArticleDraft)
class ArticleDraftType:
    article: ArticleType
    title: str | None
    content: str | None
    updated_at: Optional[str]