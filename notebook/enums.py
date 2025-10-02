import strawberry
from enum import Enum


class NotebookSortBy(Enum):
    LATEST = "latest"
    OLDEST = "oldest"
    NAME = "name"


# Convert to Strawberry enum
NotebookSortByEnum = strawberry.enum(NotebookSortBy)