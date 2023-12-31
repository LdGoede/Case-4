import pandas as pd
import requests
import matplotlib.pyplot as plt
import streamlit as st
import json
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from sklearn.linear_model import LinearRegression
import numpy as np

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
inflation = pd.read_csv('cpi.csv', sep=';', quotechar='"')

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
# Add a 'Year' column based on 'Perioden'
index['Year'] = index['Perioden'].str.extract('(\d{4})').astype(float)
index = index.dropna()

#filtering and cleaning inflation csv
# Add a 'Year' column based on 'Perioden' for the inflation DataFrame
inflation['Year'] = inflation['Perioden'].str.extract('(\d{4})').astype(float)


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
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))

    data_to_plot = gdf

    # Plot de kaart gebaseerd op 'GemiddeldeVerkoopprijs_1'
    data_to_plot.plot(column='GemiddeldeVerkoopprijs_1', ax=ax, cmap='viridis', legend=True)

    # Stel de titel van de plot in
    ax.set_title('Gemiddelde Verkoopprijs in 2015 in Euro')

    return fig
map_fig = plot_map(2015)

#lijnchart1 
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




#lijnchart2
# Create an interactive line plot with Plotly Express for the existing dataset
fig = px.line(index, x="Year", y="PrijsindexBestaandeKoopwoningen_1",
              labels={"PrijsindexBestaandeKoopwoningen_1": "Price Index Existing Homes_1"},
              hover_data=["PrijsindexBestaandeKoopwoningen_1"],
              line_shape='linear', render_mode='svg',
              title="Price Index Existing Homes")

# Add the CPI line in red with legend
fig.add_trace(go.Scatter(x=inflation['Year'], y=inflation['CPI_1'],
                         mode='lines',
                         line=dict(color='red', width=2),
                         name='CPI'))

# Add a horizontal line at the value 100
fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Value 100", annotation_position="top left")

# Update labels
fig.update_xaxes(title_text="Year")
fig.update_yaxes(title_text="Index")

