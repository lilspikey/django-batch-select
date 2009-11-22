from django.db.models.query import QuerySet
from django.db import models
from django.db.models.fields import FieldDoesNotExist

from django.conf import settings

def _not_exists(fieldname):
    raise FieldDoesNotExist('"%s" is not a ManyToManyField or a reverse ForeignKey relationship' % fieldname)

def _check_field_exists(model, fieldname):
    field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
    if not m2m:
        if direct: # reverse foreign key relationship
            _not_exists(fieldname)

def batch_select(model, instances, target_field_name, fieldname, **filter):
    '''
    basically do an extra-query to select the many-to-many
    field values into the instances given. e.g. so we can get all
    Entries and their Tags in two queries rather than n+1
    
    returns a list of the instance with the newly attached fields
    
    batch_select(Entry, Entry.objects.all(), 'tags', 'all_tags')
    
    would return a list of Entry objects with 'all_tags' fields
    containing the tags for that Entry
    '''
    
    _check_field_exists(model, fieldname)
    
    instances = list(instances)
    ids = [instance.id for instance in instances]
    
    field_object, model, direct, m2m = model._meta.get_field_by_name(fieldname)
    if m2m:
        m2m_field = field_object
        m2m_model = m2m_field.rel.to # model on other end of relationship
        related_name = m2m_field.related_query_name()
        id_column = m2m_field.m2m_column_name()
        db_table  = m2m_field.m2m_db_table()
        
        def get_instance_id(related_instance):
            return getattr(related_instance, id_column)
        
        id__in_filter={ ('%s__in' % related_name): ids }
        
        select = { id_column: '`%s`.`%s`' % (db_table, id_column) }
        # also need to get id, so we can can re-attach to instances
        related_instances = m2m_model._default_manager \
                                 .filter(**id__in_filter) \
                                 .extra(select=select)
    elif not direct:
        # handle reverse foreign key relationships
        fk_field = field_object.field
        related_model = field_object.model
        related_name  = fk_field.name
        
        def get_instance_id(related_instance):
            return getattr(related_instance, related_name).id
        
        id__in_filter={ ('%s__in' % related_name): ids }
        
        related_instances = related_model._default_manager \
                                .filter(**id__in_filter) \
                                .select_related(related_name)
    
    if filter:
        related_instances = related_instances.filter(**filter)
    
    grouped = {}
    for related_instance in related_instances:
        instance_id = get_instance_id(related_instance)
        group = grouped.get(instance_id, [])
        group.append(related_instance)
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
        
        _check_field_exists(self.model, batch.m2m_fieldname)
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
    use_for_related_fields = True
    
    def get_query_set(self):
        return BatchQuerySet(self.model)
    
    def batch_select(self, *batches, **named_batches):
        return self.all().batch_select(*batches, **named_batches)

if getattr(settings, 'TESTING_BATCH_SELECT', False):
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
        