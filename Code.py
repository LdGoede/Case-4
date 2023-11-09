from ipywidgets import interact
import pandas as pd
import requests
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

#API call 1 GeodataGemeente
@st.cache_data(ttl=1200)
def api_call_gem():
    url = "https://www.webuildinternet.com/articles/2015-07-19-geojson-data-of-the-netherlands/townships.geojson"
    Geodata = "townships.geojson"

    # Het bestand downloaden
    response = requests.get(url)

    # Controleren of de download succesvol was
    if response.status_code == 200:
    # Het bestand opslaan
        with open(Geodata, 'wb') as f:
        print(f"Download van {Geodata} voltooid.")
    else:
        print("Kon het bestand niet downloaden.")

# Open het GeoJSON-bestand met geopandas
geo_data = gpd.read_file(api_call_gem())
# Selecteer specifieke kolommen, bijvoorbeeld 'column1', 'column2' en 'column3'
selected_columns_geo = geo_data[['code', 'name', 'geometry']]
# Toevoegen van 'GM' aan de 'code'-kolom in de DataFrame
selected_columns_geo.loc[:, 'code'] = 'GM' + selected_columns_geo['code'].astype(str)


#API call 2 GeoDataProvincie
@st.cache_data(ttl=1200)
def api_call_prov():
    url2 = "https://www.webuildinternet.com/articles/2015-07-19-geojson-data-of-the-netherlands/provinces.geojson"
    GeodataProv = "provinces.geojson"
    # Het bestand downloaden
    response2 = requests.get(url2)

    # Controleren of de download succesvol was
    if response2.status_code == 200:
        # Het bestand opslaan
        with open(GeodataProv, 'wb') as f:
        print(f"Download van {GeodataProv} voltooid.")
    else:
        print("Kon het bestand niet downloaden.")
# Open het GeoJSON-bestand met geopandas
geo_data_prov = gpd.read_file(api_call_prov())
geo_data_prov['name'] = geo_data_prov['name'].replace('Friesland (Fryslân)', 'Friesland')
# Selecteer specifieke kolommen, bijvoorbeeld 'column1', 'column2' en 'column3'
selected_columns_geo_prov = geo_data_prov[['name', 'geometry']]


#CSV inladen:
#Gemiddelde verkoop
gemiddelde_verkoop = pd.read_csv('GemVerkoop.csv',sep = ';')
#Gemiddelde verkoop
gemiddelde_verkoop_prov = pd.read_csv('GemVerkoopProv.csv',sep = ';')


#Filtering CSV
# Dictionary met de corresponderende provinciecodes en namen
provinciecodes = {
    'PV20  ': 'Groningen',
    'PV21  ': 'Friesland',
    'PV22  ': 'Drenthe',
    'PV23  ': 'Overijssel',
    'PV24  ': 'Flevoland',
    'PV25  ': 'Gelderland',
    'PV26  ': 'Utrecht',
    'PV27  ': 'Noord-Holland',
    'PV28  ': 'Zuid-Holland',
    'PV29  ': 'Zeeland',
    'PV30  ': 'Noord-Brabant',
    'PV31  ': 'Limburg'
}

# Vervang de codes door de provincienamen in de kolom 'RegioS'
gemiddelde_verkoop_prov['RegioS'] = gemiddelde_verkoop_prov['RegioS'].replace(provinciecodes)
# Verwijder de laatste vier tekens van de 'Perioden' kolom
gemiddelde_verkoop_prov['Perioden'] = gemiddelde_verkoop_prov['Perioden'].str.slice(stop=-4)


#merging data
#merge1 Gemeente
# Voer de merge uit op basis van de overeenkomende kolommen 'RegioS' en 'code'
merged_data = selected_columns_geo.merge(gemiddelde_verkoop, left_on='code', right_on='RegioS')
# Verwijder de 'RegioS' kolom
merged_data.drop('RegioS', axis=1, inplace=True)
# Verwijder de laatste vier tekens van de 'Perioden' kolom
merged_data['Perioden'] = merged_data['Perioden'].str.slice(stop=-4)
#filter 2015
data_2015 = merged_data[merged_data['Perioden'] == '2015']
# Gebruik .loc om waarden toe te wijzen cleaning
data_2015.loc[data_2015['GemiddeldeVerkoopprijs_1'].isnull(), 'GemiddeldeVerkoopprijs_1'] = 248976.0

#merge2 provincie
# Voer de merge uit op basis van de overeenkomende kolommen 'RegioS' en 'name'
merged_data_prov = selected_columns_geo_prov.merge(gemiddelde_verkoop_prov, left_on='name', right_on='RegioS')


#kaart 1: 
# Creëer een geopandas GeoDataFrame
gdf = gpd.GeoDataFrame(data_2015, geometry='geometry')

# Plot initialiseren
fig1, ax = plt.subplots(1, 1, figsize=(15, 10))

# Functie voor het plotten van de kaart
def plot_map(year):
    data_to_plot = gdf[gdf['Perioden'] == year]

    # Plot de kaart gebaseerd op 'GemiddeldeVerkoopprijs_1'
    data_to_plot.plot(column='GemiddeldeVerkoopprijs_1', ax=ax, cmap='viridis', legend=True)

    # Stel de titel van de plot in met het geselecteerde jaar
    ax.set_title(f'Gemiddelde Verkoopprijs in {year}')

    # Toon de plot
    plt.show()

# Gebruik de plot_map functie om de kaart voor een specifiek jaar te genereren
plot_map('2015')


#kaart 2: 
# Laden van de data in een GeoDataFrame
gdfProv = gpd.GeoDataFrame(merged_data_prov, geometry=merged_data_prov['geometry'])

# Bepaal de minimale en maximale waarden voor de kleurschaal
min_val = gdfProv['GemiddeldeVerkoopprijs_1'].min()
max_val = gdfProv['GemiddeldeVerkoopprijs_1'].max()

# Functie om de kaart te plotten op basis van het jaar
def plot_map2(year):
    data_to_plot = gdfProv[gdfProv['Perioden'] == year]

    # Creëer de plot met 'plasma' colormap
    fig, ax = plt.subplots(figsize=(10, 10))
    data_to_plot.plot(column='GemiddeldeVerkoopprijs_1', ax=ax, legend=True, cmap='plasma', legend_kwds={'label': "Gemiddelde verkoopprijs"}, vmin=min_val, vmax=max_val)
    plt.title(f"Kaart van Nederland in {year}")

# Interactieve slider voor het jaar
interact(plot_map2, year=gdfProv['Perioden'].unique())


st.map(plot_map2)
