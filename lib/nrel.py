import pandas as pd
import numpy as np
# import geopy
# from geopy.geocoders import Nominatim
import googlemaps

class solar_data_collector():

    api_key = '0uonQPAH2V5XyTNIpmLWeAf3jgCatQJXEZgzqlSm'
    attributes = 'ghi,dhi,dni,wind_speed_10m_nwp,surface_air_temperature_nwp,solar_zenith_angle'
    year = '2015'
    leap_year = 'false'
    interval = '60'
    utc = 'false'
    your_name = 'evan+baker'
    reason_for_use = 'beta+testing'
    your_affiliation = 'General+Assembly'
    your_email = 'evancasebaker@gmail.com'
    mailing_list='true'
    gmaps = googlemaps.Client(key='AIzaSyDmBuKB3BMvjYOJbY6rqx_v99ZweE63g-s')

    def __init__(self, address):
        self.address = address
        pass

    def lat_long(self):
        geocode_result = self.gmaps.geocode(self.address)
        self.latitude = geocode_result[0]['geometry']['location']['lat']
        self.longitude = geocode_result[0]['geometry']['location']['lng']
        # geolocator = Nominatim()
        # location = geolocator.geocode(self.address)
        # self.location = location
        # self.latitude = location.latitude
        # self.longitude = location.longitude
        pass

    def solar_data(self):
        solar_data_values = {
            "DHI": [],
            "DNI": [],
            "GHI": [],
            "Solar Zenith Angle": [],
            "Temperature": [],
            "Wind Speed": []}

        url = 'http://developer.nrel.gov/api/solar/nsrdb_0512_download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=self.year,
        lat=self.latitude, lon=self.longitude, leap=self.leap_year, interval=self.interval, utc=self.utc, name=self.your_name, email=self.your_email, mailing_list=self.mailing_list, affiliation=self.your_affiliation, reason=self.reason_for_use, api=self.api_key, attr=self.attributes)

        df = pd.read_csv(url, skiprows=2)

        pivot = df.pivot_table(["GHI","DHI","DNI","Wind Speed","Temperature","Solar Zenith Angle"], index="Year")
        for c in pivot.columns:
            solar_data_values[c] = pivot[c].values[0]
        self.data = solar_data_values
        self.DHI = solar_data_values['DHI']
        self.DNI = solar_data_values['DNI']
        self.GHI = solar_data_values['GHI']
        self.zenith = solar_data_values['Solar Zenith Angle']
        self.temperature = solar_data_values['Temperature']
        self.wind_speed = solar_data_values['Wind Speed']
        return solar_data_values
