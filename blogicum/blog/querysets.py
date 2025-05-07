from django.db.models import Count, QuerySet
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

    def with_comment_count(self):
        return (
            self
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date', 'title')
        )
