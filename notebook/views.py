from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from .serializers import NotebookFormSerializer, NotebookGetSerializer, PageCreateFormSerializer, PageSerializer, PageUpdateFormSerializer, NotebookCoverSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notebook, Page
from .utils import get_notebook_from_slug

from users.models import CustomUser as User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def getNotebookPage(notebook, page_path):
    if page_path is None:
        return None
    path = page_path.split("/")
    print(path)
    page = None
    for p in path:
        if (p == ""):
            continue
        page = Page.objects.get(notebook=notebook, parent=page, slug=p)
    return page


class NoteBookPageView(APIView):
    authentication_classes = [SessionAuthentication]

    def get_children(self, notebook, path):
        page = getNotebookPage(notebook, path)
        all_child_pages = Page.objects.filter(notebook=notebook, parent=page)
        serializer = PageSerializer(all_child_pages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, username=None, slug=None, path=None):
        isChildrens = request.query_params.get("children")
        isIndex = request.query_params.get("index")
        if slug and username and path and isChildrens is not None:
            try:
                notebook = self.get_notebook(username, slug)
                return self.get_children(notebook, path)
            except Page.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data=[]
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        elif slug and username and path and isIndex is not None:
            try:
                notebook = self.get_notebook(username, slug)
                index_page = notebook.get_index_page()
                if index_page:
                    serializer = PageSerializer(index_page)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(status=status.HTTP_404_NOT_FOUND, data={"error": "Index page not found"})
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
        elif slug and username and path:
            try:
                page = self.get_page(username, slug, path)
                serializer = PageSerializer(page)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Page.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "Page not found"}
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        elif slug and username and isChildrens is not None:
            try:
                notebook = self.get_notebook(username, slug)
                return self.get_children(notebook, None)
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        elif slug and username:
            try:
                notebook = self.get_notebook(username, slug)
                index_page = notebook.get_index_page()
                if index_page:
                    serializer = PageSerializer(index_page)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(status=status.HTTP_404_NOT_FOUND, data={"error": "Index page not found"})
                # serializer = NotebookGetSerializer(notebook)
                # data = serializer.data
                # index_page = notebook.get_index_page()
                # if index_page:
                #     data["index_page"] = index_page.slug
                # data["index_page"] = notebook.get_index_page().slug
                # return Response(data, status=status.HTTP_200_OK)
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        elif username:
            try:
                user = User.objects.get(username=username)
                notebooks = Notebook.objects.filter(user=user)
                notebook_serializer = NotebookGetSerializer(notebooks, many=True)
                return Response(notebook_serializer.data, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"})
        
        all_notebooks = Notebook.objects.all()
        serializer = NotebookGetSerializer(all_notebooks, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @permission_classes([IsAuthenticated])
    @csrf_exempt
    def post(self, request, username=None, slug=None, path=None):
        """
        {
            title: "Page title",
        }
        """
        if username and slug and path:
            try:
                user = User.objects.get(username=username)
                notebook = Notebook.objects.get(slug=slug, user=user)
                parent = getNotebookPage(notebook, path)

                currentPage = Page.objects.create(
                    title=request.data["title"],
                    parent=parent,
                    notebook=notebook
                )
                serializer = PageSerializer(currentPage)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Page.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "Page not found"}
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
            except ValueError as e:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)}
                )
        if username and slug:
            try:
                user = User.objects.get(username=username)
                notebook = Notebook.objects.get(slug=slug, user=user)
                parent = None
                if "parent" in request.data:
                    parent_path = request.data["parent"]
                    parent = getNotebookPage(notebook, parent_path)
                currentPage = Page.objects.create(
                    title=request.data["title"],
                    parent=parent,
                    notebook=notebook
                )
                serializer = PageSerializer(currentPage)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)}
                )
        elif username:
            try:
                user = User.objects.get(username=username)
                createdNotebook = Notebook.objects.create(
                    name=request.data["name"],
                    user=user
                )
                serializer = NotebookGetSerializer(createdNotebook)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except KeyError:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Name is required"})
            except ValueError as e:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)}
                )

    @permission_classes([IsAuthenticated])
    def patch(self, request, username=None, slug=None, path=None):
        """
        {
            "title": "New title", (optional)
            "content": "New content" (optional)
        }
        """
        if slug and username and path:
            try:
                page = self.get_page(username, slug, path)
                serializer = PageUpdateFormSerializer(page, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Page.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "Page not found"}
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        elif slug and username:
            try:
                notebook = self.get_notebook(username, slug)
                serializer = NotebookGetSerializer(notebook)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        return Response(status=status.HTTP_404_NOT_FOUND)


    # @permission_classes([IsAuthenticated])
    def delete(self, request, username=None, slug=None, path=None):
        if username and slug and path:
            try:
                page = self.get_page(username, slug, path)
                page.delete()
            except Page.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "Page not found"}
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                data={"message": "Page deleted successfully"},
            )

        elif username and slug:
            try:
                notebook = self.get_notebook(username, slug)
                notebook.delete
                return Response(
                    status=status.HTTP_204_NO_CONTENT,
                    data={"message": "Notebook deleted successfully"},
                )
            except Notebook.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": "Notebook not found"},
                )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": "User not found"}
                )
        return Response(status=status.HTTP_404_NOT_FOUND)

    def get_page(self, username, slug, path):
        notebook = self.get_notebook(username, slug)
        page = getNotebookPage(notebook, path)
        return page

    def get_notebook(self, username, slug):
        user = User.objects.get(username=username)
        notebook = Notebook.objects.get(slug=slug, user=user)
        return notebook


