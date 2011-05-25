====================
Django Batch Select
====================

The idea of Django Batch Select is to provide an equivalent to Django's select_related_ functionality.  As of such it's another handy tool for avoiding the "n+1 query problem".

select_related_ is handy for minimizing the number of queries that need to be made in certain situations.  However it is only usual for pre-selecting ForeignKey_ relations.

batch_select is handy for pre-selecting ManyToManyField_ relations and reverse ForeignKey_ relations.

It works by performing a single extra SQL query after a QuerySet_ has been evaluated to stitch in the the extra fields asked for.  This requires the addition of a custom Manager_, which in turn returns a custom QuerySet_ with extra methods attached.

Example Usage
=============

Assuming we have models defined as the following:

::

    from batch_select.models import BatchManager
    
    class Tag(models.Model):
        name = models.CharField(max_length=32)

    class Section(models.Model):
        name = models.CharField(max_length=32)
    
        objects = BatchManager()

    class Entry(models.Model):
        title = models.CharField(max_length=255)
        section = models.ForeignKey(Section, blank=True, null=True)
        tags = models.ManyToManyField(Tag)
    
        objects = BatchManager()

I'll also define a helper function to show the SQL queries generated:

::

    from django import db
    
    def show_queries():
        for query in db.connection.queries:
            print query["sql"]
        db.reset_queries()

Here are a few example (with generated sql queries):

::

    >>> Entry.objects.batch_select('tags').all()
    []
    >>> show_queries() # no results, so no 2nd query
    SELECT "batch_select_entry"."id", "batch_select_entry"."title", "batch_select_entry"."section_id" FROM "batch_select_entry"
    >>> Entry.objects.create()
    >>> Entry.objects.create()
    >>> tag1 = Tag.objects.create(name='tag1')
    >>> tag2 = Tag.objects.create(name='tag2')
    >>> db.reset_queries()
    >>> entries = Entry.objects.batch_select('tags').all()
    >>> entry = entries[0]
    >>> print entry.tags_all
    []
    >>> show_queries()
    SELECT "batch_select_entry"."id", "batch_select_entry"."title", "batch_select_entry"."section_id" FROM "batch_select_entry" LIMIT 1
    SELECT (`batch_select_entry_tags`.`entry_id`) AS "entry_id", "batch_select_tag"."id", "batch_select_tag"."name" FROM "batch_select_tag" INNER JOIN "batch_select_entry_tags" ON ("batch_select_tag"."id" = "batch_select_entry_tags"."tag_id") WHERE "batch_select_entry_tags".entry_id IN (1)
    >>> entry.tags.add(tag1)
    >>> db.reset_queries()
    >>> entries = Entry.objects.batch_select('tags').all()
    >>> entry = entries[0]
    >>> print entry.tags_all
    [<Tag: Tag object>]
    >>> show_queries()
    SELECT "batch_select_entry"."id", "batch_select_entry"."title", "batch_select_entry"."section_id" FROM "batch_select_entry" LIMIT 1
    SELECT (`batch_select_entry_tags`.`entry_id`) AS "entry_id", "batch_select_tag"."id", "batch_select_tag"."name" FROM "batch_select_tag" INNER JOIN "batch_select_entry_tags" ON ("batch_select_tag"."id" = "batch_select_entry_tags"."tag_id") WHERE "batch_select_entry_tags".entry_id IN (1)
    >>> entries = Entry.objects.batch_select('tags').all()
    >>> for entry in entries:
    ....     print entry.tags_all
    ....
    [<Tag: Tag object>]
    []
    >>> show_queries()
    SELECT "batch_select_entry"."id", "batch_select_entry"."title", "batch_select_entry"."section_id" FROM "batch_select_entry"
    SELECT (`batch_select_entry_tags`.`entry_id`) AS "entry_id", "batch_select_tag"."id", "batch_select_tag"."name" FROM "batch_select_tag" INNER JOIN "batch_select_entry_tags" ON ("batch_select_tag"."id" = "batch_select_entry_tags"."tag_id") WHERE "batch_select_entry_tags".entry_id IN (1, 2)
    
Re-running that same last for loop without using batch_select generate three queries instead of two (n+1 queries):

