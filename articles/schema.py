import strawberry
from typing import Collection, List, Optional, Union, Annotated
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.types import Info
from strawberry.file_uploads import Upload

from articles.types.article_comments import CommentType
from articles.types.collection import CollectionType
from .types.article import ArticleType
from articles.models import (
    Article,
    ArticleComment,
    UserArticlesVisitHistory,
    Collection,
    CollectionItem,
    ArticleDraft,
)
from django.core.exceptions import ObjectDoesNotExist
from articles.types.draft_article import ArticleDraftType
from graphql import GraphQLError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


@strawberry.type
class PermissionError:
    message: str

    def __str__(self) -> str:
        return self.message


@strawberry.type
class AuthencatationError:
    message: str

    def __str__(self) -> str:
        return self.message


@strawberry.type
class DraftArticleList:
    articles: List[ArticleDraftType]  # ✅ Wrap the list inside an object


Response = Annotated[
    Union[ArticleDraftType, PermissionError],
    strawberry.union("Response"),
]


@strawberry.type
class Query:
    @strawberry.field
    def articles(
        self,
        info: Info,
        username: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[ArticleType]:
        # Build the filter dictionary
        filter_dict = {"status": Article.PUBLISHED}

        # If the user is requesting their own articles, return all the articles
        if (
            info.context.request.user.is_authenticated
            and info.context.request.user.username == username
        ):
            filter_dict = {}
        if username:
            filter_dict["author__username"] = username

        qs = Article.objects.filter(**filter_dict)
        if query:
            qs = qs.filter(title__icontains=query) | qs.filter(content__icontains=query)
        return qs

    # TO:DO = Need to fix the only published article can be accesses
    @strawberry.field
    def article(self, info, slug: str) -> ArticleType:
        id = slug.split("-")[-1]

        article = Article.objects.get(id=id)

        # Save the user visit history
        if info.context.request.user.is_authenticated:
            visit, created = UserArticlesVisitHistory.objects.get_or_create(
                user=info.context.request.user, article=article
            )
            if not created:
                visit.visit_count += 1
                visit.save()

        # Increment the article views
        article.views += 1
        article.save()

        return article

    @strawberry.field
    def draft_article(
        self, info: Info, slug: str
    ) -> Union[ArticleDraftType, PermissionError]:
        try:
            id = slug.split("-")[-1]
            draft_article = ArticleDraft.objects.get(article__id=id)

            if info.context.request.user != draft_article.article.author:
                return PermissionError(
                    message="You don't have permission to view this draft."
                )

            return draft_article

        except ObjectDoesNotExist:
            raise GraphQLError("Draft doesn't exist.")

    @strawberry.field
    def draft_articles(
        self, info: Info
    ) -> Union[AuthencatationError, DraftArticleList]:
        if not info.context.request.user.is_authenticated:
            return AuthencatationError(message="You must be logged in to view drafts.")
        drafts = ArticleDraft.objects.filter(
            article__author=info.context.request.user,
            article__status=Article.DRAFT
        ).order_by("-updated_at")
        return DraftArticleList(articles=drafts)  # ✅ Return wrapped list

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
    ) -> ArticleDraftType:
        author = info.context.request.user
        if not author.is_authenticated:
            raise Exception("You must be logged")
        article = Article.objects.create(author=author)
        draftArticle = ArticleDraft.objects.create(
            article=article, title=title, content=content
        )
        return draftArticle

    @strawberry.mutation
    def update_article(
        self,
        info,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        image: Optional[Upload] = None,
    ) -> ArticleType:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")
        article = Article.objects.get(slug=slug)
        draftArticle = article.draft
        # Print everything
        print("Title:", title)
        print("Content:", content)
        print("Image:", image)
        # Check if the user is the owner of the article
        if article.author != info.context.request.user:
            raise Exception("You Can't update Someone else's article")
        if title:
            draftArticle.title = title
        if content:
            draftArticle.content = content
        if image:
            file_content = ContentFile(image.read())
            file_name = default_storage.save(f"uploads/{image.name}", file_content)
            draftArticle.image.save(image.filename, image.file, save=True)
            draftArticle.image = file_name
        draftArticle.save()
        return article

    @strawberry.mutation
    def publish_article(self, info: Info, slug: str) -> str:
        try:
            article = Article.objects.get(slug=slug)
            if info.context.request.user != article.author:
                raise Exception("You Can't Publish Other Article")

            draftArticle = article.draft

            article.title = draftArticle.title
            article.content = draftArticle.content
            article.status = Article.PUBLISHED
            article.save()
            # print(article.slug)
            return article.slug
        except:
            return ""

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
    ) -> Union[CommentType, AuthencatationError]:
        user = info.context.request.user
        if not user.is_authenticated:
            return AuthencatationError(message="You must be logged in to comment.")

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
        self,
        info,
        id: int,
        is_public: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
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
    def toggle_add_article_to_collection(
        self, info, article_slug: str, collection_id: int
    ) -> bool:
        if not info.context.request.user.is_authenticated:
            raise Exception("You must be logged")

        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.user != info.context.request.user:
                raise Exception("You can't modify Someone else's collection")
            article = Article.objects.get(slug=article_slug)
            collection_item, created = CollectionItem.objects.get_or_create(
                collection=collection, article=article
            )
            if not created:
                collection_item.delete()
                return False
            return True
        except ObjectDoesNotExist:
            raise Exception("Collection or Article does not exist")
