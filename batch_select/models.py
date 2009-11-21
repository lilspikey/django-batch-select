from django.db.models.query import QuerySet
from django.db import models

from django.conf import settings

def batch_select(model, instances, target_field_name, m2m_fieldname, **filter):
    '''
    basically do an extra-query to select the many-to-many
    field values into the instances given. e.g. so we can get all
    Entries and their Tags in two queries rather than n+1
    
    returns a list of the instance with the newly attached fields
    
    batch_select(Entry, Entry.objects.all(), 'tags', 'all_tags')
    
    would return a list of Entry objects with 'all_tags' fields
    containing the tags for that Entry
    '''
    
    m2m_field = getattr(model, m2m_fieldname).field
    m2m_model = m2m_field.rel.to # model on other end of relationship
    related_name = m2m_field.related_query_name()
    id_column = m2m_field.m2m_column_name()
    db_table  = m2m_field.m2m_db_table()
    
    instances = list(instances)
    
    ids = [instance.id for instance in instances]
    
    id__in_filter={ ('%s__in' % related_name): ids }
    select = { id_column: '`%s`.`%s`' % (db_table, id_column) }
    # also need to get id, so we can can re-attach to instances
    m2m_instances = m2m_model._default_manager \
                             .filter(**id__in_filter) \
                             .extra(select=select)
    
    if filter:
        m2m_instances = m2m_instances.filter(**filter)
    
    grouped = {}
    for m2m_instance in m2m_instances:
        instance_id = getattr(m2m_instance, id_column)
        group = grouped.get(instance_id, [])
        group.append(m2m_instance)
        grouped[instance_id] = group
    
    for instance in instances:
        setattr(instance, target_field_name, grouped.get(instance.id,[]))
    
    return instances

class Batch(object):
    def __init__(self, m2m_fieldname, **filter):
        self.m2m_fieldname = m2m_fieldname
        self.filter = filter
        self.target_field_name = '%s_all' % m2m_fieldname

class BatchQuerySet(QuerySet):
    
    def _clone(self):
        query = super(BatchQuerySet, self)._clone()
        batches = getattr(self, '_batches', None)
        if batches:
            query._batches = set(batches)
        return query
    
    def _create_batch(self, batch_or_str, target_field_name=None):
        batch = batch_or_str
        if isinstance(batch_or_str, basestring):
            batch = Batch(batch_or_str)
        if target_field_name:
            batch.target_field_name = target_field_name
        return batch
    
    def batch_select(self, *batches, **named_batches):
        batches = getattr(self, '_batches', set()) | \
                  set(self._create_batch(batch) for batch in batches) | \
                  set(self._create_batch(batch, target_field_name) \
                        for target_field_name, batch in named_batches.items())
        
        query = self._clone()
        query._batches = batches
        return query
    
    def iterator(self):
        result_iter = super(BatchQuerySet, self).iterator()
        batches = getattr(self, '_batches', None)
        if batches:
            results = list(result_iter)
            for batch in batches:
                results = batch_select(self.model, results,
                                       batch.target_field_name,
                                       batch.m2m_fieldname,
                                       **batch.filter)
            return iter(results)
        return result_iter

class BatchManager(models.Manager):
    def get_query_set(self):
        return BatchQuerySet(self.model)
    
    def batch_select(self, *batches, **named_batches):
        return self.all().batch_select(*batches, **named_batches)

if getattr(settings, 'TESTING_BATCH_SELECT', False):
    class Tag(models.Model):
        name = models.CharField(max_length=32)
    
    class Entry(models.Model):
        tags = models.ManyToManyField(Tag)
        
        objects = BatchManager()
        