::

    >>> entries = Entry.objects.all()
    >>> for entry in entries:
    ....     print entry.tags.all()
    ....
    [<Tag: Tag object>]
    []
                                                                                                                          
    >>> show_queries()
    SELECT "batch_select_entry"."id", "batch_select_entry"."title", "batch_select_entry"."section_id" FROM "batch_select_entry"
    SELECT "batch_select_tag"."id", "batch_select_tag"."name" FROM "batch_select_tag" INNER JOIN "batch_select_entry_tags" ON ("batch_select_tag"."id" = "batch_select_entry_tags"."tag_id") WHERE "batch_select_entry_tags"."entry_id" = 1
    SELECT "batch_select_tag"."id", "batch_select_tag"."name" FROM "batch_select_tag" INNER JOIN "batch_select_entry_tags" ON ("batch_select_tag"."id" = "batch_select_entry_tags"."tag_id") WHERE "batch_select_entry_tags"."entry_id" = 2

More Advanced Usage
=========================

By default the batch fields are inserted into fields named <name>_all, on each object.  So:

::

    Entry.objects.batch_select('tags').all()

Results in the Entry instances having fields called 'tags_all' containing the Tag objects associated with that Entry.

If you want to give the field a different name just use a keyword argument - in the same way as using the Aggregation_ API:

::

    Entry.objects.batch_select(selected_tags='tags').all()

Would means the Tag objects would be assigned to fields called 'selected_tags'.

If you want to perform filtering of the related objects you will need to use a Batch object.  By doing this you can pass extra keyword arguments in the same way as when using the filter method of a QuerySet:

::
    
    from batch_select.models import Batch
    
    Entry.objects.batch_select(tags_containing_blue=Batch('tags', name__contains='blue'))

Would return Entry objects with fields called 'tags_containing_name' with only those Tags whose name contains 'blue'.

In addition to filtering using keyword arguments, you can also call the following methods on a Batch object, with their effects being passed on to the underlying QuerySet_ object:

* filter_
* exclude_
* annotate_
* order_by_
* reverse_
* select_related_
* extra_
* defer_
* only_

(Note that distinct(), values() etc are not included as they would have side-effects on how the extra query is associated with the original query)
So for example to achieve the same effect as the filter above you could do the following:

::
    
    from batch_select.models import Batch
    
    Entry.objects.batch_select(tags_containing_blue=Batch('tags').filter(name__contains='blue'))

Whereas the following would exclude tags containing "blue" and order by name:

::

    from batch_select.models import Batch
    
    batch = Batch('tags').exclude(name__contains='blue').order_by('name')
    Entry.objects.batch_select(tags_not_containing_blue=batch)


TODOs and BUGS
==============
See: http://github.com/lilspikey/django-batch-select/issues

.. _select_related: http://docs.djangoproject.com/en/dev/ref/models/querysets/#id4
.. _ForeignKey: http://docs.djangoproject.com/en/dev/ref/models/fields/#foreignkey
.. _ManyToManyField: http://docs.djangoproject.com/en/dev/ref/models/fields/#manytomanyfield
.. _QuerySet: http://docs.djangoproject.com/en/dev/ref/models/querysets/
.. _Manager: http://docs.djangoproject.com/en/dev/topics/db/managers/
.. _Aggregation: http://docs.djangoproject.com/en/dev/topics/db/aggregation/
.. _filter: http://docs.djangoproject.com/en/dev/ref/models/querysets/#filter-kwargs
.. _exclude: http://docs.djangoproject.com/en/dev/ref/models/querysets/#exclude-kwargs
.. _annotate: http://docs.djangoproject.com/en/dev/ref/models/querysets/#annotate-args-kwargs
.. _order_by: http://docs.djangoproject.com/en/dev/ref/models/querysets/#order-by-fields
.. _reverse: http://docs.djangoproject.com/en/dev/ref/models/querysets/#reverse
.. _extra: http://docs.djangoproject.com/en/dev/ref/models/querysets/#extra-select-none-where-none-params-none-tables-none-order-by-none-select-params-none
.. _defer: http://docs.djangoproject.com/en/dev/ref/models/querysets/#defer-fields
.. _only: http://docs.djangoproject.com/en/dev/ref/models/querysets/#only-fields