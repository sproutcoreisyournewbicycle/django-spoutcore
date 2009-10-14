from django.contrib import admin

from polls.models import Poll, Choice

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 5

class PollAdmin(admin.ModelAdmin):
    search_fields = ('question',)
    list_display = ('question',)
    inlines = (ChoiceInline,)
    prepopulated_fields = {"slug": ("question",)}
admin.site.register(Poll, PollAdmin)
