from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group
import json
from django.contrib.auth import get_user_model
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
## User Login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Permission

## Database Connections
from django.db import connections
from django.http import JsonResponse

# py data plots
from plotly import express as px
from plotly.utils import PlotlyJSONEncoder as enc_pltjson
from plotly import graph_objs as go
from plotly.subplots import make_subplots

# Getting Models
from .models import Clients

# Clients Form
from .forms import ClientsForm


# Get Decorators
from .decors import ajax_required
from django.utils.decorators import method_decorator

User = get_user_model()


# Check if the request is from ajax
def is_ajax(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    else:
        return False


# Get the Connection
def get_connection():
    connection1 = connections['dashboarding'].cursor()
    return connection1


# get the json response through Pandas dataframe
def get_json_response(df: pd.DataFrame):
    json_records = df.reset_index().to_json(orient='records')
    data = json.loads(json_records)
    return data


def forbidden(request):
    # logout(request)
    messages.warning(request, "No Access")
    return render(request, template_name='weatherapp/403.html')


# query Executor
def get_sql_data(query):
    connection1 = get_connection()
    with connection1 as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
        columns = cursor.description
        column = []
        for col in columns:
            column.append(col.name)
        df = pd.DataFrame(result, columns=column)
        # print(df)
        cursor.close()
        return df
def get_site_client(client_name = None):
    if client_name==None:
        df = get_sql_data("select sc.site_name,sc.client_name from configs.site_config sc")
        return df
    else:
        df = get_sql_data(f"select sc.site_name,sc.client_name from configs.site_config sc where client_name= '{client_name}'")
        return df

def convert_data_to_json(df: pd.DataFrame):
    json_records = df.reset_index().to_json(orient='records')
    data = json.loads(json_records)
    return data


# Create your views here.
@login_required(login_url='admin_login')
@user_passes_test(lambda u: u.is_superuser or u.Group.all()[0] == 'Admin', login_url='403')
def create_groups(request):
    Group.objects.get_or_create(name='Client')
    Group.objects.get_or_create(name='Admin')
    messages.success(request, "Groups Created > Admin and Client")
    return redirect('admin_home')


def admin_login(request):
    form = AuthenticationForm()
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("admin_home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    context = {'admin_form': form}
    return render(request, template_name='weatherapp/admin_login.html', context=context)


@login_required(login_url='admin_login')
@user_passes_test(lambda u: u.is_superuser or u.role_type == 'ADMIN', login_url='403')
def admin_home(request):
    groups = Group.objects.all()
    clients = Clients.objects.all()
    context = {'groups': groups, 'clients': clients}
    return render(request, template_name='weatherapp/Admin_page.html', context=context)


def logout_request(request):
    logout(request)
    messages.warning(request, "You have successfully logged out.")
    return redirect("admin_home")


def logout_request_client(request):
    logout(request)
    messages.warning(request, "You have successfully logged out.")
    return redirect("client_login")


@login_required(login_url='admin_login')
@user_passes_test(lambda u: u.is_superuser or u.role_type == 'ADMIN', login_url='403')
def create_client(request):
    form = ClientsForm()
    if request.method == 'POST':
        form = ClientsForm(request.POST, request.FILES)
        if form.is_valid():
            group_data = form.cleaned_data['role_type']
            # print(form.cleaned_data['role_type'])
            user = form.save()
            # Save admins to admin group
            client_group = Group.objects.get(name='Client')
            admin_group = Group.objects.get(name='Admin')
            if group_data == "CLIENT":
                user.groups.add(client_group)
            elif client_group=="ADMIN":
                user.groups.add(admin_group)
                list_perms = ['Can add user','Can change user','Can delete user','Can view user']
                for x in list_perms:
                    permission = Permission.objects.get(name=x)
                    user.user_permissions.add(permission)

            messages.success(request, "Client Successfully Added")
            return redirect('create_client')
        else:
            messages.warning(request, "There was an error in the Form")

    context = {'client_form': form}
    return render(request, template_name='weatherapp/create_clients.html', context=context)


# @user_passes_test(lambda u: u.is_authenticated , login_url='homepage')
def client_login(request):
    form = AuthenticationForm()
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("homepage")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    context = {'client_form': form}
    return render(request, template_name='weatherapp/client_login.html', context=context)


# page 1
# def ajax_overview(request):


@login_required(login_url='client_login')
def homepage(request):
    context = {}
    return render(request, template_name='weatherapp/homepage.html', context=context)


def get_forecast_data(request):
    pass


# @method_decorator(ajax_required)
def get_forecast_table(request):
    # if ~is_ajax(request):
    #     return redirect('403')
    # else:
    #     print("Ajax")
    if request.method == 'GET':
        username = request.GET['username']
        user_group = request.GET['group']
        # print(request.GET['group'])
        # print(user_group)
        yesterday = datetime.now()
        time_string = datetime.strftime(yesterday, '%m-%d-%y %H:%M:%S')
        query = ""
        d_swap = {'No Cloud': 'No Cloud',
                  13.0: 'High semitransparent thick clouds',
                  12.0: 'High semitransparent moderately thick clouds',
                  14.0: 'High semitransparent above low or medium clouds',
                  8.0: 'High opaque clouds',
                  6.0: 'Low clouds',
                  1.0: 'Cloud free land',
                  11.0: 'High semitransparent thin clouds',
                  7.0: 'Mid level clouds',
                  9.0: 'Very high opaque clouds',
                  10.0: 'Very High very opaque clouds',
                  5.0: 'Very Low clouds'}
        if user_group == "Admin":
           query = "SELECT site_client_name, forecast_cloud_index , timestamp, site_name,temp_actual,temp_forecast,ghi_actual" \
                   ",ghi_forecast,wind_speed_actual,wind_speed_forecast,forecast_cloud_type FROM dashboarding.v_final_dashboarding_view WHERE timestamp >= '{time_string}' " \
                   "ORDER BY timestamp DESC LIMIT 10000"
            # query = f"""SELECT vda.site_name,
            #             vda.timestamp,
            #            vda.wind_speed_10m_mps AS wind_speed_forecast,
            #            vda.wind_direction_in_deg AS wind_direction_forecast,
            #            vda.temp_c  AS temp_forecast,
            #            vda.nowcast_ghi_wpm2   AS ghi_forecast,
            #            vda.ct_flag_data "Cloud Description",,
            #            vda.ci_data as "forecast_cloud_index",
            #            vda.forecast_method,
            #            conf.client_name AS site_client_name,
            #            sa."ghi(w/m2)" AS ghi_actual,
            #            sa."temp(c)"   AS temp_actual,
            #            sa.ws          AS wind_speed_actual,
            #            sa.wd          AS wind_direction_actual
            #     FROM forecast.db_api vda
            #              JOIN configs.site_config conf ON vda.site_name = conf.site_name
            #              LEFT JOIN site_actual.site_actual sa on (vda.timestamp,vda.site_name) = (sa.timestamp,sa.site_name)
            #                 ORDER BY vda.timestamp desc WHERE timestamp >= '{time_string}'
            #     LIMIT 10000;"""
        else:
            query = f"""SELECT vda.site_name,
                        vda.timestamp,
                       vda.wind_speed_10m_mps AS wind_speed_forecast,
                       vda.wind_direction_in_deg AS wind_direction_forecast,
                       vda.temp_c  AS temp_forecast,
                       vda.nowcast_ghi_wpm2   AS ghi_forecast,
                       vda.ct_flag_data AS "Cloud Description",
                       vda.ci_data AS "forecast_cloud_index",
                       vda.ct_data AS "forecast_cloud_type",
                       vda.forecast_method,
                       conf.client_name AS site_client_name,
                       sa."ghi(w/m2)" AS ghi_actual,
                       sa."temp(c)"   AS temp_actual,
                       sa.ws          AS wind_speed_actual,
                       sa.wd          AS wind_direction_actual
                FROM forecast.db_api vda
                         JOIN configs.site_config conf ON vda.site_name = conf.site_name
                         LEFT JOIN site_actual.site_actual sa on (vda.timestamp,vda.site_name) = (sa.timestamp,sa.site_name)
                WHERE vda.timestamp >= '{time_string}' AND conf.client_name = '{username}' ORDER BY vda.timestamp desc
                LIMIT 10000;"""

            # query = f"SELECT site_client_name, forecast_cloud_index , timestamp, site_name,temp_actual,temp_forecast,ghi_actual" \
            #        ",ghi_forecast,wind_speed_actual,wind_speed_forecast,forecast_cloud_type FROM dashboarding.v_final_dashboarding_view" \
            #        f" WHERE site_client_name = '{username}' AND timestamp >= '{time_string}' ORDER BY timestamp DESC LIMIT 3000 "

        df_4 = get_sql_data(query)


        ci_index = 0.1
        df_4['forecast_cloud_type'] = df_4['forecast_cloud_type'].fillna('No Cloud') ## Old Query
        df_4['Cloud Description'] = df_4['Cloud Description'].str.replace("_"," ").str.title()
        df_4['ghi_actual'] = df_4['ghi_actual'].fillna('None')


        # df_4['Cloud Description'] = df_4['forecast_cloud_type'].map(lambda x: d_swap[x])

        df_4['Warning Description'] = None
        df_4.loc[df_4['forecast_cloud_index'] > 0.1, "Warning Description"] = "Cloud Warning"
        df_4.loc[df_4['forecast_cloud_index'] <= 0.1, "Warning Description"] = "No Warning"

        send_list = []
        df_4.fillna("None",inplace=True)
        if user_group == "Admin":
            send_list = ['site_client_name', 'timestamp', 'site_name', 'Cloud Description',
                         'Warning Description', 'temp_forecast', 'temp_actual', 'ghi_forecast',
                         'ghi_actual', 'wind_speed_forecast']
        else:
            send_list = ['timestamp', 'site_name', 'Cloud Description',
                         'Warning Description', 'temp_forecast', 'temp_actual', 'ghi_forecast',
                         'ghi_actual', 'wind_speed_forecast']
        df_4 = df_4.loc[:, send_list]
        # print(df_4)

        return JsonResponse({'data': df_4.to_dict('records')}, status=200, safe=False)


#
# Page 2
@login_required(login_url='client_login')
def forecast_tabular(request):
    context = {}
    return render(request, template_name='weatherapp/Forecast_Tabular.html', context=context)


def get_sites(request):
    if request.method == "GET":
        username = request.GET['username']
        group = request.GET['group']
        df = get_site_client()
        sites = ""
        if group == "Admin":
            sites = pd.DataFrame(df['site_name'])
        else:
            sites = pd.DataFrame(df.loc[df['client_name'] == username, 'site_name'])
        return JsonResponse({'data': sites.to_dict('records')}, status=200)


def get_clients(request):
    if request.method == "GET":
        clients = pd.read_csv("static/client_site.csv")
        clients['client_name'] = clients['client_name'].fillna("None")
        # print(clients)
        clients = pd.DataFrame(clients['client_name'].unique(), columns=['clients'])
        # clients = clients['clients'].fillna("None")
        # print(clients)
        return JsonResponse({'data': clients.to_dict('records')}, status=200, safe=False)


def get_min_date(request):
    if request.method == "GET":
        site = request.GET['site']
        variable = request.GET['variable']

        query = f"SELECT timestamp FROM dashboarding.v_final_dashboarding_view WHERE {variable}_actual IS NOT NULL AND " \
                f"{variable}_forecast IS NOT NULL AND {variable}_forecast>0 AND {variable}_actual >0 AND site_name = '{site}' ORDER BY timestamp LIMIT 1"
        df = get_sql_data(query)
       # print("Hello There")
        date_min = df['timestamp'][0].strftime("%Y-%m-%d")
        return JsonResponse({'data': date_min}, status=200)


def get_fw_data(request):
    if request.method == "GET":
        username = request.GET['username']
        group = request.GET['group']
        site_name = request.GET['site_name']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']
        variable = request.GET['variable']

        if len(start_date) > 1:
            start_date = start_date + " 00:00:00"
        if len(end_date) > 1:
            end_date = end_date + " 00:00:00"
        print(f"Start Date is {start_date}")
        # query = f"SELECT timestamp,site_name,forecast_cloud_index,{variable}_actual,{variable}_forecast FROM dashboarding.v_final_dashboarding_view WHERE" \
        #         f" site_name='{site_name}' AND timestamp >='{start_date}'" \
        #         f"AND timestamp <= '{end_date}' ORDER BY timestamp DESC"
        query = f"""SELECT vda.site_name, vda.timestamp, vda.wind_speed_10m_mps AS wind_speed_forecast, 
            vda.wind_direction_in_deg AS wind_direction_forecast, vda.temp_c AS temp_forecast, 
            vda.nowcast_ghi_wpm2 AS ghi_forecast, vda.swdown2,vda.ci_data AS forecast_cloud_index, vda.tz, vda.ct_data, vda.ct_flag_data, 
            vda.forecast_method, vda.log_ts, conf.client_name, conf.latitude AS site_lat,
            conf.longitude AS site_lon, sa."ghi(w/m2)" AS ghi_actual, 
            sa."temp(c)" AS temp_actual, sa.ws AS wind_speed_actual, sa.wd AS wind_direction_actual 
            FROM forecast.db_api vda JOIN configs.site_config conf ON vda.site_name = conf.site_name 
            LEFT JOIN site_actual.site_actual sa on (vda.timestamp,vda.site_name) = (sa.timestamp,sa.site_name) 
            WHERE conf.site_name = '{site_name}' AND vda.ci_data IS NOT NULL  AND vda.timestamp > '{start_date}' AND vda.timestamp <= '{end_date}'
              ORDER BY timestamp DESC"""
        ci_index = 0.1
        df = get_sql_data(query)

        # print(query)
        ## Plotly Graph Fore_Warn

        df = df.groupby(['timestamp']).aggregate(
            {f'{variable}_actual': 'mean', f'{variable}_forecast': 'mean',
             'forecast_cloud_index': 'mean'}).reset_index()
        df['Deviation'] = (df[f'{variable}_actual'] - df[f'{variable}_forecast']).abs().div(
            df[f'{variable}_actual']) * 100
        mn = df.loc[df[f'{variable}_actual'] > 0, 'Deviation'].mean()
        df['color'] = df['Deviation'].map(lambda x: "Green" if x <= mn else "Red")

        df['Graph Index'] = None
        df['Warning Description'] = None
        df['Warning Category'] = None
        df.loc[df['forecast_cloud_index'] > 0.1, "Warning Category"] = "Red"
        df.loc[df['forecast_cloud_index'] <= 0.1, "Warning Category"] = "Green"
        df.loc[df['forecast_cloud_index'] > 0.1, "Warning Description"] = "Cloud Warning"
        df.loc[df['forecast_cloud_index'] <= 0.1, "Warning Description"] = "No Warning"
        for x in df.loc[:, ['forecast_cloud_index', f'{variable}_forecast', 'Warning Description']].index:
            if df['forecast_cloud_index'][x] > ci_index:
                df['Graph Index'][x] = df[f'{variable}_forecast'][x]




        # df.to_csv("forecast_data.csv")
        readings = {'ghi':"W/m2","temp":f"{chr(176)} C",'wind_speed':"m/s"}
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[f'{variable}_actual'],
            name=f"{variable.title()} Actual"
        ))
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[f'{variable}_forecast'],
            name=f"{variable.title()} Forecast"
        ))
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['Graph Index'],
                name='Cloud Warning',
                mode='markers',
                marker_color='orange',
                marker_size=10
            )
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
            height=500,
            xaxis_title="Timestamp",
            yaxis_title=f"{readings[variable]}",
            legend_title="Legends",
            font=dict(
                family="Arial",
                size=15,
            ),
            margin=dict(
                l=10,
                r=10,
                b=10,
                t=10,
                pad=1
            ),
        )

        # print(df)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df.loc[df['color'] == 'Green', 'timestamp'],
            y=df.loc[df['color'] == 'Green', 'Deviation'],
            marker_color='green',
            name='Below'
        ))

        fig2.add_trace(go.Bar(
            x=df.loc[df['color'] == 'Red', 'timestamp'],
            y=df.loc[df['color'] == 'Red', 'Deviation'],
            name="Above",
            marker_color="red"

        ))
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
            height=500/2,

            xaxis_title="Timestamp",
            yaxis_title="Deviation",
            legend_title="%Deviation",
            font=dict(
                family="Arial",
                size=15,
            ),
            margin=dict(
                l=10,
                r=10,
                b=10,
                t=10,
                pad=1
            ),
        )



        # print(mn)
        # plt = px.line(data_frame=df,x='timestamp',y=['ghi_forecast','ghi_actual'])
        graphJSON = json.dumps(fig, cls=enc_pltjson)
        graphJson2 = json.dumps(fig2, cls=enc_pltjson)
        return JsonResponse({'data': graphJSON, 'deviation': graphJson2}, status=200)


