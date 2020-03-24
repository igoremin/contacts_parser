from django.contrib import admin
from .models import FileWithUrls, PageData, ParserName, NoResponseUrls, DoneUrls, Settings


admin.site.register(FileWithUrls)
admin.site.register(ParserName)
admin.site.register(PageData)
admin.site.register(NoResponseUrls)
admin.site.register(DoneUrls)
admin.site.register(Settings)
