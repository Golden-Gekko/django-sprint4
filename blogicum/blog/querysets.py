from django.db.models import QuerySet
from django.utils.timezone import localdate


class PostQuerySet(QuerySet):
    def with_related_data(self):
        return self.select_related('location', 'author', 'category')

    def published(self):
        return self.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lt=localdate()
        )
