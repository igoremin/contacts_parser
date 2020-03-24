from django.urls import path
from .views import main_page, new_parser, parser_details, load_new_search_file, continue_parsing, url_details,\
    parser_settings


urlpatterns = [
    path('', main_page, name='main_page_url'),
    path('new_parsing/', new_parser, name='new_parser_url'),
    path('load_new_file/', load_new_search_file, name='load_new_file_url'),
    path('details/<int:pk>/', url_details, name='url_details_url'),
    path('continue_parsing/<str:name>/', continue_parsing, name='continue_parsing_url'),
    path('settings/', parser_settings, name='parser_settings_url'),
    path('<str:name>/', parser_details, name='parser_details_url'),
]
