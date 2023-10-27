# %%
import pandas as pd
import numpy as np
import dash
from dash import Dash, html, dcc, Input, Output, ctx, callback
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# %%
date_df = pd.read_csv('https://raw.githubusercontent.com/BabbarGaurav/Dash/main/Input%20Files/dim_date.csv?token=GHSAT0AAAAAACI4MUWAWPOFUH3H3SE7IHRUZJMHZNQ')
hotel_df = pd.read_csv('https://raw.githubusercontent.com/BabbarGaurav/Dash/main/Input%20Files/dim_hotels.csv?token=GHSAT0AAAAAACI4MUWBZNIZZ7ZAZVSWUAH4ZJMHZTQ')
room_df = pd.read_csv('https://raw.githubusercontent.com/BabbarGaurav/Dash/main/Input%20Files/dim_rooms.csv?token=GHSAT0AAAAAACI4MUWATADK4QNXUY64FLXGZJMH2WA')
agg_df = pd.read_csv('https://raw.githubusercontent.com/BabbarGaurav/Dash/main/Input%20Files/fact_aggregated_bookings.csv?token=GHSAT0AAAAAACI4MUWAQUQ7OP7ZKL3B2HLIZJMH26Q')
booking_df = pd.read_csv('https://raw.githubusercontent.com/BabbarGaurav/Dash/main/Input%20Files/fact_bookings.csv?token=GHSAT0AAAAAACI4MUWAUR2KXTZ3LGFM3LFOZJMH3JA')

# %%
# Convert the 'date' column to datetime data type
date_df['date'] = pd.to_datetime(date_df['date'])

# Extract and convert 'week no' to an integer
date_df['week no'] = date_df['week no'].str.extract('(\d+)').astype(int)

#Including a new column to identify which are sundays
date_df['day_of_week'] = date_df['date'].dt.day_name()

#Correcting day_type based on information provided by stackholders about sunday
date_df['day_type'] = date_df['day_type'].replace({'weekeday': 'weekday'})
date_df.loc[date_df['day_of_week'] == 'Sunday', 'day_type'] = 'weekday'

# Convert 'check_in_date' to datetime data type
agg_df['check_in_date'] = pd.to_datetime(agg_df['check_in_date'])

# Convert date columns to datetime data type
booking_df['booking_date'] = pd.to_datetime(booking_df['booking_date'])
booking_df['check_in_date'] = pd.to_datetime(booking_df['check_in_date'])
booking_df['checkout_date'] = pd.to_datetime(booking_df['checkout_date'])


date_df = date_df.rename(columns={'date': 'check_in_date'})
room_df = room_df.rename(columns={'room_id': 'room_category'})

#merge df
booking_df = pd.merge(booking_df, date_df, on='check_in_date', how='inner')

booking_df = pd.merge(booking_df, hotel_df, on='property_id', how='inner')

booking_df = pd.merge(booking_df, room_df, on='room_category', how='inner')

booking_df = pd.merge(booking_df, agg_df, on = ['property_id','check_in_date', 'room_category'], how = 'inner')

booking_df["month"] = booking_df["check_in_date"].dt.strftime("%B")
booking_df = booking_df.drop(columns=["mmm yy"])


# %%
total_revenue = booking_df['revenue_realized'].sum()

total_bookings = len(booking_df)

total_capacity = agg_df['capacity'].sum()

total_successful_bookings = booking_df.groupby(['property_id', 'check_in_date','room_category']).size().reset_index(name='successful_booking')['successful_booking'].sum()

occupancy_percentage = (total_successful_bookings / total_capacity) * 100

average_rating = booking_df['ratings_given'].mean()

no_of_days = booking_df['check_in_date'].max() - booking_df['check_in_date'].min()

total_cancelled_bookings = len(booking_df[booking_df['booking_status'] == 'Cancelled'])

cancellation_percentage = (total_cancelled_bookings / total_bookings) * 100

total_checked_out = len(booking_df[booking_df['booking_status'] == 'Checked out'])

