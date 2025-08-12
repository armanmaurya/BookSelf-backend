from enum import Enum
import strawberry


@strawberry.enum
class ArticleSortBy(Enum):
    LATEST = "latest"
    POPULAR = "popular"