class NoteBookView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        all_notebooks = Notebook.objects.all()
        serializer = NotebookGetSerializer(all_notebooks, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @permission_classes([IsAuthenticated])
    def post(self, request):
        """
        {
            "name": "Notebook name"
        }
        """
        try:
            createdNotebook = Notebook.objects.create(
                name=request.data["name"],
                user=request.user
            )
            serializer = NotebookGetSerializer(createdNotebook)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Name is required"})
        except ValueError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)}
            )

    @permission_classes([IsAuthenticated])
    def patch(self, request):
        """
        {
            "name": "New name"
        }
        """
        try:
            notebook = Notebook.objects.get(slug=request.data["slug"], user=request.user)
            serializer = NotebookFormSerializer(notebook, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Notebook.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Notebook not found"},
            )

    @permission_classes([IsAuthenticated])
    def delete(self, request):
        try:
            notebook = Notebook.objects.get(slug=request.data["slug"], user=request.user)
            notebook.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                data={"message": "Notebook deleted successfully"},
            )
        except Notebook.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Notebook not found"},
            )


@csrf_exempt
def manageNotebookCover(request, slug):
    # Check if the request method is valid
    if request.method not in ["POST", "DELETE"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    # Get notebook by slug
    notebook = get_notebook_from_slug(slug)
    if notebook is None:
        return JsonResponse({"error": "Notebook not found"}, status=404)

    # Validate that the notebook belongs to the user
    if notebook.user != user:
        return JsonResponse({"error": "You are not the owner of this notebook"}, status=403)

    if request.method == "POST":
        # Check if image is provided
        if not request.FILES.get("image"):
            return JsonResponse({"error": "No cover image provided"}, status=400)

        # Update the notebook with the new cover
        notebook.cover = request.FILES["image"]
        notebook.save()
        
        return JsonResponse({
            "message": "Cover uploaded successfully",
            "cover_url": notebook.cover.url if notebook.cover else None
        }, status=200)
    
    elif request.method == "DELETE":
        # Delete the cover
        if notebook.cover:
            notebook.cover.delete(save=False)  # Delete file from storage
            notebook.cover = None
            notebook.save()
            return JsonResponse({"message": "Cover deleted successfully"}, status=200)
        else:
            return JsonResponse({"error": "No cover to delete"}, status=400)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)