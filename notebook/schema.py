import strawberry
from strawberry.exceptions import StrawberryGraphQLError

from notebook.types.notebook import NotebookType
from notebook.models import Notebook

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_notebook(self, info, name: str, overview: str | None = None) -> NotebookType:
        user = info.context.request.user
        if not user.is_authenticated:
            return StrawberryGraphQLError("You must be logged in to create a notebook.")
        
        notebook = Notebook(name=name, overview=overview, user=user)
        notebook.save()
        return notebook

    @strawberry.mutation
    def update_notebook(self, info, notebook_id: str, name: str, overview: str | None = None) -> NotebookType:
        user = info.context.request.user
        if not user.is_authenticated:
            return StrawberryGraphQLError("You must be logged in to update a notebook.")

        try:
            notebook = Notebook.objects.get(id=notebook_id, user=user)
        except Notebook.DoesNotExist:
            return StrawberryGraphQLError("Notebook not found.")

        notebook.name = name
        notebook.overview = overview
        notebook.save()
        return notebook
    

    @strawberry.mutation
    def delete_notebook(self, info, notebook_id: str) -> bool:
        user = info.context.request.user
        if not user.is_authenticated:
            raise StrawberryGraphQLError("You must be logged in to delete a notebook.")

        try:
            notebook = Notebook.objects.get(id=notebook_id, user=user)
        except Notebook.DoesNotExist:
            raise StrawberryGraphQLError("Notebook not found.")

        notebook.delete()
        return True
