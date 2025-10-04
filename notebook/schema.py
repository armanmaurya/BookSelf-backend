import strawberry
from typing import List, Optional, Union, Annotated
from strawberry.types import Info
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from notebook.models import Notebook, Page
from notebook.types import NotebookType, PageType
from notebook.enums import NotebookSortBy


@strawberry.type
class NotebookPermissionError:
    message: str

    def __str__(self) -> str:
        return self.message


@strawberry.type
class NotebookAuthenticationError:
    message: str

    def __str__(self) -> str:
        return self.message


@strawberry.type
class NotebookList:
    notebooks: List[NotebookType]  # Wrap the list inside an object


@strawberry.type
class NotebookDeleteSuccess:
    success: bool
    message: str


@strawberry.type
class NotebookQuery:
    @strawberry.field
    def notebooks(
        self,
        info: Info,
        username: Optional[str] = None,
        query: Optional[str] = None,
        sort_by: Optional[NotebookSortBy] = None,
        limit: int = 20,
        last_id: Optional[int] = None,
    ) -> List[NotebookType]:
        """Get notebooks with optional filtering and sorting"""
        filter_dict = {}
        
        # Filter by username if provided
        if username:
            filter_dict["user__username"] = username
        
        # If user is requesting their own notebooks, show all
        # Otherwise, only show public ones (if you add is_public field later)
        if (
            info.context.request.user.is_authenticated
            and username == info.context.request.user.username
        ):
            # User can see all their own notebooks
            pass
        
        # Add pagination filter
        if last_id:
            filter_dict["id__lt"] = last_id
        
        qs = Notebook.objects.select_related('user').filter(**filter_dict)
        
        # Apply search query
        if query:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=query) | Q(overview__icontains=query))
        
        # Apply sorting
        if sort_by == NotebookSortBy.LATEST:
            qs = qs.order_by("-created_at", "-id")  # Add id for consistent ordering
        elif sort_by == NotebookSortBy.OLDEST:
            qs = qs.order_by("created_at", "id")
        elif sort_by == NotebookSortBy.NAME:
            qs = qs.order_by("name", "-id")  # Add id as secondary sort
        else:
            # Default sorting (latest)
            qs = qs.order_by("-created_at", "-id")
        
        # Apply limit
        return list(qs[:limit])

    @strawberry.field
    def notebook(self, info: Info, slug: str) -> NotebookType:
        """Get a single notebook by slug"""
        try:
            # Extract ID from slug (assuming slug format: name-id)
            notebook_id = slug.split("-")[-1]
            notebook = Notebook.objects.select_related('user').get(id=notebook_id)
            return notebook
        except (Notebook.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Notebook with slug '{slug}' not found")

    @strawberry.field
    def my_notebooks(
        self, 
        info: Info, 
        limit: int = 20,
        last_id: Optional[int] = None,
    ) -> Union[NotebookList, NotebookAuthenticationError]:
        """Get current user's notebooks"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to view your notebooks")
        
        filter_dict = {"user": info.context.request.user}
        
        # Add pagination filter
        if last_id:
            filter_dict["id__lt"] = last_id
        
        notebooks = Notebook.objects.select_related('user').filter(
            **filter_dict
        ).order_by("-created_at", "-id")[:limit]
        
        return list(notebooks)

    @strawberry.field
    def pages(
        self,
        info: Info,
        notebook_slug: str,
        parent_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[PageType]:
        """Get pages from a notebook, optionally filtered by parent"""
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Build filter
            filter_dict = {"notebook": notebook}
            if parent_id:
                filter_dict["parent_id"] = parent_id
            else:
                filter_dict["parent"] = None  # Root pages
            
            pages = Page.objects.filter(**filter_dict).order_by('index')[:limit]
            return list(pages)
            
        except (Notebook.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Notebook with slug '{notebook_slug}' not found")

    @strawberry.field
    def page(self, info: Info, notebook_slug: str, page_path: str) -> PageType:
        """Get a specific page by path within a notebook"""
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Handle root path
            if not page_path or page_path == "":
                # Return the first root page or raise error if no pages exist
                try:
                    page = Page.objects.filter(notebook=notebook, parent=None).first()
                    if page is None:
                        raise GraphQLError(f"No pages found in notebook '{notebook_slug}'")
                    return page
                except Page.DoesNotExist:
                    raise GraphQLError(f"No pages found in notebook '{notebook_slug}'")
            
            # Navigate to page using path
            path_parts = [p for p in page_path.split("/") if p]
            page = None
            
            for slug in path_parts:
                page = Page.objects.get(
                    notebook=notebook, 
                    parent=page, 
                    slug=slug
                )
            
            if page is None:
                raise GraphQLError(f"Page not found at path '{page_path}'")
            
            return page
            
        except (Notebook.DoesNotExist, Page.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Page not found at path '{page_path}' in notebook '{notebook_slug}'")

    @strawberry.field
    def sidebar_pages(
        self,
        info: Info,
        notebook_slug: str,
        active_page_path: Optional[str] = None,
    ) -> List[PageType]:
        """Get nested pages for sidebar navigation - returns root pages with their children expanded based on active path"""
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Get all root pages
            root_pages = list(Page.objects.filter(notebook=notebook, parent=None).order_by('index'))
            
            # Return root pages - the nested structure comes from PageType's children field
            # The frontend can use the active_page_path to determine which pages to expand
            return root_pages
            
        except (Notebook.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Notebook with slug '{notebook_slug}' not found")


@strawberry.type
class NotebookMutation:
    @strawberry.mutation
    def create_notebook(
        self, 
        info: Info, 
        name: str, 
        overview: Optional[str] = None
    ) -> Union[NotebookType, NotebookAuthenticationError]:
        """Create a new notebook"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to create a notebook")
        
        try:
            notebook = Notebook.objects.create(
                name=name,
                overview=overview or "",
                user=info.context.request.user
            )
            return notebook
        except Exception as e:
            raise GraphQLError(f"Error creating notebook: {str(e)}")

    @strawberry.mutation
    def update_notebook(
        self,
        info: Info,
        slug: str,
        name: Optional[str] = None,
        overview: Optional[str] = None,
    ) -> Union[NotebookType, NotebookAuthenticationError, NotebookPermissionError]:
        """Update an existing notebook"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to update a notebook")
        
        try:
            # Extract ID from slug
            notebook_id = slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to update this notebook")
            
            # Update fields if provided
            if name is not None:
                notebook.name = name
            if overview is not None:
                notebook.overview = overview
            
            notebook.save()
            return notebook
            
        except (Notebook.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Notebook with slug '{slug}' not found")
        except Exception as e:
            raise GraphQLError(f"Error updating notebook: {str(e)}")

    @strawberry.mutation
    def delete_notebook(
        self, 
        info: Info, 
        slug: str
    ) -> Union[NotebookDeleteSuccess, NotebookAuthenticationError, NotebookPermissionError]:
        """Delete a notebook"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to delete a notebook")
        
        try:
            # Extract ID from slug
            notebook_id = slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to delete this notebook")
            
            notebook.delete()
            return NotebookDeleteSuccess(success=True, message="Notebook deleted successfully")
            
        except (Notebook.DoesNotExist, ValueError, IndexError):
            raise GraphQLError(f"Notebook with slug '{slug}' not found")
        except Exception as e:
            raise GraphQLError(f"Error deleting notebook: {str(e)}")

    @strawberry.mutation
    def create_page(
        self,
        info: Info,
        notebook_slug: str,
        title: str,
        path: str,
    ) -> Union[PageType, NotebookAuthenticationError, NotebookPermissionError]:
        """Create a new page in a notebook with a specified path"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to create a page")
        
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to create pages in this notebook")
            
            # Parse the path to determine parent
            # Path represents the parent location, e.g., "/" = root, "/parent-page" = under parent-page
            parent = None
            if path and path != "/":
                # Remove leading/trailing slashes and split path
                path_parts = [p for p in path.strip("/").split("/") if p]
                
                # Navigate through the entire path to find the parent
                current_parent = None
                for slug_part in path_parts:
                    try:
                        current_parent = Page.objects.get(
                            notebook=notebook,
                            slug=slug_part,
                            parent=current_parent
                        )
                    except Page.DoesNotExist:
                        raise GraphQLError(f"Parent page with slug '{slug_part}' not found in path '{path}'")
                
                parent = current_parent
            
            # Create the page
            page = Page.objects.create(
                notebook=notebook,
                title=title,
                parent=parent
            )
            
            return page
            
        # except (Notebook.DoesNotExist, ValueError, IndexError):
        #     raise GraphQLError(f"Notebook with slug '{notebook_slug}' not found")
        except Exception as e:
            raise GraphQLError(f"Error creating page: {str(e)}")

    @strawberry.mutation
    def update_page(
        self,
        info: Info,
        notebook_slug: str,
        page_path: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        insert_after_page_id: Optional[int] = None,
        insert_before_page_id: Optional[int] = None,
        parent_path: Optional[str] = None,
    ) -> Union[PageType, NotebookAuthenticationError, NotebookPermissionError]:
        """Update an existing page using notebook slug and page path"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to update a page")
        
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to update this page")
            
            # Navigate to the page using path
            path_parts = [p for p in page_path.strip("/").split("/") if p]
            current_page = None
            
            for slug_part in path_parts:
                current_page = Page.objects.get(
                    notebook=notebook,
                    slug=slug_part,
                    parent=current_page
                )
            
            if current_page is None:
                raise GraphQLError(f"Page not found at path '{page_path}'")
            
            # Handle parent change if provided
            if parent_path is not None:
                new_parent = None
                if parent_path and parent_path != "/":
                    # Navigate to the new parent page
                    parent_parts = [p for p in parent_path.strip("/").split("/") if p]
                    current_parent = None
                    
                    for slug_part in parent_parts:
                        current_parent = Page.objects.get(
                            notebook=notebook,
                            slug=slug_part,
                            parent=current_parent
                        )
                    
                    new_parent = current_parent
                
                # Check if the new parent would create a circular reference
                if new_parent:
                    # Check if the new parent is a descendant of the current page
                    temp_parent = new_parent.parent
                    while temp_parent:
                        if temp_parent.id == current_page.id:
                            raise GraphQLError("Cannot move page: would create circular reference")
                        temp_parent = temp_parent.parent
                
                current_page.parent = new_parent
            
            # Update basic fields if provided
            if title is not None:
                current_page.title = title
            if content is not None:
                current_page.content = content
            
            # Save basic changes first
            current_page.save()
            
            # Handle reordering - only one positioning method can be used
            if insert_after_page_id is not None and insert_before_page_id is not None:
                raise GraphQLError("Cannot specify both insert_after_page_id and insert_before_page_id")
            
            if insert_after_page_id is not None:
                try:
                    current_page.reorder_after(insert_after_page_id)
                except ValueError as e:
                    raise GraphQLError(str(e))
            elif insert_before_page_id is not None:
                try:
                    current_page.reorder_before(insert_before_page_id)
                except ValueError as e:
                    raise GraphQLError(str(e))
            
            return current_page
            
        except (Notebook.DoesNotExist, Page.DoesNotExist):
            raise GraphQLError(f"Page not found at path '{page_path}' in notebook '{notebook_slug}'")
        except Exception as e:
            raise GraphQLError(f"Error updating page: {str(e)}")

    @strawberry.mutation
    def delete_page(
        self,
        info: Info,
        notebook_slug: str,
        page_path: str,
    ) -> Union[NotebookDeleteSuccess, NotebookAuthenticationError, NotebookPermissionError]:
        """Delete a page using notebook slug and page path"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to delete a page")
        
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to delete this page")
            
            # Navigate to the page using path
            path_parts = [p for p in page_path.strip("/").split("/") if p]
            current_page = None
            
            for slug_part in path_parts:
                current_page = Page.objects.get(
                    notebook=notebook,
                    slug=slug_part,
                    parent=current_page
                )
            
            if current_page is None:
                raise GraphQLError(f"Page not found at path '{page_path}'")
            
            current_page.delete()
            return NotebookDeleteSuccess(success=True, message="Page deleted successfully")
            
        except (Notebook.DoesNotExist, Page.DoesNotExist):
            raise GraphQLError(f"Page not found at path '{page_path}' in notebook '{notebook_slug}'")
        except Exception as e:
            raise GraphQLError(f"Error deleting page: {str(e)}")

    @strawberry.mutation
    def reorder_page(
        self,
        info: Info,
        notebook_slug: str,
        page_path: str,
        insert_after_page_id: Optional[int] = None,
        insert_before_page_id: Optional[int] = None,
    ) -> Union[PageType, NotebookAuthenticationError, NotebookPermissionError]:
        """Reorder a page by positioning it relative to another page"""
        if not info.context.request.user.is_authenticated:
            return NotebookAuthenticationError(message="You must be logged in to reorder pages")
        
        try:
            # Extract notebook ID from slug
            notebook_id = notebook_slug.split("-")[-1]
            notebook = Notebook.objects.get(id=notebook_id)
            
            # Check if user owns the notebook
            if notebook.user != info.context.request.user:
                return NotebookPermissionError(message="You don't have permission to reorder this page")
            
            # Navigate to the page using path
            path_parts = [p for p in page_path.strip("/").split("/") if p]
            current_page = None
            
            for slug_part in path_parts:
                current_page = Page.objects.get(
                    notebook=notebook,
                    slug=slug_part,
                    parent=current_page
                )
            
            if current_page is None:
                raise GraphQLError(f"Page not found at path '{page_path}'")
            
            # Handle reordering - only one positioning method can be used
            if insert_after_page_id is not None and insert_before_page_id is not None:
                raise GraphQLError("Cannot specify both insert_after_page_id and insert_before_page_id")
            
            if insert_after_page_id is None and insert_before_page_id is None:
                raise GraphQLError("Must specify either insert_after_page_id or insert_before_page_id")
            
            if insert_after_page_id is not None:
                try:
                    current_page.reorder_after(insert_after_page_id)
                except ValueError as e:
                    raise GraphQLError(str(e))
            elif insert_before_page_id is not None:
                try:
                    current_page.reorder_before(insert_before_page_id)
                except ValueError as e:
                    raise GraphQLError(str(e))
            
            return current_page
            
        except (Notebook.DoesNotExist, Page.DoesNotExist):
            raise GraphQLError(f"Page not found at path '{page_path}' in notebook '{notebook_slug}'")
        except Exception as e:
            raise GraphQLError(f"Error reordering page: {str(e)}")


# Create the main schema components that can be imported
notebook_queries = NotebookQuery
notebook_mutations = NotebookMutation