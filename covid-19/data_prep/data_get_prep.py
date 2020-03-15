import pandas as pd
import requests
import numpy as np
from plotly import graph_objs as go
import plotly.express as px

url_timeseries_confirmed = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
url_timeseries_deaths = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
url_timeseries_recovered = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'


confirmed = pd.read_html(requests.get(url_timeseries_confirmed).content)[-1]  #.to_csv(<csv file>)
deaths = pd.read_html(requests.get(url_timeseries_deaths).content)[-1]
recovered = pd.read_html(requests.get(url_timeseries_recovered).content)[-1]


col_to_drop = 'Unnamed: 0'
confirmed.drop([col_to_drop],axis = 1, inplace =True)
deaths.drop([col_to_drop],axis = 1, inplace =True)
recovered.drop([col_to_drop],axis = 1, inplace =True)

confirmed.rename(columns={"Country/Region":"Country"} ,inplace =True)
deaths.rename(columns={"Country/Region":"Country"} , inplace =True)
recovered.rename(columns={"Country/Region":"Country"} , inplace =True)


def prep_data(df):
    countries = df['Country'].unique().tolist()
    data_per_country = df.groupby(['Country']).sum().iloc[:, 2:]
    totals_country = data_per_country.iloc[:, -1]
    totals_day = data_per_country.sum(axis=0)
    num_days = len(data_per_country.columns)
    data_rates = data_per_country.copy()

    for i, row in enumerate(data_rates.iterrows()):
        first_case = next((index for index, value in enumerate(row[1]) if value != 0), len(row[1]))
        divider = list(range(1, len(row[1]) - (first_case) + 1))
        padding = [1 for i in range(0, first_case)]
        divider = padding + divider
        data_rates.iloc[i] = data_rates.iloc[i] / divider

    return data_per_country, totals_country, totals_day, data_rates


def melt_data(df, subject_column):
    df = df.T.reset_index().rename(columns={"index": "date"})
    df = df.melt(id_vars='date', value_vars=list(df.columns[1:]))
    df.rename(columns={"value": subject_column}, inplace=True)
    # df_recovered
    df = df.sort_values(by=['Country'], ascending=False)
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
    df.sort_values(by=['date'], inplace=True)
    df['date'] = df.date.apply(str)
    return df


dpc_confirmed, tc_confirmed, td_confirmed, rates_confirmed = prep_data(confirmed)
dpc_recovered, tc_recovered, td_recovered, rates_recovered = prep_data(recovered)
dpc_deaths, tc_deaths, td_deaths, rates_deaths = prep_data(deaths)



figures = []

tc_confirmed.name = 'confirmed'
tc_recovered.name = 'recovered'
tc_deaths.name = 'deaths'
global_overview = pd.concat([tc_confirmed, tc_recovered,tc_deaths], axis=1).sort_values(by= ['confirmed'])
data = [
        go.Bar(x= global_overview.index, y= global_overview.confirmed , name='confirmed' , marker_color = "blue"),
        go.Bar(x= global_overview.index, y= global_overview.recovered, name='recovered',marker_color = "green"),
        go.Bar(x= global_overview.index, y= global_overview.deaths, name='deaths',marker_color = "red" )
       ]

layout = go.Layout(
    barmode='overlay',
    yaxis_type ="log",title = "Global Overview of confirmed,recovered and deaths per country",width = 1650,
    yaxis_title = "Number of Cases (Log Scale)"
)

global_countries = go.Figure(data = data, layout = layout)
figures.append(global_countries)

td_confirmed.name = 'confirmed'
td_recovered.name = 'recovered'
td_deaths.name = 'deaths'
time_overview = pd.concat([td_confirmed, td_recovered,td_deaths], axis=1).sort_values(by= ['confirmed'])

data = [
        go.Bar(x= time_overview.index, y= time_overview.confirmed , name='confirmed' , marker_color = "blue"),
        go.Bar(x= time_overview.index, y= time_overview.recovered, name='recovered',marker_color = "green"),
        go.Bar(x= time_overview.index, y= time_overview.deaths, name='deaths',marker_color = "red" )
       ]

layout = go.Layout(
    barmode='overlay',title = "Global Overview of confirmed,recovered and deaths per day ",width = 1650
)

global_days = go.Figure(data = data, layout = layout)
figures.append(global_days)

china_rates = pd.concat([dpc_confirmed.loc['China'] / list(range(1, len(dpc_confirmed.loc['China']) + 1)),
                         dpc_recovered.loc['China'] / list(range(1, len(dpc_recovered.loc['China']) + 1)),
                         dpc_deaths.loc['China'] / list(range(1, len(dpc_deaths.loc['China']) + 1))], axis=1)
