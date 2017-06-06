from django.shortcuts import render
from django.utils import timezone
import sys
sys.path.append("./lib")
import nrel
import inst_size_cost
import pandas as pd
import sqlite3
import os
import pickle
import numpy as np

db_file = "./solar_logs.sqlite"
conn = sqlite3.Connection(db_file, check_same_thread=False)

# reading in elastic net model for output
en_filename = 'finalized_en_model.sav'
en_model = pickle.load(open(en_filename, 'rb'))

# data on annual rates to calculate return
rates = pd.read_csv("./average_annual_rates.csv")

print "Loading Scaler"
scaler = pickle.load(open("standard_scaler.pkl", 'rb'))

def about(request):

    return render(request, 'solar_output_prediction/about.html')

def model(request):

    # Setting defaults for variables.
    dhi=None
    dni=None
    lat=None
    lon=None
    temp=None
    wind_speed=None
    cost=None
    form_message=None
    solar_message=None
    prediction = None
    size_kw = None
    azimuth = None
    prediction = None
    annual_savings = None
    break_even = None

    predictions_made = False

    # setting these as user defaults, could be updated to be a prompt for the user.
    tracking_type = "no_tracking"
    tech_1 = "Poly"

    # Everything Within this is what to do after someone has submitted.
    if request.method == "POST":

        address_1 = str(request.POST.get("address-line1"))
        address_2 = str(request.POST.get("address-line2"))
        city = str(request.POST.get("city"))
        state = str(request.POST.get("state"))
        zipcode = str(request.POST.get("zipcode"))

        # looping through items and if they exist adding them to user_address
        user_address = ''
        address_items = [address_1, address_2, city, state, zipcode]
        for i, item in enumerate(address_items):
            if item:
                if i != len(address_items) - 1:
                    user_address += item + ', '
                else:
                    user_address += item

        print "user_address: ", user_address

        user_area=None
        user_tilt=None
        try:
            user_area = float(request.POST.get("Area"))
            user_tilt = float(request.POST.get("Tilt"))
        except:
            form_message = "Please enter all fields"

        if request.POST.get("Direction") == "N":
            azimuth = 0
        elif request.POST.get("Direction") == "NE":
            azimuth = 45
        elif request.POST.get("Direction") == "E":
            azimuth = 90
        elif request.POST.get("Direction") == "SE":
            azimuth = 135
        elif request.POST.get("Direction") == "S":
            azimuth = 180
        elif request.POST.get("Direction") == "SW":
            azimuth = 225
        elif request.POST.get("Direction") == "W":
            azimuth = 270
        elif request.POST.get("Direction") == "NW":
            azimuth = 315

        # Calculating cost and size_kw capcity of installation:
        if user_area is not None:
            cost_size_calc = inst_size_cost.solar_installation_size_cost(user_area)
            size_kw = cost_size_calc.calculate_size_kw()
            print "Array Size: ", size_kw
            cost = cost_size_calc.calculate_cost()
            # cost = "$" + round(cost, 2)
            form_message = None
            solar_message = "Size Calculated"
        else:
            form_message = "Please enter all fields."

        geo_data_collected=False
        if zipcode is not None:
            solar_data = pd.read_sql('select * from zipcode_data where Zipcode = "%s"' % str(zipcode), con=conn)
            if len(solar_data) > 0:
                dhi = solar_data['DHI'].values[0]
                dni = solar_data['DHI'].values[0]
                lat = "unnecessary"
                lon = "unnecessary"
                temp = solar_data['Temperature'].values[0]
                wind_speed = solar_data['Wind Speed'].values[0]
                geo_data_collected=True
            else:
                pass
        if not geo_data_collected:
            try:
                nrel_collector = nrel.solar_data_collector(user_address)
                nrel_collector.lat_long()
                solar_data_values = nrel_collector.solar_data()
                wind_speed = solar_data_values['Wind Speed']
                dhi = round(solar_data_values['DHI'],2)
                dni = round(solar_data_values['DNI'],2)
                temp = round(solar_data_values['Temperature'],2)
                lat = round(nrel_collector.latitude, 2)
                lon = round(nrel_collector.longitude, 2)
                geo_data_collected = True
            except:
                form_message = "Bad Address, Please Enter Another"
        # trying to get solar model prediction.
        # Only want to do this if we even have geo data.
        if geo_data_collected:
            try:
                # Defining columns for the model.
                columns = [u'Intercept', u'tech_1[T.CIS]', u'tech_1[T.CdTe]', u'tech_1[T.Mono]',
                       u'tech_1[T.Mono + a-Si]', u'tech_1[T.Poly]', u'tech_1[T.Thin Film]',
                       u'tech_1[T.a-Si]', u'tech_1[T.a-Si + Micro-c]',
                       u'tech_1[T.crystalline]', u'tech_1[T.multiple]', u'tech_1[T.no_tech]',
                       u'tracking_type[T.Fixed]', u'tracking_type[T.Single-Axis]',
                       u'tracking_type[T.no_tracking]', u'size_kw', u'azimuth1', u'tilt1',
                       u'DHI', u'DNI', u'Wind_Speed']

                # Creating a blank dataframe that will end up holding user values.
                user_df = pd.DataFrame(data=[np.zeros(len(columns))], columns=columns)

                # Setting values in dataframe based on user received values.
                user_df.loc[0, 'Intercept'] = 1
                user_df.loc[0, 'size_kw'] = size_kw
                user_df.loc[0, 'azimuth1'] = azimuth
                user_df.loc[0, 'tilt1'] = user_tilt
                user_df.loc[0, 'Wind_Speed'] = wind_speed
                user_df.loc[0, 'DHI'] = dhi
                user_df.loc[0, 'DNI'] = dni
                for c in user_df.columns:
                    if tracking_type in c:
                        user_df.loc[0, c] = 1
                    if tech_1 in c:
                        user_df.loc[0, c] = 1

                # scalling the data
                print "Scaling Data"
                user_df_scaled = scaler.transform(user_df)[0]
                # Getting model prediction:
                print "Getting Prediction"
                prediction = en_model.predict(user_df_scaled)[0]

                print "Calculating electr_rate"
                # calculating annual savings from prediction
                electr_rate = rates.loc[rates['state_abbrev'] == state, 'average_retail_price'].values[0] * .01
                print "Calculating Savings"
                annual_savings = electr_rate * prediction

                # Calculating years to break even.
                break_even = cost/annual_savings

                solar_message = "Your Solar Predictions"
                predictions_made = True
            except:
                form_message = "Prediction Failed"

        # format data if we have the predictions.
        if predictions_made:
            cost = round(cost, 2)
            cost = "${:,.2f}".format(cost)

            prediction = str(round(prediction, 2)) + " kWh per year"

            annual_savings = round(annual_savings, 2)
            annual_savings = "${:,.2f}".format(annual_savings)

            break_even = str(round(break_even, 1)) + " years"



    # This is if form method != post, so if person has not submitted anything yet.
    else:
        form_message = "Enter Your Location and Solar Installation Information"

    template_data = {
        "formdata": {
            "lon": lon,
            "lat": lat,
            "temperature": temp,
            "DNI": dni,
            "Cost": cost,
            "azimuth": azimuth,
            "prediction": prediction,
            "annual_savings": annual_savings,
            "break_even": break_even,
                },
        "form_message": form_message,
        "solar_message": solar_message,
            }

    if request.POST.get("format", "HTML") == "HTML":
        return render(request, 'solar_output_prediction/prediction_page.html', template_data)

    else:
        return JsonResponse(template_data, safe=False)
