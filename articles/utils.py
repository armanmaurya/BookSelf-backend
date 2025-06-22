from articles.models import Article

def get_article_from_slug(slug):
    """
    Retrieve an article by its slug.
    """
    id = slug.split("-")[-1]
    try:
        article = Article.objects.get(id=id)
    except Article.DoesNotExist:
        return None
    return article