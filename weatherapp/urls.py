from django.urls import path

# Get the Views
from .views import *

urlpatterns = [
    path('create_group', create_groups, name='create_groups'),
    path('admin_login/', admin_login, name='admin_login'),
    path('admin_home/', admin_home, name='admin_home'),
    path("logout", logout_request, name="logout"),

    path('cl_logout/', logout_request_client, name='logout_client'),
    path('create_client/', create_client, name='create_client'),

    path('403/', forbidden, name='403'),
    path('client_login/', client_login, name='client_login'),
    path('', homepage, name='homepage'),

    path('homepage/', homepage, name='homepage'),
    path('forecast_tabular/', forecast_tabular, name='forecast_tabular'),
    path('forecast_warning/', forecast_warning, name='forecast_warning'),
    path('overview/', overview_dash, name='overview'),
    path('warnings/', warnings_dash, name='warnings'),
    # path('user_update/<int:pk>',user_update,name='update_user'),


    ## Ajax table calls
    path('get_forecast_table/', get_forecast_table, name='get_forecast_table'),
    path('get_sites/', get_sites, name='get_sites'),
    path('get_fw_data/', get_fw_data, name='get_fw_data'),
    path('get_min_date/', get_min_date, name='get_min_date'),
    path('get_overview_data/', get_overview_data, name='get_overview_data'),
    path('get_client/', get_clients, name='get_clients'),
    path('get_warnings_data/', get_warnings_data, name='get_warnings_data'),
    path('get_homepage_data/', get_homepage_data, name='get_homepage_data'),
    path('get_homepage_graph_data/',update_on_site_change,name='get_homepage_graph_data')

]
