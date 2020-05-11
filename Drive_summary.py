from csv import reader
import pandas as pd
from pygeodesy.sphericalNvector import LatLon
import datetime as dt
import pandas as pd
import time as T
import overpy
import sys
import simplejson as json
import requests
from Scripts.AwsRead import AwsRead
#### blalblvllalla

def load_csv(filename):
    '''
    loads CSV.
    Input: file path - string
    Output: data set
    '''
    dataset = list()
    with open(filename, 'r') as file:
        csv_reader = reader(file)
        for row in csv_reader:
            if not row:
                continue
            dataset.append(row)
    return dataset

def speedScore(dataset):
    speed_limit = 30
    strong_break_treshold = 20
    strong_acceleration_treshold = 25
    high_speed_counter = 0
    strong_break_counter = 0
    strong_acceleration_counter = 0
    high_speed_penalty = 1
    strong_break_penalty = 1
    strong_acceleration_penalty = 1
    row_index = 0
    for row in dataset:
        if(row_index>0):
            if (float(row[10]) > speed_limit):
                high_speed_counter += 1
            if (row_index > 1):
                if ((float(dataset[row_index-1][10])) - (float(row[10]))  > strong_break_treshold):
                    strong_break_counter += 1
                if (float(row[10]) > float(dataset[row_index-1][10]) + strong_acceleration_treshold):
                    strong_acceleration_counter += 1
        row_index +=1
    print("high_speed_counter: " + str(high_speed_counter) )
    print("strong_break_counter: " + str(strong_break_counter) )
    print("strong_acceleration_counter: " + str(strong_acceleration_counter) )
    print("REDRIVE drive grade: " + str(((high_speed_counter / len(dataset)) * high_speed_penalty) + ((strong_break_counter / len(dataset)) * strong_break_penalty) + (strong_acceleration_counter / len(dataset)) * strong_acceleration_penalty))

def fuelEficiencyScore(dataset):
    row_index = 0
    maximum_speed = 220
    maximum_engineSpeed = 8000
    bad_fuel_counter = len(dataset)

    #### creating Dt = (Data (t+1)  - Data (t))
    max_changeRate_throttle = 0
    max_changeRate_engineSpeed = 0

    for i in range(len(dataset)):
        if (i>0):
            if (float(dataset[i][9])>max_changeRate_throttle):
                max_changeRate_throttle = float(dataset[i][9])
            if (float(dataset[i][2]) > max_changeRate_engineSpeed):
                max_changeRate_engineSpeed = float(dataset[i][2])

    for row in dataset:
        if(row_index < len(dataset)-1 ):
            if (row_index > 0):
                if ((float(row[9])/maximum_engineSpeed) > 0):
                    relative_ratio_of_vehicle_speed_and_engine_speed = ((float(row[10])/maximum_speed) / (float(row[9])/maximum_engineSpeed))
                    row[0] = relative_ratio_of_vehicle_speed_and_engine_speed

                row[10] = float(dataset[row_index + 1][10] ) - float(dataset[row_index][10] )  ## speed
                row[9] = float(dataset[row_index + 1][9]) - float(dataset[row_index][9] )## Throttle
                row[2] = float(dataset[row_index + 1][2]) - float(dataset[row_index][2] )## RPM (engine speed)
                row[1] = float(dataset[row_index + 1][1]) - float(dataset[row_index][1]) ## engine load

                ##create R(zj) = relative ratio of throttle postion and engine speed
                if ((float(row[2]) / max_changeRate_engineSpeed) > 0):
                    row[3] = (float(row[9]) / max_changeRate_throttle)  / (float(row[2]) / max_changeRate_engineSpeed)

                ## create fuel efficiency score:
                if (float(row[0]) > 0.9 and float(row[0]) < 1.3): # R(cz)
                    if (float(row[3]) > 0.9 and float(row[3]) < 1.3): # R(zj)
                        if (float(row[1]) > 0.2 and float(row[1]) < 0.5): # engine load
                            bad_fuel_counter = bad_fuel_counter -1
        row_index += 1
    print ("bad fuel counter percentage: ", bad_fuel_counter/len(dataset))

