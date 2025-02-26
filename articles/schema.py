import strawberry
from typing import Collection, List, Optional

from articles.types.article_comments import CommentType
from articles.types.collection import CollectionType
from .types.article import ArticleType
from articles.models import Article, ArticleComment, UserArticlesVisitHistory, Collection
from django.core.exceptions import ObjectDoesNotExist


@strawberry.type
class Query:
    @strawberry.field
    def articles(self, info) -> List[ArticleType]:
        return Article.objects.all()

    @strawberry.field
    def article(self, info, slug: str) -> ArticleType:
        article = Article.objects.get(slug=slug)

        # Increment the article views
        article.views += 1
        article.save()

        # Save the user visit history
        if info.context.request.user.is_authenticated:
            try:
                visit = UserArticlesVisitHistory.objects.get(
                    user=info.context.request.user, article=article
                )
                visit.visit_count += 1
                visit.save()
            except ObjectDoesNotExist:
                UserArticlesVisitHistory.objects.create(
                    user=info.context.request.user, article=article
                )

        return article

    @strawberry.field
    def collection(self, info, id: int) -> CollectionType:
        return Collection.objects.get(id=id)

    # @strawberry.field
    # def collections(self, info,number: int, username: Optional[str] = None, last_id: Optional[str] = None) -> List[CollectionType]:



@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_article(
        self, info, title: Optional[str], content: Optional[str]
    ) -> ArticleType:
        author = info.context.request.user
        if not author.is_authenticated:
            raise Exception("You must be logged")
        article = Article.objects.create(title=title, content=content, author=author)
        return article

    @strawberry.mutation
    def update_article(
        self,
        info,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ArticleType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")
        article = Article.objects.get(slug=slug)

        # Check if the user is the owner of the article
        if article.author != info.context.request.user:
            raise Exception("You Can't update Someone else's article")
        if title:
            article.title = title
        if content:
            article.content = content
        article.save()
        return article

    @strawberry.mutation
    def delete_article(self, info, slug: str) -> bool:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        try:
            article = Article.objects.get(slug=slug)

            # Check if the user is the owner of the article
            if article.author != info.context.request.user:
                raise Exception("You Can't delete Someone else's article")
            article.delete()
            return True
        except ObjectDoesNotExist:
            return False

    @strawberry.mutation
    def create_comment(
        self, info, article_slug: str, content: str, parent_id: Optional[int] = None
    ) -> CommentType:
        user = info.context.request.user
        if not user.is_authenticated:
            raise Exception("You must be logged")

        article = Article.objects.get(slug=article_slug)
        parent = None
        if parent_id:
            parent = ArticleComment.objects.get(id=parent_id)
        comment = ArticleComment.objects.create(
            article=article,
            user=info.context.request.user,
            content=content,
            parent=parent,
        )
        return comment

    @strawberry.mutation
    def update_comment(self, info, id: int, content: str) -> CommentType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        comment = ArticleComment.objects.get(id=id)

        # Check if the user is the owner of the comment
        if comment.user != info.context.request.user:
            raise Exception("You Can't update Someone else's comment")

        comment.content = content
        comment.save()
        return comment

    @strawberry.mutation
    def delete_comment(self, info, id: int) -> bool:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        try:
            comment = ArticleComment.objects.get(id=id)

            # Check if the user is the owner of the comment
            if comment.user != info.context.request.user:
                raise Exception("You Can't delete Someone else's comment")
            comment.delete()
            return True
        except ObjectDoesNotExist:
            return False

    @strawberry.mutation
    def toggle_article_like(self, info, slug: str) -> ArticleType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        article = Article.objects.get(slug=slug)
        if article.likes.filter(id=info.context.request.user.id).exists():
            article.likes.remove(info.context.request.user)
        else:
            article.likes.add(info.context.request.user)
        return article

    @strawberry.mutation
    def toggle_Comment_like(self, info, id: int) -> CommentType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        comment = ArticleComment.objects.get(id=id)
        if comment.likes.filter(id=info.context.request.user.id).exists():
            comment.likes.remove(info.context.request.user)
        else:
            comment.likes.add(info.context.request.user)
        return comment

    @strawberry.mutation
    def create_collection(self, info, name: str, is_public: bool) -> CollectionType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")
        collection = Collection.objects.create(
            name=name, user=info.context.request.user, is_public=is_public
        )
        return collection

    @strawberry.mutation
    def update_collection(
        self, info, id: int, is_public: Optional[bool] = None, name: Optional[str] = None, description: Optional[str] = None
    ) -> CollectionType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")
        collection = Collection.objects.get(id=id)
        if collection.user != info.context.request.user:
            raise Exception("You Can't update Someone else's collection")

        if name:
            collection.name = name
        if description:
            collection.description = description

        if is_public is not None:
            collection.is_public = is_public

        collection.save()
        return collection

    @strawberry.mutation
    def delete_collection(self, info, id: int) -> bool:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        try:
            collection = Collection.objects.get(id=id)

            # Check if the user is the owner of the collection
            if collection.user != info.context.request.user:
                raise Exception("You Can't delete Someone else's collection")
            collection.delete()
            return True
        except ObjectDoesNotExist:
            return False

    @strawberry.mutation
    def add_article_to_collection(
        self, info, article_slug: str, collection_id: int
    ) -> CollectionType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.user != info.context.request.user:
                raise Exception("You Can't add articles to Someone else's collection")
            article = Article.objects.get(slug=article_slug)
            collection.articles.add(article)
            return collection
        except ObjectDoesNotExist:
            raise Exception("Collection or Article does not exist")
