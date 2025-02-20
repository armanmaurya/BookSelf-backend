import strawberry
from users.schema import Query as UserQuery
from articles.schema import Query as ArticleQuery

@strawberry.type
class Query(UserQuery, ArticleQuery):
    pass

schema = strawberry.Schema(query=Query)