from django.db.models import Manager

from .querysets import PostQuerySet


class PublishedPostManager(Manager):
    def get_queryset(self):
        return (
            PostQuerySet(self.model)
            .with_related_data()
            .published()
        )
