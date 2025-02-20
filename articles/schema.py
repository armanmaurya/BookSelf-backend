import strawberry
from typing import List
from .types.article import ArticleType
from articles.models import Article

@strawberry.type
class Query:
    @strawberry.field
    def articles(self, info) -> List[ArticleType]:
        return Article.objects.all()
    
    @strawberry.field
    def article(self, info, slug: str) -> ArticleType:
        return Article.objects.get(slug=slug)