import plotly.express as px
import streamlit as st
import pandas as pd
import json

from streamlit_plotly_events import plotly_events

@st.cache_data
def load_filter_options_from_json():
    with open("filters.json", "r") as f:
        filters = json.load(f)
    return filters

@st.cache_data
def load_filtered_data(province=None, city=None):
    query = []
    if province:
        query.append(("nm_prop", "in", province))
    if city:
        query.append(("nm_rayon", "in", city))
    data = pd.read_parquet("skor-abm-detail.parquet", filters=query)
    return data

st.set_page_config(
    page_title="ABM Report",
    layout="wide"
)

filters = load_filter_options_from_json()

st.markdown("<h1 style='text-align: center;'>Analisis Bakat dan Minat</h1>", unsafe_allow_html=True)
print("")
st.write("")
st.write("")

col1, col2, col3 = st.columns(3)
with col1:
    selected_provinces = st.multiselect(
        "Pilih Provinsi (Wajib)", 
        options=sorted(filters["nm_prop"]),
        help="Pilih satu atau lebih provinsi untuk filter data"
    )

province_filtered_df = None
available_cities = []
available_schools = []
final_filtered_df = pd.DataFrame()

if selected_provinces:
    province_filtered_df = load_filtered_data(province=selected_provinces)
    available_cities = sorted(province_filtered_df["nm_rayon"].unique())

with col2:
    selected_cities = st.multiselect(
        "Pilih Kota/Kabupaten (Opsional)",
        options=available_cities,
        help="Pilih satu atau lebih kota untuk filter data"
    )

if selected_cities:
    city_filtered_df = load_filtered_data(
        province=selected_provinces, 
        city=selected_cities
    )
    available_schools = sorted(city_filtered_df["nm_sek"].unique())

with col3:
    selected_schools = st.multiselect(
        "Pilih Sekolah (Opsional)",
        options=available_schools,
        help="Pilih satu atau lebih sekolah untuk filter data"
    )

if selected_schools:
    final_filtered_df = city_filtered_df[
        city_filtered_df["nm_sek"].isin(selected_schools)
    ]
elif selected_cities:
    final_filtered_df = city_filtered_df
elif selected_provinces:
    final_filtered_df = province_filtered_df