def get_overview_data(request):
    if request.method == "GET":
        user_group = request.GET['group']
        user_name = request.GET['username']
        query = ""
        # print(user_group)
        if user_group == "Client":
            sites_df = get_site_client(user_name)
            sites_tuple = tuple(sites_df['site_name'])
            df_act = get_sql_data(f"""SELECT max(timestamp) timestamp_actual,site_name from site_actual.site_actual 
                where site_name in {sites_tuple} group by site_name order by timestamp_actual desc""")
            df_fcst = get_sql_data(f"""SELECT max(timestamp) timestamp_forecast,site_name from forecast.db_api where 
                site_name in {sites_tuple} group by site_name order by timestamp_forecast desc""")
            df_config = get_sql_data(f"""select site_name,client_name,state,capacity,site_status from 
            configs.site_config where site_name in {sites_tuple}""")

            # query = f"SELECT * FROM dashboarding.v_client_data_report WHERE client_name = '{user_name}'"
            # df_act = get_sql_data(f"""SELECT max(timestamp) timestamp_actual,site_name from site_actual.  site_actual group by site_name order by timestamp_actual desc""")
        else:
            df_act = get_sql_data(f"""SELECT max(timestamp) timestamp_actual,site_name from site_actual.site_actual 
                             group by site_name order by timestamp_actual desc""")
            df_fcst = get_sql_data(f"""SELECT max(timestamp) timestamp_forecast,site_name from forecast.db_api 
            group by site_name order by timestamp_forecast desc""")
            df_config = get_sql_data(f"""select site_name,client_name,state,capacity,site_status from 
                        configs.site_config""")
        # df_c = get_sql_data(query)
        df_act_fct = pd.merge(df_act, df_fcst, how='outer', on=['site_name'])
        df_c = pd.merge(df_act_fct,df_config,on=['site_name'])
        # df_c['Client Name'] = df_c['client_name'].map(lambda x: if x = )
        df_c['client_name'] = df_c['client_name'].fillna('In-House Development')
        # this is an important Line BRO
        # df_c['max_date_wrf'] = df_c.loc[df_c['source'] == 'WRF', 'max_date']
        # df_c['min_date_wrf'] = df_c.loc[df_c['source'] == 'WRF', 'min_date']
        # df_c['max_actual'] = df_c.loc[df_c['source'] == 'Actual', 'max_date']
        # df_c['max_date_wrf_str'] = df_c['max_date_wrf'].dt.strftime('%d/%m/%Y %H:%M:%S')
        # df_c['max_actual_str'] = df_c['max_actual'].dt.strftime('%d/%m/%Y %H:%M:%S')

        df_c['today'] = pd.to_datetime(datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
        # print(df_c)
        # ser = df_c['today'] - df_c['timestamp_actual']
        df_c['days_till'] = df_c['timestamp_actual'].map(lambda x: datetime.today() -x  if pd.notna(x) else None)
        df_c['days_till'] = df_c['days_till'].map(lambda x: x.days  if pd.notna(x) else None)
        # df_c['days_till'] = df_c['total_diff'].dt.days
        # df_c['days_till'] = ser.dt.days

        # df_c = df_c.groupby(['site_name', 'client_name', 'site_status', 'state']).aggregate(
        #     {'capacity': 'mean', 'max_date_wrf': 'max', 'max_actual': 'max', 'days_till': 'sum'})
        # df_c = df_c.reset_index()
        df_c['timestamp_forecast'] = df_c['timestamp_forecast'].dt.strftime('%d/%m/%Y %H:%M:%S')
        df_c['timestamp_actual'] = df_c['timestamp_actual'].map(lambda x: datetime.strftime(x,'%d/%m/%Y %H:%M:%S') if pd.notna(x) else None)
        if user_group == "Admin":
            send_list = ['site_name', 'client_name', 'site_status', 'state', 'capacity', 'max_date_wrf',
                         'max_actual', 'days_till']
        else:
            send_list = ['site_name', 'site_status', 'state', 'capacity', 'timestamp_forecast',
                         'timestamp_actual', 'days_till']
        df_c.fillna("Not Available",inplace=True)

        df_c = df_c.loc[:, send_list]
        df_c['capacity'] = df_c['capacity'].fillna("None")
        return JsonResponse({'data': df_c.to_dict('records')}, status=200, safe=False)


# Page 1
@login_required(login_url='client_login')
def overview_dash(request):
    context = {}
    return render(request, template_name='weatherapp/Overview.html', context=context)


# page 3
@login_required(login_url='client_login')
def forecast_warning(request):
    context = {}
    return render(request, template_name='weatherapp/Forecast_Warnings.html', context=context)


# Page 4
@login_required(login_url='client_login')
def warnings_dash(request):
    context = {}
    return render(request, template_name='weatherapp/Warnings.html', context=context)


def get_warnings_data(request):
    if request.method == "GET":
        client = request.GET['client']
        ci_index = int(request.GET['index'])
        ci_index = ci_index / 10
        # print(ci_index)
        yesterday = datetime.now()
        three_plus = datetime.now() + timedelta(hours=3)
        time_string = datetime.strftime(yesterday, '%Y-%m-%d %H:%M:%S')
        # query = "SELECT timestamp,site_lat,site_lon,site_name,forecast_cloud_index FROM " \
        #         f"dashboarding.v_final_dashboarding_view WHERE site_client_name ='{client}' AND " \
        #         f" timestamp > '{time_string}' ORDER BY timestamp DESC LIMIT 1000"
        query = f"""SELECT vda.site_name, vda.timestamp, vda.ci_data AS forecast_cloud_index, vda.tz, vda.ct_data, vda.ct_flag_data, 
            vda.forecast_method, vda.log_ts, conf.client_name, conf.latitude AS site_lat,
            conf.longitude AS site_lon FROM forecast.db_api vda JOIN configs.site_config conf ON vda.site_name = conf.site_name 
            LEFT JOIN site_actual.site_actual sa on (vda.timestamp,vda.site_name) = (sa.timestamp,sa.site_name) 
            WHERE conf.client_name = '{client}' AND vda.ci_data IS NOT NULL  AND vda.timestamp > '{time_string}'
              ORDER BY timestamp DESC"""
        fnl = get_sql_data(query)
        # print(query)
        # print(fnl)
        fnl['Warning Description'] = None
        fnl['Warning Category'] = None
        fnl.loc[fnl['forecast_cloud_index'] > 0.1, "Warning Category"] = "Red"
        fnl.loc[fnl['forecast_cloud_index'] <= 0.1, "Warning Category"] = "Green"
        fnl.loc[fnl['forecast_cloud_index'] > 0.1, "Warning Description"] = "Cloud Warning"
        fnl.loc[fnl['forecast_cloud_index'] <= 0.1, "Warning Description"] = "No Warning"
        # print(fnl.head(5))
        sites_list = list(fnl['site_name'].unique())
        sites_list.sort()
        # print(sites_list)
        fnl['timestamp'] = pd.to_datetime(fnl.timestamp)
        fnl['timestamp2'] = fnl['timestamp'].dt.strftime('%d %b %Y %H:%M')
        fnl['C_I_R'] = fnl['forecast_cloud_index'] * 100
        fn1 = fnl.groupby(['site_name', 'timestamp', 'Warning Description', 'Warning Category']).aggregate(
            {'site_lat': 'mean', 'site_lon': 'mean', 'forecast_cloud_index': 'mean', 'C_I_R': 'mean'}).reset_index()
        color_list = ['lightgreen', 'green', 'red', 'red', 'red', 'red', 'red', 'crimson', 'crimson', 'crimson']
        if ci_index > 0.1:
            replace_list = ['green'] * int(ci_index * 10)
            color_list[1:(int(ci_index * 10))] = replace_list
        # print(fn1)
        fig = px.scatter_mapbox(fn1
                                , lat='site_lat'
                                , lon='site_lon'
                                , center=dict(lat=20.59, lon=80.86),
                                size='C_I_R',
                                size_max=20,
                                hover_name='site_name',
                                hover_data=["timestamp", 'forecast_cloud_index', 'Warning Category']
                                , zoom=4,
                                color='forecast_cloud_index'
                                , opacity=0.4,
                                height=700,
                                color_continuous_scale=color_list
                                , mapbox_style='open-street-map')
        fig.update_coloraxes(showscale=False)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
            margin={'l': 0, 't': 0, 'b': 0, 'r': 0} )
        graphJSON = json.dumps(fig, cls=enc_pltjson)

        three_plus = datetime.now() + timedelta(hours=3)
        # print(three_plus)
        fn1 = fn1.loc[fn1['timestamp']<=three_plus,:]
        # print(fn1)
        # sites_list = list(fnl['site_name'].unique())
        # sites_list.sort()
        # print(sites_list)
        # print(fn1.info())
        fig2 = make_subplots(rows=len(sites_list), cols=1,subplot_titles = sites_list)
        for idx in range(len(sites_list)):
            fig2.add_trace(go.Bar(
                x=fn1.loc[fn1['site_name'] == sites_list[idx], 'timestamp'],
                y=fn1.loc[fn1['site_name'] == sites_list[idx], 'forecast_cloud_index'], name=sites_list[idx]),
                row=idx + 1, col=1)
            fig2.add_hline(y=0.1,line_width=1, line_dash="dash", line_color="grey", opacity=0.7,)
            fig2.update_yaxes( range=[0.0, 0.9], row=idx + 1, col=1)
        # print(fn1)
        fig.update_layout(height=700, title_text="Forecast Cloud Index")

        fig2.update_layout(height=700,showlegend=False,)
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
            margin={'l': 0, 't': 30, 'b': 0, 'r': 0})
        graphJSON2 = json.dumps(fig2, cls=enc_pltjson)

        return JsonResponse({'data': graphJSON,'histos':graphJSON2}, status=200, safe=False)




