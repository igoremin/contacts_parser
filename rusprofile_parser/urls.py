from django.urls import path
from .views import new_parsing, done_parsings, parsing_details, company_details, rusprofile_settings

urlpatterns = [
    path('new_parsing/', new_parsing, name='new_rusprofile_parsing_url'),
    path('details/<int:pk>/', company_details, name='rusprofile_company_details_url'),
    path('settings/', rusprofile_settings, name='rusprofile_settings_url'),
    path('<str:name>/', parsing_details, name='rusprofile_parser_details_url'),
    path('', done_parsings, name='all_rusprofile_parsings_url'),
]
