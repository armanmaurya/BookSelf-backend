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

    @strawberry.field
    def items(self, info) -> List["CollectionItemType"]:
        return self.items.all()


@strawberry_django.type(CollectionItem)
class CollectionItemType:
    id: int
    article: ArticleType
    order: int
    date_added: str