total_no_show_bookings = len(booking_df[booking_df['booking_status'] == 'No Show'])

no_show_rate_percentage = (total_no_show_bookings / total_bookings) * 100

booking_platform_percentages = booking_df['booking_platform'].value_counts(normalize = True) * 100

room_class_percentages = booking_df['room_class'].value_counts(normalize = True)*100

adr = booking_df['revenue_generated'].sum() / total_bookings

realisation_percentage = total_checked_out / total_bookings

revpar = total_revenue / total_capacity

booking_df['occupancy'] = (booking_df['successful_bookings'] / booking_df['capacity']) * 100


# %%
k = booking_df.groupby('property_name')[['revenue_realized','occupancy','ratings_given']].agg(
    total_booking=('revenue_realized', 'size'),
    total_revenue=('revenue_realized', 'sum'),
    average_occupancy=('occupancy', 'mean'),
    average_ratings=('ratings_given', 'mean')
).reset_index()

k = k.rename(columns={
    'property_name': 'Property',
    'total_booking': 'Total Bookings',
    'total_revenue': 'Total Revenue',
    'average_occupancy': 'Average Occupancy',
    'average_ratings': 'Average Ratings'
})

k['Average Occupancy'] = k['Average Occupancy'].round(2)
k['Average Ratings'] = k['Average Ratings'].round(2)

# %%
# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

logo = 'https://d1muf25xaso8hp.cloudfront.net/https%3A%2F%2Ff2fa1cdd9340fae53fcb49f577292458.cdn.bubble.io%2Ff1663995322968x622558936746862000%2FAtliq%2520A%2520logo-04.png'


def your_filtering_function(selected_cities, selected_room_classes, selected_months):
    # Filter the data based on selected cities and room classes
    if not selected_cities and not selected_room_classes and not selected_months:
        # No filters selected, return total revenue for all data
        return booking_df
    else:
        # Apply filters based on selected cities and room classes
        filtered_data = booking_df
        if selected_cities:
            filtered_data = filtered_data[filtered_data['city'].isin(selected_cities)]
        if selected_room_classes:
            filtered_data = filtered_data[filtered_data['room_class'].isin(selected_room_classes)]
        if selected_months:
            filtered_data = filtered_data[filtered_data['month'].isin(selected_months)]

        return filtered_data

# Define the content of the navbar
navbar = dbc.Navbar(
    id='navbar',
    children=[
        dbc.Row([
            dbc.Col(
                html.Img(
                    src=logo,
                    height="50px",
                ),
            ),
            dbc.Col(
                dbc.NavbarBrand("Analytics Dashboard", style={"color": "Black", "fontSize": "30px", "fontFamily": "Helvetica", "fontWeight": "bold"}),
            ),
        ],
    )], color = '#f5d3cb')

# Create a card component without the extra level of nesting
chipgroup = dbc.CardBody(
    [
        dbc.Row([
            dbc.Col([
                html.H6('Filter by City'),
                dmc.ChipGroup(
                    [
                        dmc.Chip(
                            x,
                            value = x,
                            variant = 'filled',
                            size = 'sm',
                            radius = 'sm',
                        )
                        for x in hotel_df.sort_values('city')['city'].unique()
                    ],
                    id = 'city-filter',
                    multiple=True,
                )
            ])
            ]),
        
        html.Hr(),

        dbc.Row([
            dbc.Col([
                html.H6('Filter by Room Category'),
                dmc.ChipGroup(
                    [
                        dmc.Chip(
                            x,
                            value = x,
                            variant = 'filled',
                            size = 'sm',
                            radius = 'sm',
                        )
                        for x in room_df.sort_values('room_class')['room_class'].unique()
                    ],
                    id='room-class-filter',
                    multiple=True,
                )
            ])
            ]),
        html.Hr(),

        dbc.Row([
            dbc.Col([
                html.H6('Filter by Month'),
                dmc.ChipGroup(
                    [
                        dmc.Chip(
                            x,
                            value = x,
                            variant = 'filled',
                            size = 'sm',
                            radius = 'sm',
                        )
                        for x in booking_df['month'].unique()
                    ],
                    id='month-filter',
                    multiple=True,
                )
        ])
    ])
])