def calculate_route_in_KM_GPS (gps_dataset):
    row_index = 0
    accumulated_d = 0
    published_weather = False
    try_again_soon = False
    for row in gps_dataset:
        if (row_index > 1):
            t_Longitude = float(row[2])
            t_Latitude = float(row[3])
            if (published_weather == False):
                #is_rain(t_Latitude,t_Longitude)
                is_rain(31.2680245, 34.7971712)
                published_weather = True
            t_minus_1_Longitude = float(gps_dataset[row_index-1][2])
            t_minus_1_Latitude = float(gps_dataset[row_index-1][3])
            x = LatLon(t_Latitude,t_Longitude)
            y = LatLon(t_minus_1_Latitude,t_minus_1_Longitude)
            d = x.distanceTo(y) # 9.64 km
            if(try_again_soon == False):
                if (row_index % 51 == 0 ):
                    try:
                        #max_speed = maxspeed(t_Latitude, t_Longitude, 100)
                        max_speed = maxspeed(31.561134, 34.803414, 100)
                    except:
                        print("An exception occurred")
                        try_again_soon = True
                    if(len(max_speed) > 0 and try_again_soon == False):
                        print("road name: ", max_speed[0]['name'])
                        print("max speed allowed: ",max_speed[0]['speed_limit'])
                    else:
                        try_again_soon = True
            else:
                try_again_soon = False
                if (row_index % 5 == 0 ):
                    try:
                        max_speed = maxspeed(t_Latitude, t_Longitude, 100)
                    except:
                        print("An exception occurred")
                        try_again_soon = True
                    if(len(max_speed) > 0 and try_again_soon == False):
                        print("max speed allowed: ",max_speed[0]['speed_limit'])
                        try_again_soon = False
                    else:
                        try_again_soon = True
            #print (d)
            accumulated_d = accumulated_d + d ## total distance in meters
        row_index = row_index + 1
    print("total meters driven: ", str(accumulated_d))

def calculate_route_in_KM_Speed (gps_dataset):
    row_index = 0
    accumulated_d = 0
    date_format = "%H:%M:%S"
    for row in gps_dataset:
        if (row_index > 1):
            time = row[1]
            meter_per_sec = float(gps_dataset[row_index-1][4])
            time_minus_1 = gps_dataset[row_index-1][1]
            diff = T.strptime(str(time), date_format).tm_sec - T.strptime(str(time_minus_1), date_format).tm_sec + (T.strptime(str(time), date_format).tm_min - T.strptime(str(time_minus_1), date_format).tm_min)*60
            d = meter_per_sec * diff# calculate distance
            #d = meter_per_sec * pd.to_timedelta(time_minus_1,time,unit='S')
            #print (row_index)
            accumulated_d = accumulated_d + d ## total distance in meters
        row_index = row_index + 1
    print("total meters driven: ", str(accumulated_d))

#pip install overpy
#python overpass_speed.py 37.7833 -122.4167 500

def maxspeed(lat,lon, radius):
    lat, lon = lat,lon
    api = overpy.Overpass()

# fetch all ways and nodes
    result = api.query("""
            way(around:""" + str(radius) + """,""" + str(lat)  + """,""" + str(lon)  + """) ["maxspeed"];
                (._;>;);
                    out body;
                        """)
    results_list = []
    for way in result.ways:
        road = {}
        road["name"] = way.tags.get("name", "n/a")
        road["speed_limit"] = way.tags.get("maxspeed", "n/a")
        nodes = []
        for node in way.nodes:
            nodes.append((node.lat, node.lon))
        road["nodes"] = nodes
        results_list.append(road)
    return results_list

def is_rain (lat, lon):
    lat, lon = lat, lon
    # Enter your API key here
    api_key = "e2da3d92f35bc0631b4301bf7572f3dd"
    # base_url variable to store url
    #base_url = "http://api.openweathermap.org/data/2.5/weather?"
    try:
        base_url = "https://api.openweathermap.org/data/2.5/onecall?lat="
        # Give city name
        #city_name = input("Enter city name : ")
        # complete_url variable to store
        # complete url address
        complete_url = base_url +  str(lat) +"&lon=" +str(lon) +"&appid=" + api_key
        # get method of requests module
        # return response object
        response = requests.get(complete_url)
        # json method of response object
        # convert json format data into
        # python format data
        x = response.json()
        # Now x contains list of nested dictionaries
        # Check the value of "cod" key is equal to
        # "404", means city is found otherwise,
        # city is not found
        if response.status_code == 200:
        #if x["cod"] != "404" and x["cod"] != "401":
            # store the value of "main"
            # key in variable y
            main_description = x['current']['weather'][0]['main']
            citry = x['current']['weather'][0]['main']
            print("Zone: "+ x['timezone'])
            print("weather description = " +str(main_description))
        else:
            print(" 404 error")
    except:
        print("there was an error with request")

##--------------------- MAIN --------------------------------------
try:
    user1 = AwsRead('User1')
    user1_tables = user1.getUserTables()
    print(user1_tables)
except:
    print("couldnt connect")


filepath = 'C:\\Users\\omria\\Desktop\\obd.csv'
dataset = load_csv(filepath)

###### calculate scores
speedScore(dataset)
fuelEficiencyScore(dataset)

filepath = 'C:\\Users\\omria\\Desktop\\gps.csv'
gps_dataset = load_csv(filepath)
calculate_route_in_KM_GPS(gps_dataset)
calculate_route_in_KM_Speed(gps_dataset)
##-----------------------------------------------------------------



#0.425143707 * KPL = MPG
#1 Mile per gallon = 0.425143707 kilometers per liter







