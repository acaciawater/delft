from django.contrib import admin, messages
from models import Alarm, Inspector, Receiver, Event
from django.utils.safestring import mark_safe

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ('inspector', 'series', )
    list_filter = ('inspector', 'series', 'receivers')
    search_fields = ('series', )
    filter_horizontal = ('receivers',)
    exclude = ('sent',)
    actions = ('inspect',)
    fieldsets = (
        (None, {
            'fields': ('series','inspector', 'receivers', 'options')
            }),
        ('Email template', {
            'fields': ('subject','text_template','html_template')
            }), 
        )
    
    def inspect(self, request, queryset):
        num_events = 0
        for alarm in queryset:
            events = alarm.inspect(notify=True)
            # TODO: use bulk_upsert here
            for e in events:
                alarm.event_set.update_or_create(time=e.time,defaults={'message':e.message})
            num_events += len(events)

        message = '{alarms} alarms processed, <a href="{url}">{events} events</a> generated'.format(
            alarms = queryset.count(), 
            url = '/admin/delft/event?alarm__id__in=[{}]'.format(','.join([str(a.id) for a in queryset])),
            events = num_events)
        messages.success(request, mark_safe(message))
    inspect.short_description = 'Test alarm'
    
@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description','classname')

@admin.register(Receiver)
class ReceiverAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('alarm', 'time')
    list_filter = ('alarm', 'alarm__series', 'time')
    actions = ('notify',)
    
    def notify(self, request, queryset):
        alarms = set((e.alarm for e in queryset))
        for alarm in alarms:
            events = queryset.filter(alarm=alarm)
            alarm.notify(events)
#         message = '{} emails sent'.format(queryset.count())
#         messages.success(request, message)
    notify.short_description = 'Send email to registered receivers'
        
