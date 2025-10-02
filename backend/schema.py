import strawberry
from users.schema import Query as UserQuery, Mutation as UserMutation
from articles.schema import Query as ArticleQuery, Mutation as ArticleMutation
from notebook.schema import NotebookQuery, NotebookMutation

@strawberry.type
class Query(UserQuery, ArticleQuery, NotebookQuery):
    pass

@strawberry.type
class Mutation(ArticleMutation, UserMutation, NotebookMutation):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)