if not final_filtered_df.empty:
    minat_cols = final_filtered_df.columns[final_filtered_df.columns.str.contains("minat")]

    for minat_col in minat_cols:
        final_filtered_df[f"{minat_col}_ket"] = final_filtered_df[minat_col].apply(
            lambda x: "Minat" if x >= 60 else "Tidak Minat"
        )

    with st.expander("Klik di sini untuk melihat data"):
        st.dataframe(final_filtered_df, hide_index=True, use_container_width=True)

    bakat_columns = ["bakat_1_ket", "bakat_2_ket", "bakat_3_ket", "bakat_4_ket", "bakat_5_ket", "bakat_6_ket", "bakat_7_ket"]
    melted_df = final_filtered_df.melt(value_vars=bakat_columns, var_name="bakat_type", value_name="bakat_ket")
    hue_order = ["Tidak Terukur", "Kurang", "Sedang", "Baik"]
    aggregated_df = melted_df.groupby(["bakat_type", "bakat_ket"]).size().reset_index(name="count")

    rename_mapping = {
        "bakat_1_ket": "Kemampuan Spasial",
        "bakat_2_ket": "Kemampuan Verbal",
        "bakat_3_ket": "Penalaran",
        "bakat_4_ket": "Kemampuan Klerikal",
        "bakat_5_ket": "Kemampuan Mekanika",
        "bakat_6_ket": "Kemampuan Kuantitatif",
        "bakat_7_ket": "Kemampuan Bahasa",
        "minat_1_ket": "Fasilitasi Sosial",
        "minat_2_ket": "Pengelolaan",
        "minat_3_ket": "Detail Bisnis",
        "minat_4_ket": "Pengelolaan Data",
        "minat_5_ket": "Keteknikan",
        "minat_6_ket": "Kerja Lapangan",
        "minat_7_ket": "Kesenian",
        "minat_8_ket": "Helping",
        "minat_9_ket": "Sains Sosial",
        "minat_10_ket": "Influence",
        "minat_11_ket": "Sistem Bisnis",
        "minat_12_ket": "Analisis Finansial",
        "minat_13_ket": "Kerja Ilmiah",
        "minat_14_ket": "Quality Control",
        "minat_15_ket": "Kerja Manual",
        "minat_16_ket": "Personal Service",
        "minat_17_ket": "Keteknisian",
        "minat_18_ket": "Layanan Dasar"
    }

    with st.container(border=True):
        show_real_values = st.checkbox("Tampilkan Nilai Real", value=False)

        aggregated_df["percentage"] = (
            aggregated_df["count"] / aggregated_df.groupby("bakat_type")["count"].transform("sum")
        ) * 100

        if show_real_values:
            y_axis = "count"
            y_label = "Jumlah"
            text_template = "%{text}"
        else:
            y_axis = "percentage"
            y_label = "Persentase (%)"
            text_template = "%{text:.2f}%"

        fig = px.bar(
            aggregated_df,
            x="bakat_type",
            y=y_axis,
            color="bakat_ket",
            title="Distribusi Kategori Bakat",
            category_orders={"bakat_ket": hue_order},
            labels={"bakat_type": "Bakat", y_axis: y_label, "bakat_ket": "Kategori Bakat"},
            color_discrete_map={
                "Tidak Terukur": "#f7b787",
                "Kurang": "#fed76a",
                "Sedang": "#64ccc5",
                "Baik": "#176b87"
            }
        )

        fig.update_layout(
            barmode="stack",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            plot_bgcolor="white",
            showlegend=True,
            uniformtext_minsize=14,
            uniformtext_mode="hide",
            margin=dict(t=30)
        )

        fig.update_xaxes(
            ticktext=[rename_mapping.get(val, val).replace(" ", "<br>") for val in aggregated_df["bakat_type"].unique()],
            tickvals=aggregated_df["bakat_type"].unique()
        )

        for trace in fig.data:
            trace.update(
                text=trace.y,
                textposition="inside",
                texttemplate=text_template,
                textfont=dict(size=16, color="#424242")
            )

        selected_bakat_dict = plotly_events(fig, click_event=True)

    st.info("Silakan klik salah satu bar di atas untuk melihat minat", icon="ℹ")

    if selected_bakat_dict:
        selected_bakat = selected_bakat_dict[0]["x"]

        minat_df = final_filtered_df[
            [selected_bakat] + [col for col in final_filtered_df.columns if "minat_" in col and "ket" in col]
        ]

        categories = ["Baik", "Sedang", "Kurang", "Tidak Terukur"]

        cols = st.columns(2)
        for i, category in enumerate(categories):
            category_filtered_df = minat_df[minat_df[selected_bakat] == category]

            minat_aggregated = category_filtered_df.melt(
                id_vars=[selected_bakat],
                value_vars=[col for col in minat_df.columns if "minat_" in col],
                var_name="minat_type",
                value_name="minat_ket"
            ).groupby(["minat_type", "minat_ket"]).size().reset_index(name="count")

            minat_aggregated["percentage"] = (
                minat_aggregated["count"]
                / minat_aggregated.groupby("minat_type")["count"].transform("sum")
            ) * 100

            top_minat = (
                minat_aggregated[minat_aggregated["minat_ket"] == "Minat"]
                .nlargest(5, "count")
                .reset_index()
            )
            top_categories = top_minat["minat_type"].unique()
            filtered_df = minat_aggregated[minat_aggregated["minat_type"].isin(top_categories)]
            filtered_df = filtered_df.sort_values(by=["percentage"], ascending=False)

            fig = px.bar(
                filtered_df,
                x="minat_type",
                y="percentage",
                color="minat_ket",
                title=f"Top 5 Minat untuk '{rename_mapping.get(selected_bakat)}' Kategori '{category}'",
                category_orders={"minat_ket": ["Tidak Minat", "Minat"]},
                color_discrete_map = {
                    "Minat": "#64ccc5",
                    "Tidak Minat": "#f7b787",
                },
                labels={"percentage": "Persentase (%)", "minat_type": "Minat", "minat_ket": "Kategori Minat"},
            )

            fig.update_layout(
                barmode="stack",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                plot_bgcolor="white",
                showlegend=True,
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                margin=dict(t=30)
            )

            fig.update_traces(
                texttemplate="%{y:.2f}%",
                textposition="inside",
                textfont=dict(size=12, color="#424242")
            )

            fig.update_xaxes(
                ticktext=[rename_mapping.get(val, val).replace(" ", "<br>") for val in minat_aggregated["minat_type"].unique()],
                tickvals=minat_aggregated["minat_type"].unique()
            )

            col = cols[i % 2]
            with col:
                with st.container(border=True):
                    plotly_events(fig, click_event=False)

else:
    st.info("Silakan pilih satu atau lebih provinsi", icon="ℹ")