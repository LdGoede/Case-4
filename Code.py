import pandas as pd
import requests
import matplotlib.pyplot as plt
import streamlit as st
import json
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd

#API call 1 GeodataGemeente
def load_geo_data():
    url = "https://www.webuildinternet.com/articles/2015-07-19-geojson-data-of-the-netherlands/townships.geojson"

    # Het bestand downloaden
    response = requests.get(url)

    # Controleren of de download succesvol was
    if response.status_code == 200:
        data = response.json()
        return gpd.GeoDataFrame.from_features(data)
    else:
        st.write("Kon het bestand niet downloaden.")
        return None

# Functie aanroepen om de gegevens te laden
geo_data = load_geo_data()
# Selecteer specifieke kolommen, bijvoorbeeld 'column1', 'column2' en 'column3'
selected_columns_geo = geo_data[['code', 'name', 'geometry']]
# Toevoegen van 'GM' aan de 'code'-kolom in de DataFrame
selected_columns_geo.loc[:, 'code'] = 'GM' + selected_columns_geo['code'].astype(str)


#API call 2 GeoDataProvincie
def api_call_prov():
    url2 = "https://www.webuildinternet.com/articles/2015-07-19-geojson-data-of-the-netherlands/provinces.geojson"
    
    # Het bestand downloaden
    response = requests.get(url2)

    # Controleren of de download succesvol was
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        st.write("Kon het bestand niet downloaden.")
        return None

def get_geo_data():
    geo_dataProv = api_call_prov()
    return gpd.GeoDataFrame.from_features(geo_dataProv['features'])

geo_data_prov = get_geo_data()
geo_data_prov['name'] = geo_data_prov['name'].replace('Friesland (Fryslân)', 'Friesland')
# Selecteer specifieke kolommen, bijvoorbeeld 'column1', 'column2' en 'column3'
selected_columns_geo_prov = geo_data_prov[['name', 'geometry']]


#CSV inladen:
#Gemiddelde verkoop
gemiddelde_verkoop = pd.read_csv('GemVerkoop.csv',sep = ';')
#Gemiddelde verkoop
gemiddelde_verkoop_prov = pd.read_csv('GemVerkoopProv.csv',sep = ';')
#Index
index = pd.read_csv('bestaande_koopwoningen.csv', sep=';', quotechar='"')

#Filtering CSV Prov
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

#filtering and cleaning index csv
kolommen_te_verwijderen = ["ID", "OntwikkelingTOVEenJaarEerder_3", "OntwikkelingTOVVoorgaandePeriode_2", "OntwikkelingTOVVoorgaandePeriode_5", "OntwikkelingTOVEenJaarEerder_6", "TotaleWaardeVerkoopprijzen_8"]
index = index.drop(columns=kolommen_te_verwijderen)
index = index.dropna()


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
# Creëer een geopandas GeoDataFrame met gegevens van alleen 2015
gdf = gpd.GeoDataFrame(data_2015, geometry='geometry')

# Functie voor het plotten van de kaart
def plot_map(year):
    fig, ax = plt.subplots(1, 1, figsize=(30, 10))

    data_to_plot = gdf

    # Plot de kaart gebaseerd op 'GemiddeldeVerkoopprijs_1'
    data_to_plot.plot(column='GemiddeldeVerkoopprijs_1', ax=ax, cmap='viridis', legend=True)

    # Stel de titel van de plot in
    ax.set_title('Gemiddelde Verkoopprijs in 2015 in Euro')

    return fig
map_fig = plot_map(2015)

#lijnchart 
# Maak een interactieve lijnplot met Plotly Express
fig1 = px.line(index, x="Perioden", y="PrijsindexBestaandeKoopwoningen_1",
              labels={"PrijsindexBestaandeKoopwoningen_1": "Prijsindex Bestaande Koopwoningen_1"},
              hover_data=["PrijsindexBestaandeKoopwoningen_1"])

# Voeg een horizontale lijn toe bij de waarde 100
fig1.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Waarde 100", annotation_position="top left")

# Voeg een rechthoekig gebied toe van '2007MM10' tot '2011JJ00'
fig1.add_vrect(x0='2007MM10', x1='2011JJ00', fillcolor="rgba(0, 0, 255, 0.2)", line_width=0)

# Voeg de tekst 'Kredietcrisis' toe aan het gemarkeerde gebied
fig1.add_trace(
    go.Scatter(
        x=['2009MM10'],
        y=[190],
        text=['Kredietcrisis'],
        mode='text',
        showlegend=False
    )
)

# Zoek de index van de waarde 128.8 in de dataset
index_128_8 = index[index['PrijsindexBestaandeKoopwoningen_1'] == 128.8].index[0]

# Voeg een verticale lijn toe op de x-as bij de index waar de waarde 128.8 wordt bereikt
fig1.add_vline(x=index_128_8, line_dash="dot", line_color="green", annotation_text="Stikstofcrisis", annotation_position="bottom right")

# Pas de labels aan
fig1.update_xaxes(title_text="Perioden")
fig1.update_yaxes(title_text="Prijsindex van Bestaande Koopwoningen")

# Streamlit section
st.title("De woningcrisis o.b.v. data")
st.caption("Door Emma Wartena & Luuk de Goede")
st.image('https://hips.hearstapps.com/hmg-prod/images/model-home-resting-on-top-of-us-paper-currency-royalty-free-image-1631301093.jpg?crop=1.00xw:0.376xh;0,0.126xh&resize=1200:*', caption='Credit: Elle.com')


st.plotly_chart(fig1, use_container_width=True)
st.pyplot(map_fig)
