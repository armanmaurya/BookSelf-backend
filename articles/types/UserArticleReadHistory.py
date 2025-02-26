import strawberry
import strawberry_django

from articles.models import UserArticlesVisitHistory
from articles.types.article import ArticleType

@strawberry_django.type(UserArticlesVisitHistory)
class UserArticleReadHistoryType:
    id: int
    article: ArticleType
    visit_count: int
    last_visited: str