def get_homepage_data(request):
    if request.method == "GET":
        group = request.GET['group']
        client = request.GET['username']
        yesterday = datetime.now()
        time_string = datetime.strftime(yesterday, '%m-%d-%y %H:%M:%S')
        if group == "Admin":
            query = ""
        else:
            # query = "SELECT site_client_name,site_lat,site_lon,timestamp,ghi_forecast,ghi_actual,forecast_cloud_index," \
            #         f"site_name FROM dashboarding.v_final_dashboarding_view  WHERE site_client_name ='{client}' AND " \
            #         f"forecast_cloud_index IS NOT NULL AND timestamp > '{time_string}' ORDER BY timestamp DESC LIMIT 1000"
            query = f"""SELECT vda.site_name, vda.timestamp, vda.wind_speed_10m_mps AS wind_speed_forecast, 
            vda.wind_direction_in_deg AS wind_direction_forecast, vda.temp_c AS wind_direction_forecast, 
            vda.nowcast_ghi_wpm2 AS ghi_forecast, vda.swdown2,vda.ci_data AS forecast_cloud_index, vda.tz, vda.ct_data, vda.ct_flag_data, 
            vda.forecast_method, vda.log_ts, conf.client_name, conf.latitude AS site_lat,
            conf.longitude AS site_lon, sa."ghi(w/m2)" AS ghi_actual, 
            sa."temp(c)" AS temp_actual, sa.ws AS wind_speed_actual, sa.wd AS wind_direction_actual 
            FROM forecast.db_api vda JOIN configs.site_config conf ON vda.site_name = conf.site_name 
            LEFT JOIN site_actual.site_actual sa on (vda.timestamp,vda.site_name) = (sa.timestamp,sa.site_name) 
            WHERE conf.client_name = '{client}' AND vda.ci_data IS NOT NULL  AND vda.timestamp > '{time_string}'
              ORDER BY timestamp DESC"""
        ci_index = 0.1
        df = get_sql_data(query)

        df = df.groupby(['timestamp','site_name','client_name']).aggregate({'ghi_forecast':'mean','ghi_actual':'mean','forecast_cloud_index':'mean','site_lat':'mean','site_lon':'mean'}).reset_index()

        df['C_I_R'] = df['forecast_cloud_index'] * 100
        df['Warning Description'] = None
        df['Warning Category'] = None
        df['Graph Index'] = None
        df.loc[df['forecast_cloud_index'] > 0.1, "Warning Category"] = "Red"
        df.loc[df['forecast_cloud_index'] <= 0.1, "Warning Category"] = "Green"
        df.loc[df['forecast_cloud_index'] > 0.1, "Warning Description"] = "Cloud Warning"
        df.loc[df['forecast_cloud_index'] <= 0.1, "Warning Description"] = "No Warning"

        for x in df.loc[:, 'forecast_cloud_index'].index:
            if df['forecast_cloud_index'][x] > ci_index:
                df['Graph Index'][x] = df[f'ghi_forecast'][x]

        # fn1 = df.groupby(['site_name', 'timestamp', 'Warning Description', 'Warning Category']).aggregate(
        #     {'site_lat': 'mean', 'site_lon': 'mean', 'forecast_cloud_index': 'mean', 'C_I_R': 'mean'}).reset_index()
        color_list = ['lightgreen', 'green', 'red', 'red', 'red', 'red', 'red', 'crimson', 'crimson', 'crimson']

        fig = px.scatter_mapbox(df
                                , lat='site_lat'
                                , lon='site_lon'
                                , center=dict(lat=20.59, lon=80.86),
                                size='C_I_R',
                                size_max=20,
                                hover_name='site_name',
                                hover_data=["timestamp", 'forecast_cloud_index', 'Warning Category']
                                , zoom=3,
                                color='forecast_cloud_index'
                                , opacity=0.4,
                                height=350,
                                color_continuous_scale=color_list
                                , mapbox_style='open-street-map')
        fig.update_coloraxes(showscale=False)
        fig.update_layout(
            margin={'l': 0, 't': 0, 'b': 0, 'r': 0},showlegend=False,paper_bgcolor='rgb(0,0,0)' )
        graphJSON = json.dumps(fig, cls=enc_pltjson)

        variable = 'ghi'

        # df = df.groupby(['timestamp',''])
        # df_sites = pd.read_csv("static/client_site.csv")
        df_sites = get_site_client()
        sites = list(df_sites.loc[df_sites['client_name']==client,'site_name'])
        df = df.loc[df['site_name']==sites[0]]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[f'{variable}_actual'],
            name=f"{variable.title()} Actual"
        ))
        fig2.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[f'{variable}_forecast'],
            name=f"{variable.title()} Forecast"
        ))
        fig2.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['Graph Index'],
                name='Cloud Warning',
                mode='markers',
                marker_color='orange',
                marker_size=10
            )
        )
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',

            height=500,
            xaxis_title="Timestamp",
            yaxis_title="GHI (W/m2)",
            # legend_title="Legends",

            font=dict(
                family="Arial",
                size=15,
            ),
            margin=dict(
                l=10,
                r=10,
                b=10,
                t=10,
                pad=1
            ),
        )
        graphJSON2 = json.dumps(fig2, cls=enc_pltjson)
        return JsonResponse({'maps_data': graphJSON,'graphs_data':graphJSON2}, status=200, safe=False)
        # if is_ajax(request):
        #     username = request.GET['username']
        #     group = request.GET['group']
        #
        #     # This is the bog One
        #     # The Table 1 Data
        #     return JsonResponse({'data':"Hello World"},status=200,safe=False)
        # else:
        #     return redirect('403')
# @login_required('client_login')
# def user_update(request,id:int):
#     user_details = Clients.objects.get(id=id)
#     if len(user_details.username)<0:
#         return redirect('homepage')
#     else:
#         form = ClientsForm(data=user_details)
#         return render(request,template_name='weatherapp/update_user.html',context={'form':form})
