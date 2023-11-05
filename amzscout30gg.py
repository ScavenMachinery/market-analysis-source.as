import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import locale
import duckdb
from PIL import Image
from ipyvizzu import Chart, Data, Config 

# Carica un'immagine per l'icona della pagina
img = Image.open('tondino3.png')
image = Image.open('logo.bettershop.png')

# Imposta la configurazione della pagina
st.set_page_config(
        layout="wide",
        page_title='Market Analysis',
        page_icon=img)

# Mostra un'immagine nell'intestazione
st.image(image, width=400)

# Titolo della pagina
st.title("ANALISI DI MERCATO 30 GIORNI")
st.markdown("_source.as v.1.0_")

# Nascondi la scritta "made with streamlit" nel footer
hide_style = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# Carica il file Excel
@st.cache_data
def load_data(file):
    data = pd.read_excel(file)
    return data

uploaded_file = st.sidebar.file_uploader("Scegli un file Excel")

if uploaded_file is None:
    st.info("Carica un file tramite il menu laterale")
    st.stop()

df = load_data(uploaded_file)




# Scelta del tipo di analisi
analisi_type = st.sidebar.radio("Seleziona il tipo di analisi:", [None, "RISULTATO BRAND", "RISULTATO CATEGORIA"])


if analisi_type == "RISULTATO BRAND":
    # Rimuovi le colonne specifiche
    brand_name = st.sidebar.text_input("Inserisci il nome del BRAND:")

    columns_to_remove = ["Netto", "Commissioni FBA", "Margine netto", "LQS", "Peso"]
    df_cleaned = df.drop(columns=columns_to_remove, axis=1)

    # Formatta la colonna "Disponibile da" come data
    df_cleaned["Disponibile da"] = pd.to_datetime(df_cleaned["Disponibile da"], errors="coerce").dt.strftime("%d/%m/%Y")

    # Rimuovi i duplicati basati sulla colonna "ASIN"
    df_cleaned = df_cleaned.drop_duplicates(subset=["ASIN"])

    # Converte le celle vuote in "Vendite stimate" in 1 se "Entrate stimate" contiene un valore
    mask = (df_cleaned["Vendite stimate"].isna()) & (df_cleaned["Entrate stimate"].notna())
    df_cleaned.loc[mask, "Vendite stimate"] = 1

    # Rimuovi le righe in cui entrambe le colonne sono vuote
    df_cleaned = df_cleaned.dropna(subset=["Vendite stimate", "Entrate stimate"], how="all")

    if brand_name:
        # Filtra il DataFrame in base al nome del brand
        df_cleaned = df_cleaned[df_cleaned["Marca"].str.contains(brand_name, case=False, na=False)]
        if df_cleaned.empty:
            st.sidebar.warning("NESSUN BRAND RILEVATO")

    # Espandi il DataFrame pulito per la visualizzazione
    with st.expander("Anteprima dei dati puliti"):
        st.dataframe(df_cleaned)

    # KPIs
    total_Revenue = df_cleaned["Entrate stimate"].sum()
    total_Sales = df_cleaned["Vendite stimate"].sum()
    asp = df_cleaned["Prezzo"].mean()

    formatted_total_revenues = "{:,.2f}".format(total_Revenue).replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_total_units = "{:,.2f}".format(total_Sales).replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_asp = "{:,.2f}".format(asp).replace(",", "X").replace(".", ",").replace("X", ".")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"{formatted_total_revenues} €")

    with col2:
        st.metric(
            label="Total Sales",
            value=f"{formatted_total_units}")
    
    with col3:
        st.metric(
            label="Average Selling Price",
            value=f"{formatted_asp} €")


    #FULFILLMENT KPIS

    fatturato_FBA = df_cleaned[df['Venditore'] == 'FBA']['Entrate stimate'].sum()
    fatturato_MFN = df_cleaned[df['Venditore'] == 'MCH']['Entrate stimate'].sum()
    fatturato_AMZ = df_cleaned[df['Venditore'] == 'AMZ']['Entrate stimate'].sum()

    incidenza_FBA = (fatturato_FBA / total_Revenue) * 100
    incidenza_MFN = ( fatturato_MFN / total_Revenue) * 100
    incidenza_AMZ = (fatturato_AMZ / total_Revenue) * 100

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            label="FBA",
            value="{:.2f} %".format(incidenza_FBA))

    with col5:
        st.metric(
            label="MCH/FBM",
            value="{:.2f} %".format(incidenza_MFN))


    with col6:
        st.metric(
            label="AMZ",
            value="{:.2f} %".format(incidenza_AMZ))
        
    colA, colB= st.columns(2)

    # Calcola il conteggio di ASIN e Marca
    count_asin = df_cleaned["ASIN"].nunique()
    count_brand = df_cleaned["Marca"].nunique()

    with colA:
        st.metric("Conteggio ASIN", count_asin, "ASIN")

    with colB:
        st.metric("Conteggio BRAND", count_brand, "Marca")


    #ANALISI PER PRODOTTI NEL RISULTATO BRAND

    st.subheader("_Visualizzazione TOP BRAND per Revenue e Unita'_", divider ="orange")

    # Seleziona il grafico da visualizzare

    selected_chart = st.selectbox("Seleziona il grafico da visualizzare", ["ASIN BY REVENUES", "ASIN BY UNITS"])

    col7, col8 = st.columns(2)

    ASIN_revenues = df_cleaned.groupby("ASIN").sum().nlargest(10, "Entrate stimate")

    fig1 = px.bar(ASIN_revenues,
                x=ASIN_revenues.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
                y="Entrate stimate",
                title="Top 10 ASIN by Revenue")

    ASIN_units = df_cleaned.groupby("ASIN").sum().nlargest(10, "Vendite stimate")

    fig2 = px.bar(ASIN_units,
                x=ASIN_units.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
                y="Vendite stimate",
                title="Top 10 ASIN by Units")

    # Ordina il DataFrame in base al fatturato (in ordine decrescente)
    df_sorted_revenues = df_cleaned.sort_values(by="Entrate stimate", ascending=False)
    df_sorted_units = df_cleaned.sort_values(by="Vendite stimate", ascending=False)


    # Seleziona solo le colonne "ASIN" e "Product Details"
    preview_table1 = df_sorted_revenues[["ASIN", "Nome prodotto","Prezzo"]]
    preview_table2 = df_sorted_units[["ASIN", "Nome prodotto","Prezzo"]]


    # Visualizza il grafico selezionato
    if selected_chart == "ASIN BY REVENUES":
        with col7:
            st.plotly_chart(fig1)
        with col8:
            st.dataframe(preview_table1)
    else:
        with col7:
            st.plotly_chart(fig2)
        with col8:
            st.dataframe(preview_table2)


    st.subheader("_Quote di mercato e Prezzo_", divider ="orange")

    col9, col10 =st.columns(2)

   # Calcola le quote di mercato percentuali per i primi 10 ASIN
    top_10_ASIN = df_cleaned.groupby("ASIN")["Entrate stimate"].sum().nlargest(10)
    ASIN_market_share_percentage = top_10_ASIN / top_10_ASIN.sum() * 100

    # Crea un DataFrame con le quote di mercato percentuali
    market_share_df = pd.DataFrame({
        "ASIN": top_10_ASIN.index,
        "Market Share (%)": ASIN_market_share_percentage.values})
    
