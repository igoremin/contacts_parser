from django.contrib import admin
from .models import RusprofileParser, RusprofileParserData, RusprofileSettings


admin.site.register(RusprofileParser)
admin.site.register(RusprofileParserData)
admin.site.register(RusprofileSettings)
