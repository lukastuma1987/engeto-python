import sqlalchemy
import pandas as pd
import numpy as np

conn_string = f"mysql+pymysql://student:p7@vw7MCatmnKjy7@data.engeto.com/data"
alchemy_conn = sqlalchemy.create_engine(conn_string)

df = pd.read_sql('edinburgh_bikes', alchemy_conn, parse_dates=True)

print("Celkovy pocet vypujcek od '" + str(df['started_at'].min()).split()[0] + "' do '" + str(df['ended_at'].max()).split()[0] + "': " + str(len(df.index)))
print("Prumerna delka trvani vypujcky: " + str(int(np.round(df['duration'].mean() / 60))) + " min a " + str(int(((df['duration'].mean() / 60) % 1) * 60)) + " sec")

start_stations_ids_arr = np.unique(df['start_station_id'].to_numpy())
end_stations_ids_arr = np.unique(df['end_station_id'].to_numpy())
stations_ids_arr = np.unique(np.concatenate((start_stations_ids_arr, end_stations_ids_arr)))
print("Celkovy pocet stanic: " + str(stations_ids_arr.shape[0]))

only_start_stations_mask = ~np.isin(start_stations_ids_arr, end_stations_ids_arr)
only_end_stations_mask = ~np.isin(end_stations_ids_arr, start_stations_ids_arr)
print("Stanice, kde vypujcky pouze zacinaji: " + str(start_stations_ids_arr[only_start_stations_mask]))
print("Stanice, kde vypujcky pouze konci: " + str(end_stations_ids_arr[only_end_stations_mask]))

df_stations_freq = pd.DataFrame(stations_ids_arr, columns=['station_id'])
df_stations_freq['start_station_count'] = df_stations_freq.apply(lambda x: np.where(df['start_station_id'] == x['station_id'], True, False).sum(), axis=1)
df_stations_freq['end_station_count'] = df_stations_freq.apply(lambda x: np.where(df['end_station_id'] == x['station_id'], True, False).sum(), axis=1)
print("Stanice s nejcastejsim zacatkem vypujcky:")
print(df_stations_freq.sort_values('start_station_count', ascending=False).head(10).to_string(index=False))
print("Stanice s nejcastejsim koncem vypujcky:")
print(df_stations_freq.sort_values('end_station_count', ascending=False).head(10).to_string(index=False))


