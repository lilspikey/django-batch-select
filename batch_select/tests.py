from django.conf import settings

if getattr(settings, 'TESTING_BATCH_SELECT', False):
    from django.test import TransactionTestCase
    from batch_select.models import Tag, Entry
    
    class TestBatchSelect(TransactionTestCase):
        
        def test_batch_select_empty(self):
            entries = Entry.objects.batch_select(all_tags='tags')
            self.failUnlessEqual([], list(entries))
        
        def test_batch_select_no_tags(self):
            entry = Entry.objects.create()
            entries = Entry.objects.batch_select(all_tags='tags')
            self.failUnlessEqual([entry], list(entries))
        
        def test_batch_select_with_tags(self):
            entry1 = Entry.objects.create()
            entry2 = Entry.objects.create()
            entry3 = Entry.objects.create()
            entry4 = Entry.objects.create()
            
            tag1 = Tag.objects.create(name='tag1')
            tag2 = Tag.objects.create(name='tag2')
            tag3 = Tag.objects.create(name='tag3')
            
            entry1.tags.add(tag1)
            entry1.tags.add(tag2)
            entry1.tags.add(tag3)
            
            entry2.tags.add(tag2)
            
            entry3.tags.add(tag2)
            entry3.tags.add(tag3)
            
            entries = Entry.objects.batch_select(all_tags='tags').order_by('id')
            entries = list(entries)
            
            self.failUnlessEqual([entry1, entry2, entry3, entry4], entries)
            
            entry1, entry2, entry3, entry4 = entries
            
            self.failUnlessEqual(set([tag1, tag2, tag3]), set(entry1.all_tags))
            self.failUnlessEqual(set([tag2]),             set(entry2.all_tags))
            self.failUnlessEqual(set([tag2, tag3]),       set(entry3.all_tags))
            self.failUnlessEqual(set([]),                 set(entry4.all_tags))
            