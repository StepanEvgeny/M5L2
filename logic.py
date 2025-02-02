import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime
import pytz
import requests


class DB_Map():
    def __init__(self, database):
        self.database = database
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self,user_id, city_name ):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

            
    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities


    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates
    
    def get_cities_by_country(self, country_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT city FROM cities WHERE country = ?", (country_name,))
            return [row[0] for row in cursor.fetchall()]
    
    def get_cities_by_population_density(self, min_density, max_density):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT city FROM cities WHERE density BETWEEN ? AND ?", (min_density, max_density))
            return [row[0] for row in cursor.fetchall()]

    def get_cities_by_country_and_density(self, country_name, min_density, max_density):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT city FROM cities WHERE country = ? AND density BETWEEN ? AND ?", (country_name, min_density, max_density))
            return [row[0] for row in cursor.fetchall()]
    
    def get_weather(self, city_name):
        api_key = "YOUR_WEATHER_API_KEY"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        response = requests.get(url).json()
        if response.get("main"):
            temp = response["main"]["temp"]
            weather_desc = response["weather"][0]["description"]
            return f"{temp}°C, {weather_desc}"
        return "Нет данных"
    
    def get_time(self, city_name):
        timezone_mapping = {
            "New York": "America/New_York",
            "London": "Europe/London",
            "Tokyo": "Asia/Tokyo",
            "Moscow": "Europe/Moscow"
        }
        tz = pytz.timezone(timezone_mapping.get(city_name, "UTC"))
        return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

    def create_grapf(self, path, cities, color='red'):
       ax = plt.axes(projection=ccrs.PlateCarree())
       ax.stock_img()
       for city in cities:
           coordinates = self.get_coordinates(city)
           lat, lng = coordinates
           plt.plot([lng], [lat], color='r', linewidth=1, marker='.', transform=ccrs.Geodetic())
           plt.text(lng + 3, lat + 12, city, horizontalalignment='left', transform=ccrs.Geodetic())
       plt.savefig(path)
       plt.close()
        
    def draw_distance(self, city1, city2,color ='red'):
        city1_coords = self.get_coordinates(city1)
        city2_coords = self.get_coordinates(city2)
        fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.LAND, color='lightgray')
        ax.add_feature(cfeature.OCEAN, color='lightblue')
        ax.add_feature(cfeature.BORDERS, linestyle='--', edgecolor='black')
        ax.add_feature(cfeature.RIVERS, edgecolor='blue')
        ax.stock_img()
        plt.plot([city1_coords[1], city2_coords[1]], [city1_coords[0], city2_coords[0]], color='red', linewidth=2, marker='o', transform=ccrs.Geodetic())
        plt.text(city1_coords[1] + 3, city1_coords[0] + 12, city1, horizontalalignment='left', transform=ccrs.Geodetic())
        plt.text(city2_coords[1] + 3, city2_coords[0] + 12, city2, horizontalalignment='left', transform=ccrs.Geodetic())
        plt.savefig('distance_map.png')
        plt.close()


if __name__=="__main__":
    
    m = DB_Map(DATABASE)
    m.create_user_table()
