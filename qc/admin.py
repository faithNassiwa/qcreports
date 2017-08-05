from django.contrib import admin
from .models import Contact, Group, Email, Run, Flow, Step, Value, Message


class EmailAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'project')
    search_fields = ['name']


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'name', 'language', 'urns', 'groups', 'points', 'number_of_weeks', 'blocked', 'stopped',
                    'created_on', 'modified_on')
    list_filter = ('created_on', 'modified_on')
    search_fields = ['name', 'urns', 'groups']


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'folder', 'contact', 'urn', 'broadcast', 'channel', 'direction', 'type', 'status',
                    'visibility', 'text', 'labels', 'created_on', 'sent_on', 'modified_on')
    list_filter = ('created_on', 'modified_on')
    search_fields = ['urn', 'text']


class FlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'name', 'expires', 'created_on')
    search_fields = ['name']


class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'name', 'query', 'count', 'get_sync', 'send_sync')
    search_fields = ['name']


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_id', 'responded', 'contact', 'flow', 'created_on', 'modified_on', 'exit_type')
    search_fields = ['run_id', 'contact', 'flow',]


class StepAdmin(admin.ModelAdmin):
    list_display = ('id', 'node', 'time', 'run_id')
    search_fields = ['node']


class ValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'value_name', 'value', 'category', 'node', 'time', 'run_id')
    search_fields = ['value', 'value_name']


admin.site.register(Contact, ContactAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(Run, RunAdmin)
admin.site.register(Flow, FlowAdmin)
admin.site.register(Step, StepAdmin)
admin.site.register(Value, ValueAdmin)
