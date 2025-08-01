from articles.models import Article
from google.cloud import tasks_v2
import json
import os
import base64
from datetime import datetime, timedelta
from django.conf import settings

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

def create_sample_cloud_task(payload=None, delay_seconds=0):
    """
    Create a sample Google Cloud Task.
    
    Args:
        payload (dict): The payload to send with the task
        delay_seconds (int): Delay before task execution in seconds
    
    Returns:
        dict: Response from Cloud Tasks API
    """
    # Initialize the Cloud Tasks client
    client = tasks_v2.CloudTasksClient()
    
    # Configuration from Django settings
    project_id = settings.GOOGLE_CLOUD_PROJECT
    queue_name = settings.CLOUD_TASKS_QUEUE
    location = settings.CLOUD_TASKS_LOCATION
    endpoint_url = settings.TASK_ENDPOINT_URL
    
    # Construct the fully qualified queue name
    parent = client.queue_path(project_id, location, queue_name)
    
    # Default payload if none provided
    if payload is None:
        payload = {
            'task_type': 'sample_task',
            'timestamp': datetime.now().isoformat(),
            'message': 'Hello from Cloud Tasks!',
            'article_id': 123,
            'action': 'process_article'
        }
    
    # Create the task
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': endpoint_url or 'https://httpbin.org/post',
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'Google-Cloud-Tasks',
                'Authorization': f'Bearer {settings.CLOUD_TASKS_AUTH_TOKEN}' if hasattr(settings, 'CLOUD_TASKS_AUTH_TOKEN') else None
            },
            'body': json.dumps(payload).encode('utf-8')
        }
    }
    
    # Remove Authorization header if not set
    if task['http_request']['headers']['Authorization'] is None:
        del task['http_request']['headers']['Authorization']
    
    # Add scheduling if delay is specified
    if delay_seconds > 0:
        # Calculate the time when the task should be executed
        schedule_time = datetime.now() + timedelta(seconds=delay_seconds)
        task['schedule_time'] = {
            'seconds': int(schedule_time.timestamp())
        }
    
    try:
        # Create the task
        response = client.create_task(
            request={
                'parent': parent,
                'task': task
            }
        )
        
        return {
            'success': True,
            'task_name': response.name,
            'message': f'Task created successfully: {response.name}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to create task: {str(e)}'
        }

def create_embedding_generation_cloud_task(article: Article):
    """
    Create a task to generate an embedding for the article.
    
    Args:
        article: Article model instance
    
    Returns:
        dict: Response from Cloud Tasks API
    """
    # Initialize the Cloud Tasks client
    client = tasks_v2.CloudTasksClient()
    
    # Configuration from Django settings
    project_id = settings.GOOGLE_CLOUD_PROJECT
    queue_name = settings.CLOUD_TASKS_QUEUE
    location = settings.CLOUD_TASKS_LOCATION
    endpoint_url = settings.TASK_ENDPOINT_URL
    
    # Construct the fully qualified queue name
    parent = client.queue_path(project_id, location, queue_name)
    
    # Use the model's method to get properly formatted text for embedding
    combined_text = article.get_embedding_text()
    
    payload = {
        'task_type': 'embedding_generation',
        'timestamp': datetime.now().isoformat(),
        'article_embedding_request': {
            'article_id': str(article.id),
            'text': combined_text,
            'normalize': True,
            'dimensions': 768
        }
    }
    
    # Create the task with base64 encoded body
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': endpoint_url,
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'Google-Cloud-Tasks-Embedding',
                'Authorization': f'Bearer {settings.CLOUD_TASKS_AUTH_TOKEN}' if hasattr(settings, 'CLOUD_TASKS_AUTH_TOKEN') else None
            },
            'body': base64.b64encode(json.dumps(payload).encode('utf-8'))
        }
    }
    
    # Remove Authorization header if not set
    if task['http_request']['headers']['Authorization'] is None:
        del task['http_request']['headers']['Authorization']
    
    try:
        # Create the task
        response = client.create_task(
            request={
                'parent': parent,
                'task': task
            }
        )
        
        return {
            'success': True,
            'task_name': response.name,
            'message': f'Embedding task created successfully: {response.name}',
            'article_id': article.id
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to create embedding task: {str(e)}',
            'article_id': article.id
        }
    