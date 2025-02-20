import strawberry
from typing import List, Optional
from .types.article import ArticleType
from articles.models import Article
from django.core.exceptions import ObjectDoesNotExist


@strawberry.type
class Query:
    @strawberry.field
    def articles(self, info) -> List[ArticleType]:
        return Article.objects.all()

    @strawberry.field
    def article(self, info, slug: str) -> ArticleType:
        return Article.objects.get(slug=slug)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_article(
        self, info, title: Optional[str], content: Optional[str]
    ) -> ArticleType:
        author = info.context.request.user
        article = Article.objects.create(title=title, content=content, author=author)
        return article
    
    @strawberry.mutation
    def update_article(
        self, info, slug: str, title: Optional[str], content: Optional[str]
    ) -> ArticleType:
        article = Article.objects.get(slug=slug)
        if title:
            article.title = title
        if content:
            article.content = content
        article.save()
        return article
    
    @strawberry.mutation
    def delete_article(self, info, slug: str) -> bool:
        try:
            article = Article.objects.get(slug=slug)
            article.delete()
            return True
        except ObjectDoesNotExist: 
            return False
