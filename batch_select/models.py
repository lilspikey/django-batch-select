from django.db.models.query import QuerySet
from django.db import models

from django.conf import settings

def batch_select(model, instances, target_field_name, m2m_fieldname):
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
    
    grouped = {}
    for m2m_instance in m2m_instances:
        instance_id = getattr(m2m_instance, id_column)
        group = grouped.get(instance_id, [])
        group.append(m2m_instance)
        grouped[instance_id] = group
    
    for instance in instances:
        setattr(instance, target_field_name, grouped.get(instance.id,[]))
    
    return instances

class BatchQuerySet(QuerySet):
    
    def _clone(self):
        query = super(BatchQuerySet, self)._clone()
        batches = getattr(self, '_batches', None)
        if batches:
            query._batches = set(batches)
        return query
    
    def batch_select(self, **field_names):
        query = self._clone()
        batches = getattr(self, '_batches', set())
        for target_field_name, m2m_fieldname in field_names.items():
            batches.add((target_field_name, m2m_fieldname))
        query._batches = batches
        return query
    
    def __iter__(self):
        result_iter = super(BatchQuerySet, self).__iter__()
        batches = getattr(self, '_batches', None)
        if batches:
            results = list(result_iter)
            for target_field_name, m2m_fieldname in set(batches):
                results = batch_select(self.model, results, target_field_name, m2m_fieldname)
                batches.remove((target_field_name, m2m_fieldname))
            return iter(results)
        return result_iter

class BatchManager(models.Manager):
    def get_query_set(self):
        return BatchQuerySet(self.model)
    
    def batch_select(self, **field_names):
        return self.all().batch_select(**field_names)

if getattr(settings, 'TESTING_BATCH_SELECT', False):
    class Tag(models.Model):
        name = models.CharField(max_length=32)
    
    class Entry(models.Model):
        tags = models.ManyToManyField(Tag)
        
        objects = BatchManager()
        