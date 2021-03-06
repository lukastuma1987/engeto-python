import sqlalchemy
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

conn_string = f"mysql+pymysql://student:p7@vw7MCatmnKjy7@data.engeto.com/data"
alchemy_conn = sqlalchemy.create_engine(conn_string)

df = pd.read_sql('edinburgh_bikes', alchemy_conn, parse_dates=True)
df_weather = pd.read_sql('edinburgh_weather', alchemy_conn, parse_dates=True)
df['weekday'] = ((pd.to_datetime(df['started_at']).dt.dayofweek == 5) | (pd.to_datetime(df['started_at']).dt.dayofweek == 6)).astype(int)
df['duration_hours'] = df['duration'] // 3600

print("Celkovy pocet vypujcek od '" + str(df['started_at'].min()).split()[0] + "' do '" + str(df['ended_at'].max()).split()[0] + "': " + str(len(df.index)))
print("Prumerna delka trvani vypujcky: " + str(int(np.round(df['duration'].mean() / 60))) + " min a " + str(int(((df['duration'].mean() / 60) % 1) * 60)) + " sec")

start_stations_ids_arr = np.unique(df['start_station_id'].to_numpy())
end_stations_ids_arr = np.unique(df['end_station_id'].to_numpy())
stations_ids_arr = np.unique(np.concatenate((start_stations_ids_arr, end_stations_ids_arr)))
print("Celkovy pocet stanic: " + str(stations_ids_arr.shape[0]))

only_start_stations_mask = ~np.isin(start_stations_ids_arr, end_stations_ids_arr)
only_end_stations_mask = ~np.isin(end_stations_ids_arr, start_stations_ids_arr)
print("Stanice, kde vypujcky pouze zacinaji: " + str(start_stations_ids_arr[only_start_stations_mask]))
print("Stanice, kde vypujcky pouze konci: " + str(end_stations_ids_arr[only_end_stations_mask]) + "\n")

df_stations_freq = pd.DataFrame(stations_ids_arr, columns=['station_id'])
df_stations_freq['start_station_count'] = df_stations_freq.apply(lambda x: np.where(df['start_station_id'] == x['station_id'], True, False).sum(), axis=1)
df_stations_freq['end_station_count'] = df_stations_freq.apply(lambda x: np.where(df['end_station_id'] == x['station_id'], True, False).sum(), axis=1)
print("Stanice s nejcastejsim zacatkem vypujcky:")
print(df_stations_freq.sort_values('start_station_count', ascending=False).head(10).to_string(index=False) + "\n")
print("Stanice s nejcastejsim koncem vypujcky:")
print(df_stations_freq.sort_values('end_station_count', ascending=False).head(10).to_string(index=False) + "\n")


def station_coords(station_id):
    station_lat = df.loc[df['start_station_id'] == station_id, 'start_station_latitude']
    station_lon = df.loc[df['start_station_id'] == station_id, 'start_station_longitude']
    if len(station_lat) == 0:
        station_lat = df.loc[df['end_station_id'] == station_id, 'end_station_latitude'].iloc[0]
        station_lon = df.loc[df['end_station_id'] == station_id, 'end_station_longitude'].iloc[0]
    else:
        station_lat = station_lat.iloc[0]
        station_lon = station_lon.iloc[0]
    return (station_lat, station_lon)


stations_distances = np.empty(shape=(stations_ids_arr.shape[0],stations_ids_arr.shape[0]))
for index1 in range(len(stations_ids_arr)):
    station1_id = stations_ids_arr[index1]
    coords_1 = station_coords(station1_id)
    for index2 in range(len(stations_ids_arr)):
        station2_id = stations_ids_arr[index2]
        coords_2 = station_coords(station2_id)
        stations_distances[index1, index2] = geodesic(coords_1, coords_2).km

print("Nasledujici matice rozmeru " + str(stations_distances.shape) + " obsahuje vzdalenosti v km mezi jednotlivymi stanicemi:")
print(stations_distances + "\n")


pocet_vypujcek_df = df['started_at'].groupby([pd.to_datetime(df['started_at']).dt.isocalendar().year, pd.to_datetime(df['started_at']).dt.isocalendar().week]).count()
delka_vypujcek_df = df[['started_at', 'duration']].groupby([pd.to_datetime(df['started_at']).dt.isocalendar().year, pd.to_datetime(df['started_at']).dt.isocalendar().week])['duration'].mean()/60
df_weather['datetime'] = df_weather['date'] + ' ' + df_weather['time']
df_weather['temp'] = pd.to_numeric(df_weather['temp'].str.split(" ").str[0])
df_weather_temp = df_weather[['datetime', 'temp']].groupby([pd.to_datetime(df_weather['datetime']).dt.isocalendar().year, pd.to_datetime(df_weather['datetime']).dt.isocalendar().week])['temp'].mean()

fig = plt.figure(figsize=(15,8))
gs = gridspec.GridSpec(2, 3)

ax1 = plt.subplot(gs[0,0])
df.hist(ax=ax1, column='duration_hours', grid=True, log=True)
ax1.title.set_text('Histogram trv??n?? v??p??j??ek kol')
ax1.set_ylabel('po??et v??p??j??ek')
ax1.set_xlabel('trv??n?? v??p??j??ky [hod]')

ax2 = plt.subplot(gs[0,1])
pocet_vypujcek_df.plot(ax=ax2, title='V??voj po??tu v??p??j??ek kol v ??ase', grid=True)
ax2.set_ylabel('po??et v??p??j??ek')
ax2.set_xlabel('rok a t??den')

ax3 = plt.subplot(gs[0,2])
delka_vypujcek_df.plot(ax=ax3, title='V??voj pr??m??rn?? d??lky v??p??j??ek kol v ??ase', grid=True)
ax3.set_ylabel('pr??m??rn?? d??lka v??p??j??ky [min]')
ax3.set_xlabel('rok a t??den')

ax4 = plt.subplot(gs[1,0])
pd.DataFrame({'pocet': [len(df[df['weekday'] == 1]), len(df[df['weekday'] == 0])]}, index=['v??kend', 'pracovn?? dny']).plot.pie(ax=ax4, y='pocet', autopct='%1.1f%%', title='V??p??j??ky o v??kendu/pracovn?? dny')
ax4.legend(loc="lower right")

ax5 = plt.subplot(gs[1,1])
df_weather_temp.plot(ax=ax5, title='V??voj pr??m??rn?? teploty v ??ase', grid=True)
ax5.set_ylabel('pr??m??rn?? teplota [??C]')
ax5.set_xlabel('rok a t??den')

plt.tight_layout()
plt.show()