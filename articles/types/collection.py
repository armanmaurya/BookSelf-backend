from typing import List
import strawberry
import strawberry_django
from articles.models import Collection, CollectionItem
from articles.types.article import ArticleType

@strawberry_django.type(Collection)
class CollectionType:
    id: int
    name: str
    description: str
    created_at: str
    updated_at: str
    is_public: bool

    @strawberry.field
    def retrieve_items(self, info) -> List["CollectionItemType"]:
        return self.items.all()

    @strawberry.field
    def is_added(self, info, article_slug: str) -> bool:
        return CollectionItem.objects.filter(collection=self, article__slug=article_slug).exists()
    
    @strawberry.field
    def is_self(self, info) -> bool:
        user = info.context.request.user
        if user.is_authenticated:
            return self.user == user
        return False
    
    @strawberry.field
    def items_count(self) -> int:
        return self.items.count()


@strawberry_django.type(CollectionItem)
class CollectionItemType:
    id: int
    article: ArticleType
    order: int
    date_added: str