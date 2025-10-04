from notebook.models import Notebook


def get_notebook_from_slug(slug):
    """
    Retrieve a notebook by its slug.
    """
    try:
        notebook = Notebook.objects.get(slug=slug)
    except Notebook.DoesNotExist:
        return None
    return notebook