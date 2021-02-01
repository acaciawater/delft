from django.contrib import admin, messages
from models import Alarm, Inspector, Recipient, Event, Message
from django.utils.safestring import mark_safe

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ('inspector', 'series', 'active')
    list_filter = ('inspector', 'series', 'recipients')
    search_fields = ('series', )
    filter_horizontal = ('recipients',)
    actions = ('inspect',)
    fieldsets = (
        (None, {
            'fields': ('series',('inspector', 'active'), 'recipients', 'options')
            }),
        ('Email', {
            'fields': ('subject','message_text')
            }), 
        )
    
    def inspect(self, request, queryset):
        num_events = 0
        for alarm in queryset:
            events = alarm.inspect(notify=False, save=True)
            num_events += len(events)
        message = '{alarms} alarms processed, <a href="{url}">{events} events</a> generated'.format(
            alarms = queryset.count(), 
            url = '/admin/delft/event?alarm__id__in=[{}]'.format(','.join([str(a.id) for a in queryset])),
            events = num_events)
        messages.success(request, mark_safe(message))
    inspect.short_description = 'Test selected alarms (do not notify users)'

class AlarmInline(admin.TabularInline):
    model = Alarm.recipients.through
        
@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description','classname')

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    inlines = (AlarmInline,)
    
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
    notify.short_description = 'Send emails to recipients for selected events'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('event', 'sent')
    list_filter = ('event__alarm', 'event__alarm__series','sent','recipients')
