from django.contrib import admin

# Register your models here.
from .models import Post, Group



class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'group', 'author')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = "-пусто-"
 

class GroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'description',)
    search_fields = ('title', 'description',)
    empty_value_display = "-пусто-"

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)