china_rates.columns = ['confirmed_rate', 'recovered_rate', 'death_rate']
data = [
    go.Scatter(x=china_rates.index, y=china_rates.death_rate, name='deaths rate', marker_color="red", fill='tonexty'),
    go.Scatter(x=china_rates.index, y=china_rates.recovered_rate, name='recovered rate', marker_color="green",
               fill='tonexty'),
    go.Scatter(x=china_rates.index, y=china_rates.confirmed_rate, name='confirmed rate', marker_color="blue",
               fill='tonexty'),

]

layout = go.Layout(
    yaxis_type="linear",
    title="Chinas confirmed,recovered and death rates per day<br>How well is the China handling the virus?", width=1650,
    yaxis_title="persons per day"
)

china_rates_fig = go.Figure(data=data, layout=layout)
china_rates_fig.update_traces(mode="lines+markers")
figures.append(china_rates_fig)

global_rates = pd.concat(
    [(td_confirmed / list(range(1, len(td_confirmed) + 1))), (td_recovered / list(range(1, len(td_recovered) + 1))),
     (td_deaths / list(range(1, len(td_deaths) + 1)))], axis=1).rename(
    columns={'confirmed': 'confirmed_rate', 'recovered': 'recovered_rate', 'deaths': 'death_rate'})


data = [
    go.Scatter(x=global_rates.index, y=global_rates.death_rate-china_rates.death_rate, name='death rate',
               marker_color="red", fill='tonexty'),
    go.Scatter(x=global_rates.index, y=global_rates.recovered_rate-china_rates.recovered_rate, name='recovered rate',
               marker_color="green", fill='tonexty'),
    go.Scatter(x=global_rates.index, y=global_rates.confirmed_rate-china_rates.confirmed_rate, name='confirmed rate',
               marker_color="blue", fill='tonexty'),

]

layout = go.Layout(
    yaxis_type="linear",
    title="Rest of the World confirmed,recovered and death rates per day<br>How well is the world handling the virus?",
    width=1650,
    yaxis_title="persons per day"
)

global_rates_fig = go.Figure(data=data, layout=layout)
global_rates_fig.update_traces(mode="lines+markers")
figures.append(global_rates_fig)

world_map_confirmed = px.choropleth(global_overview, locations=global_overview.index,
                    locationmode = "country names",
                    color=np.log(global_overview.confirmed),
                    hover_name=global_overview.index,
                    hover_data = ["confirmed"],
                    projection = "orthographic",
                   color_continuous_scale="blues",
                   range_color= [0,np.log(global_overview.confirmed).max()],
                   )
world_map_confirmed.update_layout( coloraxis_colorbar = dict(title = "Confirmed (Log scale)"  ))
figures.append(world_map_confirmed)


world_map_deaths = px.choropleth(global_overview, locations=global_overview.index,
                    locationmode = "country names",
                    color=np.log(global_overview.deaths),
                    hover_name=global_overview.index,
                    hover_data = ["deaths"],
                    projection = "orthographic",
                   color_continuous_scale="reds",
                   range_color= [0,np.log(global_overview.deaths).max()],
                   )
world_map_deaths.update_layout( coloraxis_colorbar = dict(title = "Deaths (Log scale)"  ))
figures.append(world_map_deaths)

world_map_recovered = px.choropleth(global_overview, locations=global_overview.index,
                    locationmode = "country names",
                    color=np.log(global_overview.recovered),
                    hover_name=global_overview.index,
                    hover_data = ["recovered"],
                    projection = "orthographic",
                   color_continuous_scale="greens",
                   range_color= [0,np.log(global_overview.recovered).max()],
                   )
world_map_recovered.update_layout( coloraxis_colorbar = dict(title = "Recovered (Log scale)"  ))
figures.append(world_map_recovered)


rates_con_plot = melt_data(rates_confirmed,'Confirmation_Rates')

top_10_countires = list(tc_confirmed.sort_values(ascending= False)[:10].index)

rates_con_plot['Confirmation_Rates'] = rates_con_plot.Confirmation_Rates.replace([np.inf, -np.inf], np.nan)
rates_con_plot = rates_con_plot.dropna()

rates_con_plot = rates_con_plot.loc[rates_con_plot.Country.isin(top_10_countires)  &  (rates_con_plot.Confirmation_Rates != 0)]


rates_con_fig = px.scatter(rates_con_plot,x = 'date' ,y = 'Confirmation_Rates' ,log_y=True ,range_y = [rates_con_plot.Confirmation_Rates.min(),rates_con_plot.Confirmation_Rates.max() ], \
                           color = 'Country', height = 500
                          ,title = "Confirmation rates for top 10 countries with highest confirmed cases <br>persons per day from first confirmed cases")