# Crea il grafico a torta per i primi 10 brand
    fig_pie = px.pie(market_share_df,
                 names="ASIN",
                 values="Market Share (%)",
                 title="Quote di Mercato dei Top 10 ASIN")

    with col9:
        st.plotly_chart(fig_pie)

    # Crea il sottografo con due assi y
    fig3 = go.Figure()

    # Aggiungi il grafico a barre per le quote di mercato sull'asse y sinistra
    fig3.add_trace(go.Bar(x=market_share_df["ASIN"], y=market_share_df["Market Share (%)"], name="Quote di Mercato (%)"))

    # Crea un secondo asse y per i valori in colonna "Prezzo"
    fig3.update_layout(yaxis=dict(title="Quote di Mercato (%)", titlefont=dict(color="blue")),
                    yaxis2=dict(title="Prezzo", titlefont=dict(color="red"), overlaying="y", side="right"))
    fig3.add_trace(go.Scatter(x=market_share_df["ASIN"], y=[df_cleaned[df_cleaned["ASIN"] == asin]["Prezzo"].mean() for asin in top_10_ASIN.index],
                         mode="lines+markers", name="Prezzo", yaxis="y2"))

    # Imposta il titolo del grafico
    fig3.update_layout(title="Quote di Mercato e Prezzo dei Top 10 ASIN")

    # Imposta le etichette degli assi
    fig3.update_xaxes(title_text="ASIN")

    with col10:
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("_Analisi Sales Rank / Vendite stimate_", divider ="orange")

    col11, col12 = st.columns([1,1])
    ASIN_ratings = df_cleaned.groupby("ASIN").sum().nsmallest(10, "Piazzamento")

    # Rimuovi le righe in cui "Piazzamento" è vuoto o uguale a zero
    ASIN_ratings = ASIN_ratings.dropna(subset=["Piazzamento"])
    ASIN_ratings = ASIN_ratings[ASIN_ratings["Piazzamento"] > 0]

    # Ordina il DataFrame in modo crescente in base al "Piazzamento"
    ASIN_ratings = ASIN_ratings.sort_values(by="Piazzamento")

    fig4 = px.bar(
        ASIN_ratings,
        x="Piazzamento",
        y=ASIN_ratings.index,
        title="Top 10 ASIN by Sales Rank",
        orientation="h")

    fig4.update_traces(marker_color="lightblue", marker_line_width=1.5)

    fig4.update_layout(
        xaxis_title="Piazzamento",
        yaxis_title="ASIN",
        yaxis=dict(autorange="reversed"))
    
    with col11:
        st.plotly_chart(fig4)

    preview_table3 = df_cleaned[["ASIN", "Nome prodotto","Piazzamento","Vendite stimate"]]

    with col12:
        st.dataframe(preview_table3)

    
    #GRAFICO CONFRONTO PIAZZAMENTO VENDITE E PREZZO
    # Seleziona i primi 10 ASIN in base alle Vendite stimate
    top_10_ASIN = df_cleaned.nlargest(10, 'Vendite stimate')

    fig6 = go.Figure()

    # Aggiungi le barre per Vendite stimate e Piazzamento sull'asse y sinistra
    fig6.add_trace(go.Bar(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Vendite stimate'], name='Vendite stimate', yaxis='y', marker_color='blue'))
    fig6.add_trace(go.Bar(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Piazzamento'], name='Piazzamento', yaxis='y', marker_color='lightblue'))

    # Aggiungi il Prezzo come linea sull'asse y destra
    fig6.add_trace(go.Scatter(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Prezzo'], name='Prezzo', yaxis='y2', mode='lines+markers', line=dict(color='green')))

    # Imposta i titoli degli assi e del grafico
    fig6.update_layout(
        title='Confronto tra Vendite stimate, Piazzamento e Prezzo per i primi 10 ASIN per Vendite stimate',
        xaxis_title='ASIN',
        yaxis_title='Vendite/Piazzamento',
        yaxis2=dict(
            title='Prezzo',
            overlaying='y',
            side='right'))

    # Visualizza il grafico
    st.plotly_chart(fig6, use_container_width=True)







    st.subheader("_Analisi scostamento Sales rank da BSR 30_", divider ="orange")


    # GRAFICO VARIAZIONE % PIAZZAMENTO E BSR 30
    col13, col14 =st.columns(2)
    # Crea un nuovo DataFrame con le colonne desiderate
    df_variazione = df_cleaned[["ASIN", "Nome prodotto", "Piazzamento", "BSR 30"]]

    # Calcola la percentuale di variazione tra "Piazzamento" e "BSR 30"
    df_variazione["Variazione %"] = ((df_variazione["Piazzamento"] - df_variazione["BSR 30"]) / df_variazione["BSR 30"]) * 100

    # Ordina il nuovo DataFrame in base alla variazione %
    df_variazione = df_variazione.sort_values(by="Piazzamento")

    with col14:
        st.dataframe(df_variazione)

    # Aggiungi un filtro per il range di valori Variazione %
    variazione_range = st.slider("Seleziona un range di Variazione %", min_value=-100, max_value=100, value=(-100, 100))

    # Crea il DataFrame filtrato in base al range selezionato
    filtered_df_variazione = df_variazione[(df_variazione["Variazione %"] >= variazione_range[0]) & (df_variazione["Variazione %"] <= variazione_range[1])]

    # Crea il grafico a barre con i dati filtrati
    fig5_filtered = px.bar(filtered_df_variazione, x="ASIN", y="Variazione %", title="Variazione % tra Piazzamento e BSR 30 per ASIN")

    # Imposta le etichette degli assi
    fig5_filtered.update_xaxes(title_text="ASIN")
    fig5_filtered.update_yaxes(title_text="Variazione %")

    # Colora le barre in base al valore di Variazione %
    colors_filtered = ["green" if val < 0 else "red" for val in filtered_df_variazione["Variazione %"]]
    fig5_filtered.update_traces(marker=dict(color=colors_filtered))

    # Visualizza il grafico
    with col13:
        st.plotly_chart(fig5_filtered)

    #COMMENTO IMPORTANTE!
    st.markdown("considerazioni importanti:")
    st.markdown("in merito al confronto tra Sales rank (Piazzamento) e Variazione % è importante ricordarsi che i dati estratti dalla source sono una fotografia del tracciamento. Infatti una discrepanza riscontrata è che per alcuni ASIN è stato rilevato una variazione % positiva del sales rank ma nonostante ciò la stima del venduto è 1 in quanto la posizione in classifica attuale rimane comunque alta.\n\n Se si vuole avere un traciamento più dinamico si potrebbe identificare e confrontare a quanto corrisponde il BSR 30 in termini di vendite con la stima di vendite della posizione attuale così da poter dire che negli ultimi 30gg si è passati da un sales rank a un altro con una variazione di stima di vendite x.")

    #ANNOTAZIONI IMPORTANTI: Prendere come esempio l'ASIN B0B74RSBQZ BSR 30 56k a Piazzamento attuale 1.2k e dire: nell'ultimo periodo si stima un aumento delle vendite di tot distribuito irregolarmente nel periodo.


    st.subheader("_Analisi Entrate stimate e Recensioni_", divider ="orange")



    # GRAFICO RPR CONFRONTO ENTRATE STIMATE E NUMERO DI REVIEWS
    # Ordina il DataFrame per "Entrate stimate" in ordine decrescente e prendi i primi 10 ASIN
    df = df_cleaned.sort_values(by="Entrate stimate", ascending=False).head(10)

    # Crea il grafico a barre per "Entrate stimate" e "# di recensioni"
    fig7 = go.Figure()

    fig7.add_trace(go.Bar(x=df["ASIN"], y=df["Entrate stimate"], name="Entrate stimate"))
    fig7.add_trace(go.Bar(x=df["ASIN"], y=df["# di recensioni"], name="# di recensioni"))

    # Aggiungi il grafico a linea per "RPR"
    fig7.add_trace(go.Scatter(x=df["ASIN"], y=df["RPR"], mode="lines", name="RPR", yaxis="y2"))

    # Imposta le etichette degli assi
    fig7.update_layout(
        xaxis=dict(title="ASIN"),
        yaxis=dict(title="Valore", titlefont=dict(color="blue"), tickfont=dict(color="blue")),
        yaxis2=dict(title="RPR", titlefont=dict(color="red"), tickfont=dict(color="red"),
                    overlaying="y", side="right"))

    # Imposta il titolo del grafico
    fig7.update_layout(title="Confronto tra Entrate stimate, # di recensioni e RPR Top 10 ASIN per Entrate stimate")

    # Mostra il grafico
    st.plotly_chart(fig7, use_container_width=True)


    st.subheader("_Conteggi_", divider ="orange")


    # Raggruppa i dati per la colonna "Varianti" e conta il numero di occorrenze
    varianti_counts = df_cleaned['Varianti'].value_counts().reset_index()
    varianti_counts.columns = ['Varianti', 'Count']

    # Crea il grafico a barre
    fig8 = px.bar(varianti_counts, x='Varianti', y='Count', title='Conteggio delle Varianti')
    fig8.update_xaxes(categoryorder='total ascending')  # Ordina le etichette x in ordine crescente

    # Visualizza il grafico
    st.plotly_chart(fig8, use_container_width=True)

    # Raggruppa i dati per la colonna "Categoria" e conta il numero di occorrenze
    categoria_counts = df_cleaned['Categoria'].value_counts().reset_index()
    categoria_counts.columns = ['Categoria', 'Count']

    # Crea il grafico a barre
    fig9 = px.bar(categoria_counts, x='Categoria', y='Count', title='Conteggio delle Categorie')
    fig9.update_xaxes(categoryorder='total ascending')  # Ordina le etichette x in ordine crescente

    # Visualizza il grafico
    st.plotly_chart(fig9, use_container_width=True)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------BLOCCO CODICE ANALISI CATEGORIA-----------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------


elif analisi_type == "RISULTATO CATEGORIA":
    # Blocco di codice per l'analisi della categoria
    # Rimuovi le colonne specifiche
    columns_to_remove = ["Netto", "Commissioni FBA", "Margine netto", "LQS", "Peso"]
    df_cleaned = df.drop(columns=columns_to_remove, axis=1)

    # Formatta la colonna "Disponibile da" come data
    df_cleaned["Disponibile da"] = pd.to_datetime(df_cleaned["Disponibile da"], errors="coerce").dt.strftime("%d/%m/%Y")

    # Rimuovi i duplicati basati sulla colonna "ASIN"
    df_cleaned = df_cleaned.drop_duplicates(subset=["ASIN"])

    # Converte le celle vuote in "Vendite stimate" in 1 se "Entrate stimate" contiene un valore
    mask = (df_cleaned["Vendite stimate"].isna()) & (df_cleaned["Entrate stimate"].notna())
    df_cleaned.loc[mask, "Vendite stimate"] = 1

    # Rimuovi le righe in cui entrambe le colonne sono vuote
    df_cleaned = df_cleaned.dropna(subset=["Vendite stimate", "Entrate stimate"], how="all")

    # Espandi il DataFrame pulito per la visualizzazione
    with st.expander("Anteprima dei dati puliti"):
        st.dataframe(df_cleaned)

    
    #KPIS
    # KPIs
    total_Revenue = df_cleaned["Entrate stimate"].sum()
    total_Sales = df_cleaned["Vendite stimate"].sum()
    asp = df_cleaned["Prezzo"].mean()

    formatted_total_revenues = "{:,.2f}".format(total_Revenue).replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_total_units = "{:,.2f}".format(total_Sales).replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_asp = "{:,.2f}".format(asp).replace(",", "X").replace(".", ",").replace("X", ".")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"{formatted_total_revenues} €")

    with col2:
        st.metric(
            label="Total Sales",
            value=f"{formatted_total_units}")
    
    with col3:
        st.metric(
            label="Average Selling Price",
            value=f"{formatted_asp} €")


    #FULFILLMENT KPIS

    fatturato_FBA = df_cleaned[df['Venditore'] == 'FBA']['Entrate stimate'].sum()
    fatturato_MFN = df_cleaned[df['Venditore'] == 'MCH']['Entrate stimate'].sum()
    fatturato_AMZ = df_cleaned[df['Venditore'] == 'AMZ']['Entrate stimate'].sum()

    incidenza_FBA = (fatturato_FBA / total_Revenue) * 100
    incidenza_MFN = ( fatturato_MFN / total_Revenue) * 100
    incidenza_AMZ = (fatturato_AMZ / total_Revenue) * 100

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            label="FBA",
            value="{:.2f} %".format(incidenza_FBA))

    with col5:
        st.metric(
            label="MCH/FBM",
            value="{:.2f} %".format(incidenza_MFN))


    with col6:
        st.metric(
            label="AMZ",
            value="{:.2f} %".format(incidenza_AMZ))
        

    colA, colB= st.columns(2)

    # Calcola il conteggio di ASIN e Marca
    count_asin = df_cleaned["ASIN"].nunique()
    count_brand = df_cleaned["Marca"].nunique()

    with colA:
        st.metric("Conteggio ASIN", count_asin, "ASIN")

    with colB:
        st.metric("Conteggio BRAND", count_brand, "Marca")
        


    st.subheader("_Visualizzazione TOP BRAND per Revenue e Unita'_", divider ="orange")
    #GRAFICO DEI BRANDS
    col7, col8 = st.columns(2)

    
    #GRAFICO 1
    Brand_revenues = df_cleaned.groupby("Marca").sum().nlargest(10, "Entrate stimate")

    fig1 = px.bar(Brand_revenues,
                x=Brand_revenues.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
                y="Entrate stimate",
                title="Top 10 Brands by Revenue")

    with col7:
        st.plotly_chart(fig1)

    Brand_units = df_cleaned.groupby("Marca").sum().nlargest(10, "Vendite stimate")

    fig2 = px.bar(Brand_units,
                x=Brand_units.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
                y="Vendite stimate",
                title="Top 10 Brands by Units")

    with col8:
        st.plotly_chart(fig2)

    st.subheader("_Quote di mercato e Prezzo_", divider ="orange")

    col9, col10 =st.columns(2)

   # Calcola le quote di mercato percentuali per i primi 10 ASIN
    top_10_ASIN = df_cleaned.groupby("Marca")["Entrate stimate"].sum().nlargest(10)
    ASIN_market_share_percentage = top_10_ASIN / top_10_ASIN.sum() * 100

    # Crea un DataFrame con le quote di mercato percentuali
    market_share_df = pd.DataFrame({
        "Marca": top_10_ASIN.index,
        "Market Share (%)": ASIN_market_share_percentage.values})
    
    # Crea il grafico a torta per i primi 10 brand
    fig_pie = px.pie(market_share_df,
                 names="Marca",
                 values="Market Share (%)",
                 title="Quote di Mercato dei Top 10 Brand")

    with col9:
        st.plotly_chart(fig_pie)



    # Crea il sottografo con due assi y
    fig3 = go.Figure()

    # Aggiungi il grafico a barre per le quote di mercato sull'asse y sinistra
    fig3.add_trace(go.Bar(x=market_share_df["Marca"], y=market_share_df["Market Share (%)"], name="Quote di Mercato (%)"))

    # Crea un secondo asse y per i valori in colonna "Prezzo"
    fig3.update_layout(yaxis=dict(title="Quote di Mercato (%)", titlefont=dict(color="blue")),
                    yaxis2=dict(title="Prezzo", titlefont=dict(color="red"), overlaying="y", side="right"))
    fig3.add_trace(go.Scatter(x=market_share_df["Marca"], y=[df_cleaned[df_cleaned["Marca"] == asin]["Prezzo"].mean() for asin in top_10_ASIN.index],
                         mode="lines+markers", name="Prezzo", yaxis="y2"))

    # Imposta il titolo del grafico
    fig3.update_layout(title="Quote di Mercato e Prezzo dei Top 10 Brand")

    # Imposta le etichette degli assi
    fig3.update_xaxes(title_text="Brand")

    with col10:
        st.plotly_chart(fig3, use_container_width=True)


    st.subheader("_Analisi Sales Rank / Vendite stimate_", divider ="orange")

    #GRAFICO RANKS
    # Filtro per la colonna "Marca"
    selected_brand = st.selectbox("Seleziona un Brand", df_cleaned["Marca"].unique())
    col11, col12 = st.columns([1, 1])

    # Filtra il DataFrame in base alla Marca selezionata
    filtered_df = df_cleaned[df_cleaned["Marca"] == selected_brand]

    ASIN_ratings = filtered_df.groupby("ASIN").sum().nsmallest(10, "Piazzamento")

    # Rimuovi le righe in cui "Piazzamento" è vuoto o uguale a zero
    ASIN_ratings = ASIN_ratings.dropna(subset=["Piazzamento"])
    ASIN_ratings = ASIN_ratings[ASIN_ratings["Piazzamento"] > 0]

    # Ordina il DataFrame in modo crescente in base al "Piazzamento"
    ASIN_ratings = ASIN_ratings.sort_values(by="Piazzamento")

    fig4 = px.bar(
        ASIN_ratings,
        x="Piazzamento",
        y=ASIN_ratings.index,
        title="Top 10 ASIN by Sales Rank",
        orientation="h")

    fig4.update_traces(marker_color="lightblue", marker_line_width=1.5)

    fig4.update_layout(
        xaxis_title="Piazzamento",
        yaxis_title="ASIN",
        yaxis=dict(autorange="reversed"))

    with col11:
        st.plotly_chart(fig4)

    preview_table3 = filtered_df[["ASIN", "Nome prodotto", "Piazzamento", "Vendite stimate"]]

    with col12:
        st.dataframe(preview_table3)


    #GRAFICO CONFRONTO PIAZZAMENTO VENDITE E PREZZO
    # Seleziona i primi 10 ASIN in base alle Vendite stimate

    filtered_df = df_cleaned[df_cleaned["Marca"] == selected_brand]

    # Seleziona i primi 10 ASIN in base alle Vendite stimate
    top_10_ASIN = filtered_df.nlargest(10, 'Vendite stimate')

    fig5 = go.Figure()

    # Aggiungi le barre per Vendite stimate e Piazzamento sull'asse y sinistra
    fig5.add_trace(go.Bar(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Vendite stimate'], name='Vendite stimate', yaxis='y', marker_color='blue'))
    fig5.add_trace(go.Bar(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Piazzamento'], name='Piazzamento', yaxis='y', marker_color='lightblue'))

    # Aggiungi il Prezzo come linea sull'asse y destra
    fig5.add_trace(go.Scatter(x=top_10_ASIN['ASIN'], y=top_10_ASIN['Prezzo'], name='Prezzo', yaxis='y2', mode='lines+markers', line=dict(color='green')))

    # Imposta i titoli degli assi e del grafico
    fig5.update_layout(
        title=f'Confronto tra Vendite stimate, Piazzamento e Prezzo per i primi 10 ASIN per {selected_brand}',
        xaxis_title='ASIN',
        yaxis_title='Vendite/Piazzamento',
        yaxis2=dict(
            title='Prezzo',
            overlaying='y',
            side='right'))

    # Visualizza il grafico
    st.plotly_chart(fig5, use_container_width=True)



    st.subheader("_Analisi scostamento Sales rank da BSR 30_", divider ="orange")

    # GRAFICO VARIAZIONE % PIAZZAMENTO E BSR 30
    # Aggiungi un filtro multiplo per "Marca"
    selected_brands = st.multiselect("Seleziona una o più Brands", df_cleaned["Marca"].unique(), default=df_cleaned["Marca"].unique())
    col13, col14 = st.columns(2)

    # Crea un nuovo DataFrame con le colonne desiderate
    df_variazione = df_cleaned[["ASIN", "Nome prodotto", "Piazzamento", "BSR 30", "Marca"]]

    # Filtra il DataFrame in base alle Marcas selezionate
    df_variazione = df_variazione[df_variazione["Marca"].isin(selected_brands)]

    # Calcola la percentuale di variazione tra "Piazzamento" e "BSR 30"
    df_variazione["Variazione %"] = ((df_variazione["Piazzamento"] - df_variazione["BSR 30"]) / df_variazione["BSR 30"]) * 100

    # Ordina il nuovo DataFrame in base alla variazione %
    df_variazione = df_variazione.sort_values(by="Piazzamento")

    with col14:
        st.dataframe(df_variazione)

    # Aggiungi un filtro per il range di valori Variazione %
    variazione_range = st.slider("Seleziona un range di Variazione %", min_value=-100, max_value=100, value=(-100, 100))

    # Crea il DataFrame filtrato in base al range selezionato
    filtered_df_variazione = df_variazione[(df_variazione["Variazione %"] >= variazione_range[0]) & (df_variazione["Variazione %"] <= variazione_range[1])]

    # Crea il grafico a barre con i dati filtrati
    fig6_filtered = px.bar(filtered_df_variazione, x="ASIN", y="Variazione %", title="Variazione % tra Piazzamento e BSR 30 per ASIN")

    # Imposta le etichette degli assi
    fig6_filtered.update_xaxes(title_text="ASIN")
    fig6_filtered.update_yaxes(title_text="Variazione %")

    # Colora le barre in base al valore di Variazione %
    colors_filtered = ["green" if val < 0 else "red" for val in filtered_df_variazione["Variazione %"]]
    fig6_filtered.update_traces(marker=dict(color=colors_filtered))

    # Visualizza il grafico
    with col13:
        st.plotly_chart(fig6_filtered)




    st.subheader("_Analisi Entrate stimate e Recensioni_", divider ="orange")


    # Aggiungi un filtro per "BRAND"
    selected_brands2 = st.multiselect("Seleziona una o più Brand", df["Marca"].unique(), default=df["Marca"].unique())

    col14, col15 = st.columns(2)

    # GRAFICO RPR CONFRONTO ENTRATE STIMATE E NUMERO DI REVIEWS
    # Ordina il DataFrame per "Entrate stimate" in ordine decrescente e prendi i primi 10 ASIN
    df = df.sort_values(by="Entrate stimate", ascending=False)
    

    # Filtra il DataFrame in base ai Brand selezionati
    df = df[df["Marca"].isin(selected_brands2)]

    # Crea il grafico a barre per "Entrate stimate" e "# di recensioni"
    fig7 = go.Figure()

    fig7.add_trace(go.Bar(x=df["ASIN"], y=df["Entrate stimate"], name="Entrate stimate"))
    fig7.add_trace(go.Bar(x=df["ASIN"], y=df["# di recensioni"], name="# di recensioni"))

    # Aggiungi il grafico a linea per "RPR"
    fig7.add_trace(go.Scatter(x=df["ASIN"], y=df["RPR"], mode="lines", name="RPR", yaxis="y2"))

    # Imposta le etichette degli assi
    fig7.update_layout(
        xaxis=dict(title="ASIN"),
        yaxis=dict(title="Valore", titlefont=dict(color="blue"), tickfont=dict(color="blue")),
        yaxis2=dict(title="RPR", titlefont=dict(color="red"), tickfont=dict(color="red"),
                    overlaying="y", side="right"))

    # Imposta il titolo del grafico
    fig7.update_layout(title="Confronto tra Entrate stimate, # di recensioni e RPR Top 10 ASIN per Entrate stimate")

    # Mostra il grafico
    with col14:
        st.plotly_chart(fig7, use_container_width=True)

    df_tab = df_cleaned[["ASIN", "Nome prodotto", "Entrate stimate", "# di recensioni", "RPR"]]

    # Filtra il DataFrame in base alle Marcas selezionate
    df_tab = df_tab[df_cleaned["Marca"].isin(selected_brands2)]


    # Ordina il nuovo DataFrame in base alla variazione %
    df_tab = df_tab.sort_values(by="Entrate stimate")

    with col15:
        st.dataframe(df_tab)


    st.subheader("_Distribuzione fatturato tra le gestioni fulfillment_", divider ="orange")

    top_10_brands = df_cleaned.groupby("Marca")["Entrate stimate"].sum().nlargest(10)
    filtered_df = df_cleaned[df_cleaned["Marca"].isin(top_10_brands.index)]

    # Definisci un set personalizzato di colori per le colonne
    color_discrete_map = {
        "FBA": "blue",  # Cambia i colori a tuo piacimento
        "MCH/FBM": "lightgreen",
        "AMZ": "orange"}

    # Crea un grafico a barre raggruppato con il set di colori personalizzato
    fig8 = px.bar(filtered_df, x="Marca", y="Entrate stimate", color="Venditore", title="Fatturato per FBA, MCH/FBM e AMZ dei Top 10 Brand",
                barmode="group", color_discrete_map=color_discrete_map)

    # Visualizza il grafico con larghezza adattabile
    st.plotly_chart(fig8, use_container_width=True)


    st.subheader("_Conteggi_", divider ="orange")

    # Raggruppa i dati per la colonna "Varianti" e conta il numero di occorrenze
    varianti_counts = df_cleaned['Varianti'].value_counts().reset_index()
    varianti_counts.columns = ['Varianti', 'Count']

    # Crea il grafico a barre
    fig9 = px.bar(varianti_counts, x='Varianti', y='Count', title='Conteggio delle Varianti')
    fig9.update_xaxes(categoryorder='total ascending')  # Ordina le etichette x in ordine crescente

    # Visualizza il grafico
    st.plotly_chart(fig9, use_container_width=True)

    # Raggruppa i dati per la colonna "Categoria" e conta il numero di occorrenze
    categoria_counts = df_cleaned['Categoria'].value_counts().reset_index()
    categoria_counts.columns = ['Categoria', 'Count']

    # Crea il grafico a barre
    fig10 = px.bar(categoria_counts, x='Categoria', y='Count', title='Conteggio delle Categorie')
    fig10.update_xaxes(categoryorder='total ascending')  # Ordina le etichette x in ordine crescente

    # Visualizza il grafico
    st.plotly_chart(fig10, use_container_width=True)