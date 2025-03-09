import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from babel.numbers import format_currency  # Add this import for currency formatting

# Load dataset
@st.cache_data
def load_data():
    return pd.read_csv("main_data.csv", parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "shipping_limit_date"
    ])

df = load_data()

# Sidebar filters
st.sidebar.header("Filter Data")
state_filter = st.sidebar.multiselect("Pilih Negara Bagian", df["customer_state"].unique())
category_filter = st.sidebar.multiselect("Pilih Kategori Produk", df["product_category_name"].unique())

# Apply filters
filtered_df = df.copy()
if state_filter:
    filtered_df = filtered_df[filtered_df["customer_state"].isin(state_filter)]
if category_filter:
    filtered_df = filtered_df[filtered_df["product_category_name"].isin(category_filter)]

st.title("Dashboard Brazilian E-Commerce by Olist")
st.markdown("Dashboard interaktif untuk mengeksplorasi data transaksi pelanggan.")

# Top Selling Products
st.subheader("Top 10 Product with Best Performing")

wanted_product = filtered_df.groupby("product_category_name")["item_count"].sum().reset_index()
most_wanted_product = wanted_product.sort_values(by="item_count", ascending=False).head(10)
fewest_wanted_product = wanted_product.sort_values(by="item_count", ascending=True).head(10)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
colors = ["lightcoral", "lightcoral", "lightcoral", "lightcoral", "lightcoral", "skyblue","skyblue","skyblue","skyblue","skyblue"]

sns.barplot(x="item_count", y="product_category_name", data=most_wanted_product, palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="item_count", y="product_category_name", data=fewest_wanted_product, palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
st.pyplot(fig)

# Shipping Duration Analysis
st.subheader("Distribusi Durasi Pengiriman")

# Tampilkan metrik dalam 2 kolom
col1, col2 = st.columns(2)
with col1:
    avg_payment_duration = round(filtered_df["payment_duration"].mean(), 2)
    st.metric("⏳ Rata-rata Durasi Pembayaran (jam)", value=f"{avg_payment_duration} jam")
with col2:
    avg_shipping_duration = round(filtered_df["shipping_duration"].mean(), 2)
    st.metric("🚚 Rata-rata Durasi Pengiriman (hari)", value=f"{avg_shipping_duration} hari")

# Visualisasi distribusi durasi pengiriman
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(filtered_df['shipping_duration'], bins=20, kde=True, color='skyblue', ax=ax)
ax.set_title("Distribusi Durasi Pengiriman")
st.pyplot(fig)

# Geospatial Analysis
st.subheader("Statistik Pola Pembelian Pelanggan Berdasarkan Lokasi")

demand_stats = filtered_df.groupby("demand_category").agg({
    "item_count": ["mean", "sum", "count"]
}).reset_index()
demand_stats.columns = ["Demand Category", "Avg Orders", "Total Orders", "Customer Count"]

col1, col2, col3 = st.columns(3)
# Tampilkan rata-rata pesanan
with col1:
    st.metric(label="📦 Rata-rata Pesanan", value=f"{demand_stats['Avg Orders'].mean():.2f}")
# Tampilkan total pesanan
with col2:
    st.metric(label="🛒 Total Pesanan", value=f"{demand_stats['Total Orders'].sum()}")
# Tampilkan jumlah pelanggan unik
with col3:
    st.metric(label="👥 Jumlah Pelanggan", value=f"{demand_stats['Customer Count'].sum()}")

# Subheader untuk Peta
st.markdown("### Clustering Daerah berdasarkan Demand")

m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4, tiles="CartoDB positron")
# Warna berdasarkan kategori demand
demand_colors = {
    "Low Demand": "lightcoral",
    "Medium Demand": "skyblue",
    "High Demand": "mediumseagreen"
}

# Iterasi setiap baris dalam DataFrame
for _, row in filtered_df.iterrows():
    folium.CircleMarker(
        location=[row['customer_lat'], row['customer_lng']],
        radius=2,  # Ukuran marker lebih besar untuk visibilitas
        color=demand_colors.get(row['demand_category'], "gray"),  # Default gray jika tidak ada kategori
        fill=True,
        fill_opacity=0.5,
        popup=f"State: {row['customer_state']}<br>Demand: {row['demand_category']}<br>Total Orders: {row['item_count']}"
    ).add_to(m)
folium_static(m)

# RFM Analysis
st.subheader("Analisis RFM Pelanggan")

rfm_df = filtered_df.groupby("customer_id").agg({
    "order_purchase_timestamp": "max",
    "order_id": "nunique",
    "total_order_value": "sum"
}).reset_index()
rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
rfm_df["recency"] = (df["order_purchase_timestamp"].max() - rfm_df["max_order_timestamp"]).dt.days

## Statistics Information 
col1, col2, col3 = st.columns(3)
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
with col3:
    avg_monetary = round(rfm_df.monetary.mean(), 2) 
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(1, 3, figsize=(35, 10))

sns.histplot(rfm_df['recency'], bins=20, kde=True, ax=ax[0], color='skyblue')
ax[0].set_title("Distribusi Recency")
sns.histplot(rfm_df['frequency'], bins=20, kde=True, ax=ax[1], color='skyblue')
ax[1].set_title("Distribusi Frequency")
sns.histplot(rfm_df['monetary'], bins=20, kde=True, ax=ax[2], color='skyblue')
ax[2].set_title("Distribusi Monetary")
st.pyplot(fig)

st.markdown("---")
st.markdown("2025 © Cintya Kusumawardhani MC008D5X2337")