filters = dmc.Navbar(
            p="xl",
            width={"base": 400},
            height=1000,
            fixed=False,
            position={"left": 0, "top": 400},
            children=[
               dbc.Card(chipgroup)
            ]
)

table = dag.AgGrid(
    id = 'property-level',
    rowData = k.to_dict('records'),
    columnDefs = [{'field': i} for i in k.columns],
)

layout = dbc.Container([
            html.Br(),
                dmc.SimpleGrid(
                    cols=4,
                    children=[
                    dbc.Col([dbc.Card(id='card_num1', style = {'height':'150px'})]),
                    dbc.Col([dbc.Card(id='card_num2', style = {'height':'150px'})]),
                    dbc.Col([dbc.Card(id='card_num3', style = {'height':'150px'})]),
                    dbc.Col([dbc.Card(id='card_num4', style = {'height':'150px'})])
                    ]
                ),
            html.Br(),
                dbc.Row([
                    dbc.Col([dbc.Card(id='card_num5')], width = 7),
                    dbc.Col([dbc.Card(id='card_num6')])
                ]),
            html.Br(),
                dbc.Row([dbc.Card(id='card_num7', style = {'height':'200px'})]),
                dbc.Row([dbc.Card(id='card_num8')])
            ])


# Define the layout of your dashboard
app.layout = dbc.Container(
    [
        navbar,
        dbc.Row([
            dbc.Col([
                filters,layout
            ],style ={'display':'flex'})
        ]),
    ],fluid=True,
)




# Create a callback function to update the filter values
@app.callback([Output('card_num1', 'children'),
               Output('card_num2', 'children'),
               Output('card_num3', 'children'),
               Output('card_num4', 'children'),
               Output('card_num5', 'children'),
               Output('card_num6', 'children'),
               Output('card_num7', 'children'),
               Output('card_num8', 'children')],
              [Input('city-filter', 'value'),
               Input('room-class-filter', 'value'),
               Input('month-filter', 'value')])
               