rates_con_fig.update_traces(mode = "lines+markers" ,line = dict(shape = 'spline') )
rates_con_fig.update_layout(xaxis_title = "Notice the increase in confirmed rates after 20 Feb , did testing get better ? is the virus spreading faster ?",
                           yaxis_title = "Confirmation rates")
figures.append(rates_con_fig)


rates_rec_plot = melt_data(rates_recovered,'Recovery_Rates')

top_10_countires = list(tc_recovered.sort_values(ascending= False)[:10].index)

rates_rec_plot['Recovery_Rates'] = rates_rec_plot.Recovery_Rates.replace([np.inf, -np.inf], np.nan)
rates_rec_plot = rates_rec_plot.dropna()

rates_rec_plot = rates_rec_plot.loc[rates_rec_plot.Country.isin(top_10_countires)  &  (rates_rec_plot.Recovery_Rates != 0)]


rates_rec_fig = px.line(rates_rec_plot,x = 'date' ,y ='Recovery_Rates',log_y=True ,range_y = [rates_rec_plot.Recovery_Rates.min(),rates_rec_plot.Recovery_Rates.max() ],
                           color = 'Country', height = 500
                          ,title = "Recovery rates for top 10 countries with highest recovery cases <br>persons per day from first confirmed cases")

rates_rec_fig.update_traces(mode = "lines+markers",line = dict(shape = 'spline')  )
rates_rec_fig.update_layout(xaxis_title = "We would like to see this sharply increasing over the days to come,<br>notice recovery rates increase after 5th March,<br>also notice the drop in recovery at the beginning",
                           yaxis_title = "Recovery rates")
figures.append(rates_rec_fig)

rates_de_plot = melt_data(rates_deaths,'Death_Rates')

top_10_countires = list(tc_recovered.sort_values(ascending= False)[:10].index)

rates_de_plot['Death_Rates'] = rates_de_plot.Death_Rates.replace([np.inf, -np.inf], np.nan)
rates_de_plot = rates_de_plot.dropna()

rates_de_plot = rates_de_plot.loc[rates_de_plot.Country.isin(top_10_countires)  &  (rates_de_plot.Death_Rates != 0)]


rates_dea_fig = px.scatter(rates_de_plot,x = 'date' ,y ='Death_Rates',log_y=True ,range_y = [rates_de_plot.Death_Rates.min(),rates_de_plot.Death_Rates.max() ],
                           color = 'Country', height = 500
                          ,title = "Death rates for top 10 countries with highest death cases <br>persons per day from first confirmed cases")

rates_dea_fig.update_traces(mode = "lines+markers",line = dict(shape = 'spline')  )

rates_dea_fig.update_layout(xaxis_title = "We hope to see a sharp decline here as the days progress, Notice countries that are possibly doing a good job combating the virus",
                           yaxis_title = "Death rates")
figures.append(rates_dea_fig)


def multi_plot(df):
    fig = go.Figure()
    countries = df.Country.unique().tolist()
    for country in countries:
        specic_df = df.loc[df.Country == country]
        for column in df.columns[-3:].to_list():
            fig.add_trace(
                go.Scatter(
                    x=specic_df.date,
                    y=specic_df[column],
                    name=column,
                    visible=False
                )
            )

    button_none = dict(label='None',
                       method='update',
                       args=[{'visible': list(np.array([0 for i in range(0, len(countries) * 3)]) == 1),
                              'title': 'None',
                              'showlegend': True}])

    def activate(country):
        selector_list = [0 for i in range(0, len(countries) * 3)]
        index = countries.index(country)
        starter_index = index * 3
        for i in range(0, 3):
            selector_list[starter_index + i] = 1
        return list(np.array(selector_list) == 1)

    def create_layout_button(country):
        return dict(label=country,
                    method='update',
                    args=[{'visible': activate(country),
                           'title': country,
                           'showlegend': True}])

    fig.update_layout(yaxis_title="Persons per day", title="Drag scroll bar to scroll:",
                      updatemenus=[go.layout.Updatemenu(
                          active=1,
                          buttons=[button_none] + list(map(create_layout_button, countries)),
                          x=0.15,
                          y=1.13

                      )
                      ])
    fig.update_traces(mode="lines+markers", line=dict(shape='spline'))

    return fig


multi_plot_df = melt_data(rates_deaths, 'Death_Rates')
multi_plot_df['Confirmed_Rates'] = melt_data(rates_confirmed, 'Confirmed_Rates').Confirmed_Rates
multi_plot_df['Recovered_Rates'] = melt_data(rates_recovered, 'Recovered_Rates').Recovered_Rates

multi_plot_fig = multi_plot(multi_plot_df)

figures.append(multi_plot_fig)


def return_figs():
   return figures

def get_totals():
    return td_confirmed[-1],td_recovered[-1],td_deaths[-1]