# Add a legend
fig.update_layout(legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

# Train the model for Price Index Existing Homes
X_price_index = index[['Year']]
y_price_index = index['PrijsindexBestaandeKoopwoningen_1']

# Instantiate the regression model
model_price_index = LinearRegression()

# Train the model for Price Index Existing Homes
model_price_index.fit(X_price_index, y_price_index)

# Predict values for the period until '2050JJ00'
future_years_price_index = pd.DataFrame({'Year': np.arange(1995, 2051, 1)})  # Adjust to the desired period
predictions_price_index = model_price_index.predict(future_years_price_index[['Year']])

# Add the predictions to the plot for Price Index Existing Homes
fig.add_trace(go.Scatter(x=future_years_price_index['Year'], y=predictions_price_index,
                         mode='lines',
                         line=dict(color='purple', width=2),
                         name='Predicted Price Index'))

# Train the model for CPI
X_cpi = inflation[['Year']]
y_cpi = inflation['CPI_1']

# Instantiate the regression model
model_cpi = LinearRegression()

# Train the model for CPI
model_cpi.fit(X_cpi, y_cpi)

# Predict values for the period until '2050JJ00'
future_years_cpi = pd.DataFrame({'Year': np.arange(1995, 2051, 1)})  # Adjust to the desired period
predictions_cpi = model_cpi.predict(future_years_cpi[['Year']])

# Add the predictions to the plot for CPI
fig.add_trace(go.Scatter(x=future_years_cpi['Year'], y=predictions_cpi,
                         mode='lines',
                         line=dict(color='orange', width=2),
                         name='Predicted CPI'))
r_squared_price_index = model_price_index.score(X_price_index, y_price_index)
# Assess R-squared for CPI
r_squared_cpi = model_cpi.score(X_cpi, y_cpi)






# Streamlit section
st.title("De woningcrisis uitgedrukt in data")
st.caption("Door Emma Wartena & Luuk de Goede")
st.image('https://hips.hearstapps.com/hmg-prod/images/model-home-resting-on-top-of-us-paper-currency-royalty-free-image-1631301093.jpg?crop=1.00xw:0.376xh;0,0.126xh&resize=1200:*', caption='Credit: Elle.com')
st.write('''Een koopwoning krijgen is haast onmogelijk, je hoort het vaak genoeg in het nieuws of om je heen. Erg vervelend maar wat zijn nou oorzaken hiervan? En kunnen deze oorzaken uitgelicht worden door de data? En wat zegt de data over de toekomst? In deze post wordt ingezoomd op al deze punten. De data die gebruikt is, is afkomstig van het CBS en is van de periode 1995 tot 2022. ''')
st.subheader("Prijsindex koopwoningen Nederland (1995-2022)")
st.plotly_chart(fig1, use_container_width=True)
st.write('''In deze grafiek wordt de consumentprijsindex tegenover de prijsindex van de verkoopprijzen van huizen geplaatst. In de prijsindex, ofwel PBK,  wordt de prijsverandering gemeten van de voorraad bestaande koopwoningen in Nederland.
In de grafiek zijn twee belangrijke gebeurtenissen in het verleden weergegeven. Deze gebeurtenissen hebben duidelijk veel invloed gehad op de loop van de huizenmarkt. De prijsindex is 100 in 2015. Dit is dus het basisjaar waar alle waardes aan worden gerefereerd. Verder is er een duidelijke daling te zien na 2022. Dit komt door de invloed van de hypotheekrente die op dat punt weer zijn gestegen. Hierdoor kost lenen meer geld, en zijn mensen hier dus voorzichter mee. ''')
st.caption('Data bron: CBS')
st.divider()
st.subheader("Invloed van locatie op gemiddelde prijs")
st.pyplot(map_fig, use_container_width=True)
st.write('''De kaart hierboven geeft weer wat de gemiddelde verkoopprijs van een koophuis was in 2015 per gemeente. Hieruit valt op te maken dat de gemiddelde prijzen in steden en gebieden rond steden hoger zijn. Vooral in de randstad is dit prominent aanwezig. Ook is te zien dat in de uithoeken van het land de huisprijzen gemiddeld lager zijn. Op de eilanden zijn de prijzen echter wel weer wat hoger. ''')
st.caption('Data bron: GJSON township of the Netherlands 2015 / webuildinternet.com')
#kaart 2
gdfProv = gpd.GeoDataFrame(merged_data_prov, geometry=merged_data_prov['geometry'])
# Bepaal de minimale en maximale waarden voor de kleurschaal
min_val = gdfProv['GemiddeldeVerkoopprijs_1'].min()
max_val = gdfProv['GemiddeldeVerkoopprijs_1'].max()
# Functie om de kaart te plotten op basis van het jaar
def plot_map(year):
    data_to_plot = gdfProv[gdfProv['Perioden'] == year]

    # Creëer de plot met 'plasma' colormap
    fig, ax = plt.subplots(figsize=(10, 7))
    data_to_plot.plot(column='GemiddeldeVerkoopprijs_1', ax=ax, legend=True, cmap='plasma', legend_kwds={'label': "Gemiddelde verkoopprijs in Euro"}, vmin=min_val, vmax=max_val)
    plt.title(f"Kaart van Nederland in {year}")
    st.pyplot(fig)

# Lijst van jaren om in het dropdownmenu weer te geven
years_list = gdfProv['Perioden'].unique()

# Dropdownmenu voor het jaar
selected_year = st.selectbox('Selecteer een jaar', years_list)

# Genereer de kaart op basis van het geselecteerde jaar
plot_map(selected_year)
st.write('''Op de kaart is te zien hoe de gemiddelde prijs van een verkoopwoning per provincie is veranderd over de jaren (1995-2022). In de vroege jaren 1995-2000 is te zien dat de prijzen tussen de provincies niet zeer grote verschillen hebben. Met de jaren is echter te zien dat de verschillen tussen de provincies groter worden. Dit is goed te zien bij provincies als Noord-Holland. Het gemiddelde ligt veel hoger dan bij bijvoorbeeld Groningen. Nu is bestaat Noord-Holland natuurlijk niet alleen uit Amsterdam. Vergeleken de gemeentekaart is goed te zien dat er zeker in het noorden van Noord-Holland gebieden zijn met lagere prijzen. Dit duidt aan dat de prijzen in steden harder zijn gestegen dan in de rest van de provincie. Zo kan geconcludeerd worden dat de prijzen in steden (zeker in de randstad) harder zijn gestegen. ''')
st.caption('Data bron: GJSON provinces of the Netherlands / webuildinternet.com')
st.divider()
st.subheader('Toekomst perspectief ten opzichte van inflatie')
st.plotly_chart(fig, use_container_width = True)
st.write(f'R-squared for Price Index Existing Homes: {r_squared_price_index}')
st.write(f'R-squared for CPI: {r_squared_cpi}')
st.write(''' In deze grafiek is er een lineaire regressielijn geplot en zijn ook de CPI-waardes toegevoegd. De consumentenprijsindex, ofwel CPI, is een afgeleide van de inflatie. Dit wordt weergeven in een percentage index. Wanneer de CPI-waarde lager is dan de prijsindex betekent het dat er een grotere vraag is naar huizen dan de markt eigenlijk aan zou kunnen. Wanneer deze waardes dus gelijk zijn is er een stabiel vraag en aanbod op de markt.
 
Er is zowel een regressielijn voor de CPI als voor de PBK. Omdat de huizenmarkt door een gebeurtenis makkelijk te beïnvloeden is, is het moeilijk om eigenlijk al zo ver in de toekomst te kijken. Daardoor is de kwaliteit van het regressiemodel bepaald door de R-sqaured , ofwel  de determinatie coëfficiënt. . Deze percentages geven aan hoe goed het model in staat is om de toekomst te voorspellen. Voor de CPI is deze veel hoger, dan voor de PBK. Een oorzaak hiervan is dat de woningmarkt door veel gebeurtenis wordt beïnvloed, waardoor er in het verleden al veel schommelingen zichtbaar zijn. Hierdoor is de toekomst daarvoor minder precies te voorspellen. ''')
st.caption('Data bron: CBS')
st.divider()
st.subheader('Conclusie')
st.write('''Uit de visualisaties kan opgemaakt worden dat de woningcrisis een serieus probleem is. Als de prijzen op blijven lopen als deze doen bij de trendlijn zal snel iets moeten gebeuren. Het uiteenlopende CPI tegenover de groeiende prijzen versterkt dit. Verder kan geconcludeerd worden dat de prijzen in steden nog harder zijn gegroeid, misschien dat spreiding van de bevolking over het land voor de toekomst een goed idee is. ''')