def update_filtered_data(selected_cities, selected_room_classes,selected_months):

    # Get the filtered data using the filtering function
    filtered_data = your_filtering_function(selected_cities, selected_room_classes, selected_months)

    # Calculate the total revenue based on the filtered data
    total_revenue_filtered = filtered_data['revenue_realized'].sum()
    occupancy_percentage_ = (filtered_data.groupby(['property_id', 'check_in_date','room_category']).size().reset_index(name='successful_booking')['successful_booking'].sum() / filtered_data.groupby(['property_id','room_class', 'check_in_date'])['capacity'].max().reset_index()['capacity'].sum()) * 100
    average_rating_ = filtered_data['ratings_given'].mean()
    cancellation_percentage_     = (len(filtered_data[filtered_data['booking_status'] == 'Cancelled']) / len(filtered_data)) * 100
    weekly_revenue = filtered_data.groupby(['week no'])['revenue_realized'].sum().reset_index()
    platform_breakup = filtered_data[filtered_data['booking_status']=='Cancelled'].groupby(['booking_platform','booking_status']).size().reset_index(name ='count')
    f = filtered_data[filtered_data['day_type'] == 'weekday'].groupby(['city', 'day_type'])['revenue_realized'].sum().reset_index()
    f['%']= (f['revenue_realized'] / f['revenue_realized'].sum()) * 100
    
    fig1 = go.Figure(go.Indicator(
                            mode = "number",
                            value = total_revenue_filtered,
                                )
                   )
    
    fig1.update_layout(
        height=80,  # You can adjust the height as needed
        margin=dict(l = 10, r = 10, t = 20, b = 20),
    )    
    
    fig2 = go.Figure(go.Indicator(
                            mode = "number",
                            value = occupancy_percentage_,
                            number = {'suffix': "%"}
                                )
                    )
    
    fig2.update_layout(
        height=80,  # You can adjust the height as needed
        margin=dict(l = 10, r = 10, t = 20, b = 20),
    )  
    
    fig3 = go.Figure(go.Indicator(
                            mode = "number",
                            value = average_rating_,
                                )
                    )
    
    fig3.update_layout(
        height=80,  # You can adjust the height as needed
        margin=dict(l = 10, r = 10, t = 20, b = 20),
    )
    
    fig4 = go.Figure(go.Indicator(
                            mode = "number",
                            value = cancellation_percentage_,
                            number = {'suffix': "%"}
                                )
                   )
    
    fig4.update_layout(
        height=80,  # You can adjust the height as needed
        margin=dict(l = 10, r = 10, t = 20, b = 20),
    )  


    

    fig5 = go.Figure(go.Scatter(
                            x = weekly_revenue['week no'],
                            y = weekly_revenue['revenue_realized'],
                            mode = 'lines + markers',
                            name = 'Revenue'
                                )
                   )

    fig5.update_layout(
        margin=dict(l = 30, r = 30, t = 30, b = 30),
    )



    fig6 = go.Figure(data=[go.Pie(
                            labels = platform_breakup["booking_platform"],
                            values = platform_breakup["count"],
                            hole=.4,
                            textinfo='label+percent+value',
                            textposition = 'outside',
                            pull=[0.2]
                            )])

    fig6.update_layout(
        margin = dict(l = 30, r = 30, t = 20, b = 20),
        showlegend = False) 
                     


    fig7 = px.bar(f,
            x= '%',
            y= 'day_type',
            color = 'city',
            orientation = 'h',
            text_auto='.2f',
            height = 160,
    )

    fig7.update_layout(
            xaxis_title='',  # Remove x-axis title
            yaxis_title='',  # Remove y-axis title
            showlegend=True,  # Display the legend
            legend_orientation="h",  # Move the legend to the top
            legend_y=1.45,  # Adjust the legend position
            legend_x=0.5,  # Center the legend horizontally
            legend_bgcolor='rgba(0, 0, 0, 0)',  # Make the legend background transparent
            legend_title_text='City',
            margin = dict(l = 10, r = 10, t = 30, b = 30),
    )



    # Define the content for card1 & card2
    
    card1_content = [
        dbc.CardBody(
                [
                html.H6('Revenue', style = {'fontWeight':'bold', 'fontSize':'18px','textAlign':'center'}),
                dcc.Graph(figure = fig1)
                ]),  
    ]
    
    card2_content = [
        dbc.CardBody(
                [
                html.H6('Occupancy %', style = {'fontWeight':'bold', 'fontSize':'18px','textAlign':'center'}),
                dcc.Graph(figure = fig2)
                ]),  
    ]
    
    card3_content = [
        dbc.CardBody(
                [
                html.H6('Average Rating', style = {'fontWeight':'bold', 'fontSize':'18px','textAlign':'center'}),
                dcc.Graph(figure = fig3)
                ]),  
    ]
        
    card4_content = [
        dbc.CardBody(
                [
                html.H6('Cancellation %', style = {'fontWeight':'bold', 'fontSize':'18px','textAlign':'center'}),
                dcc.Graph(figure = fig4)
                ]),  
    ]
    
    card5_content = [
            dbc.CardBody(
                [
                dcc.Graph(figure = fig5)
                ]
            )
    ]


    card6_content = [
            dbc.CardBody(
                [
                dcc.Graph(figure = fig6)
                ]
            )
    ]


    card7_content = [
            dbc.CardBody(
                [
                dcc.Graph(figure = fig7)
                ]
            )
    ]


    card8_content = [
            dbc.CardBody(
                [
                table
                ]
            )
    ]

    return card1_content, card2_content, card3_content, card4_content, card5_content, card6_content, card7_content, card8_content


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
