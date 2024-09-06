import streamlit as st
import psycopg2
import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_folium import folium_static
import folium
import plotly.graph_objects as go
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Function to connect to the database
def connect_to_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# Custom CSS to improve layout
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stAlert {
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .st-emotion-cache-1v0mbdj {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Streamlit app
def main():
    st.title("Belgian Organizations Employing in .NET")

    # Connect to the database and fetch data
    conn = connect_to_db()
    cur = conn.cursor()

    # Fetch data from the table, including the new columns
    cur.execute("SELECT * FROM public_dbt.a_final_kenze_companies")
    data = cur.fetchall()

    # Convert data to a pandas DataFrame
    df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])

    # Add a new section to display the complete dataframe
    st.subheader("Complete Dataset")
    st.write("This table shows the complete dataset from the a_final_kenze_companies query:")
    st.dataframe(df)


    # Modify the filtering section
    st.sidebar.title("Filters")
    if 'industry' in df.columns:
        selected_industries = st.sidebar.multiselect("Select Industries", df['industry'].unique())
    else:
        selected_industries = []
        st.sidebar.warning("Industry data not available")

    if 'employee_count' in df.columns:
        min_employees = st.sidebar.number_input("Minimum Employees", min_value=0, value=0, key="sidebar_min_employees")
        max_employees = st.sidebar.number_input("Maximum Employees", min_value=0, value=int(df['employee_count'].max()), key="sidebar_max_employees")
    else:
        min_employees, max_employees = 0, float('inf')
        st.sidebar.warning("Employee count data not available")

    # Filter the dataframe
    filtered_df = df[
        (df['industry'].isin(selected_industries) if selected_industries and 'industry' in df.columns else True) &
        (df['employee_count'] >= min_employees if 'employee_count' in df.columns else True) &
        (df['employee_count'] <= max_employees if 'employee_count' in df.columns else True)
    ]

    # Project Overview
    st.markdown("### 🔍 Project Overview")
    st.info("""
    This project is based on the following assumptions:
    1. LinkedIn is the most accurate & up-to-date source for company and employee data.
    2. Every .NET developer mentioned this in their profile.
    3. Every LinkedIn profile has an associated LinkedIn company identification.
    
    The goal is to identify and analyze organizations in Flanders that employ .NET software engineers,
    providing valuable insights for targeting and market analysis.
    
    Approach:
    
    Step 1. Scrape LinkedIn profiles of .NET developers in Flanders
    
    Step 2. Use the data to create a list of companies that employ .NET developers
    
    Step 3. Collect company data from LinkedIn Company Pages
    
    Step 4. Scrape all LinkedIn profiles of employees of these companies
    
    Step 5. Label employees on '.NET' skills, 'Department' and 'Seniority'
    
    Step 6. Scrape all Google My Business (GMB) profiles of these companies
    
    Step 7. Scrape all company websites with focus on job pages
    
    Step 8. Scrape financial data
    
    """)

    # New section: Query Results Graph
    st.markdown("### 📊 Step 1: Search .NET Profiles")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        Starting with a LinkedIn search, profiles were collected using various keywords such as ".NET" or "dotNET." 
        However, LinkedIn's search results are not always fully accurate when specific filters are applied. 
        The profiles were then screened for .NET-related skills and experience, identifying unique companies where employees with .NET skills are employed.

        To enable downstream analysis, it is crucial to gather information about these companies. However, not all profiles included employer details, which limited the ability to conduct a comprehensive analysis based on company information.""")

    # Connect to the database
    conn = connect_to_db()
    cur = conn.cursor()

    # Execute the correct query
    cur.execute("""
    SELECT 
        COUNT(*) AS total_result,
        COUNT(CASE WHEN net_profile = TRUE THEN 1 END) AS net_profile_true,
        (SELECT COUNT(DISTINCT companyid) 
         FROM kenze_profile_search 
         WHERE net_profile = TRUE) AS distinct_companyid_count
    FROM kenze_profile_search;
    """)
    
    result = cur.fetchone()
    
    # Calculate values
    total_profiles, net_profiles, distinct_companies = result

    # Create data for the nested bubble chart
    data = {
        "ids": ["Total", "NET", "Companies"],
        "labels": ["Total Profiles", ".NET Profiles", "Unique Companies"],
        "parents": ["", "Total", "NET"],
        "values": [total_profiles, net_profiles, distinct_companies],
        "colors": ['#FFFFFF', '#66b3ff', '#ffcc99']
    }

    # Create the Sunburst chart
    fig = go.Figure(go.Sunburst(
        ids=data['ids'],
        labels=data['labels'],
        parents=data['parents'],
        values=data['values'],
        marker=dict(
            colors=data['colors'],
            line=dict(color=['#000000', '#FFFFFF', '#FFFFFF'], width=[2, 0, 0])  # Add border to Total Profiles
        ),
        textinfo="label+value",
        hoverinfo="label+value+percent parent+percent root",
        textfont=dict(size=16, color="black"),
    ))

    # Update layout
    fig.update_layout(
        title={
            'text': "Profile Statistics",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        width=1000,
        height=800,
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)

    # Display the raw numbers with some formatting
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Profiles", f"{total_profiles:,}")
    with col2:
        st.metric(".NET Profiles", f"{net_profiles:,}")
    with col3:
        st.metric("Unique Companies", f"{distinct_companies:,}")

    # Create a geo map
    if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
        # Convert latitude and longitude to float if they're not already
        filtered_df['latitude'] = pd.to_numeric(filtered_df['latitude'], errors='coerce')
        filtered_df['longitude'] = pd.to_numeric(filtered_df['longitude'], errors='coerce')

        # Remove rows with null values in latitude or longitude
        df_map = filtered_df.dropna(subset=['latitude', 'longitude'])

        # Filter for Belgium (approximate bounding box)
        belgium_lat_min, belgium_lat_max = 49.5, 51.5
        belgium_lon_min, belgium_lon_max = 2.5, 6.4
        df_belgium = df_map[
            (df_map['latitude'] >= belgium_lat_min) & 
            (df_map['latitude'] <= belgium_lat_max) & 
            (df_map['longitude'] >= belgium_lon_min) & 
            (df_map['longitude'] <= belgium_lon_max)
        ]

        if not df_belgium.empty:
            st.subheader("Interactive Company Map")
            map_filters = st.expander("Map Filters", expanded=False)
            with map_filters:
                map_industries = st.multiselect("Filter by Industry", df_belgium['industry'].unique())
                min_employees_map = st.number_input("Minimum Employees", min_value=0, value=0, key="map_min_employees")
                max_employees_map = st.number_input("Maximum Employees", min_value=0, value=int(df_belgium['employee_count'].max()), key="map_max_employees")
                if 'net_dev_count' in df_belgium.columns:
                    min_net_devs = st.number_input("Minimum .NET Developers", min_value=0, value=0, key="map_min_net_devs")

            filtered_map_df = df_belgium[
                (df_belgium['industry'].isin(map_industries) if map_industries else True) &
                (df_belgium['employee_count'] >= min_employees_map) &
                (df_belgium['employee_count'] <= max_employees_map) &
                (df_belgium['net_dev_count'] >= min_net_devs if 'net_dev_count' in df_belgium.columns else True)
            ]

            if not filtered_map_df.empty:
                m = folium.Map(location=[filtered_map_df['latitude'].mean(), filtered_map_df['longitude'].mean()], zoom_start=8)
                
                for idx, row in filtered_map_df.iterrows():
                    popup_content = f"<strong>{row.get('company_name', 'N/A')}</strong>"
                    if 'employee_count' in row:
                        popup_content += f"<br>Employees: {row['employee_count']}"
                    if 'net_dev_count' in row:
                        popup_content += f"<br>.NET Devs: {row['net_dev_count']}"
                    if 'industry' in row:
                        popup_content += f"<br>Industry: {row['industry']}"
                    
                    folium.Marker(
                        [row['latitude'], row['longitude']],
                        popup=popup_content,
                        tooltip=row.get('company_name', 'Company')
                    ).add_to(m)
                
                folium_static(m)

                # Add a table with company data
                st.subheader("Filtered Company Data")
                columns_to_display = ['company_name', 'industry', 'employee_count', 'total', 'it_engineering', 'net_profile', 'net_profile_vs_total_ratio', 'it_team_percentage', 'it_executive_vs_it_specialist_ratio', 'specialist_vs_total_ratio', 'net_profile_vs_it_engineering_ratio', 'technical_executive', 'operations', 'customer_success', 'finance,', 'sales','marketing','human_resources', 'specialist', 'senior', 'executive', 'advisor', 'cli_url', 'founded', 'hq_city', 'tagline', 'cli_website', 'vat_number', 'cover_image', 'description', 'followercount', 'universal_name', 'logo_resulution', 'employee_count_range', 'equity', 'fte_employees', 'profit_loss', 'gross_margin', 'cid', 'gmb_title', 'rating', 'gmb_address', 'category', 'phone_number', 'rating_count', 'wc_description', 'wc_business_type', 'wc_hiring', 'wc_about_section', 'wc_pricing_mentioned', 'wc_trial_available', 'wc_keywords', 'wc_career_urls', 'wc_social_media', 'wc_open_positions', 'wc_ideal_customer_profile', 'wc_case_studies', 'wc_contact_info' ] 
                if 'net_dev_count' in filtered_map_df.columns:
                    columns_to_display.append('net_dev_count')
                
                # Only include columns that exist in the dataframe
                available_columns = [col for col in columns_to_display if col in filtered_map_df.columns]
                
                if available_columns:
                    total_results = len(filtered_map_df)
                    st.dataframe(filtered_map_df[available_columns].head(10).reset_index(drop=True), use_container_width=True)
                    st.info(f"Total results: {total_results}. Showing top 10 companies, all companies will be enabled in final delivery.")
                    
                    # New download section with info
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = filtered_map_df[available_columns].to_csv(index=False)
                        st.download_button(
                            label="Download data as CSV",
                            data=csv,
                            file_name="company_data.csv",
                            mime="text/csv",
                            disabled=True
                        )
                    with col2:
                        st.info("The download CSV button will be enabled in the final delivery.")
                else:
                    st.warning("No relevant columns available to display.")
            else:
                st.warning("No companies match the selected filters.")
        else:
            st.warning("No valid data points found within Belgium.")
    else:
        st.warning("Latitude and longitude columns not found in the data.")

    # Industry Distribution
    st.subheader("Industry Distribution")
    industry_counts = filtered_df['industry'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=industry_counts.index, values=industry_counts.values)])
    fig.update_layout(title="Distribution of Companies by Industry")
    st.plotly_chart(fig)

    # Company Size Distribution
    st.subheader("Company Size Distribution")
    size_bins = [0, 10, 50, 250, 1000, float('inf')]
    size_labels = ['1-10', '11-50', '51-250', '251-1000', '1000+']
    filtered_df['size_category'] = pd.cut(filtered_df['employee_count'], bins=size_bins, labels=size_labels, right=False)
    size_dist = filtered_df['size_category'].value_counts().sort_index()

    fig = go.Figure(data=[go.Bar(x=size_dist.index, y=size_dist.values)])
    fig.update_layout(title="Distribution of Companies by Size", xaxis_title="Company Size", yaxis_title="Number of Companies")
    st.plotly_chart(fig)

    # .NET Developer Concentration
    st.subheader(".NET Developer Concentration")
    if 'net_dev_count' in filtered_df.columns and 'employee_count' in filtered_df.columns:
        filtered_df['net_dev_count'] = pd.to_numeric(filtered_df['net_dev_count'], errors='coerce')
        filtered_df['employee_count'] = pd.to_numeric(filtered_df['employee_count'], errors='coerce')
        filtered_df['net_dev_percentage'] = (filtered_df['net_dev_count'] / filtered_df['employee_count']) * 100
        fig = go.Figure(data=[go.Histogram(x=filtered_df['net_dev_percentage'])])
        fig.update_layout(title=".NET Developer Concentration", xaxis_title="Percentage of .NET Developers", yaxis_title="Number of Companies")
        st.plotly_chart(fig)
    else:
        st.warning(".NET developer concentration data not available")

    # Top Companies Table
    st.subheader("Top Companies")
    if 'company_name' in filtered_df.columns:
        columns_to_display = ['company_name']
        if 'industry' in filtered_df.columns:
            columns_to_display.append('industry')
        if 'employee_count' in filtered_df.columns:
            columns_to_display.append('employee_count')
        if 'net_dev_count' in filtered_df.columns:
            columns_to_display.append('net_dev_count')
        if 'net_profile' in filtered_df.columns:
            columns_to_display.append('net_profile')
        if 'net_profile_vs_total_ratio' in filtered_df.columns:
            columns_to_display.append('net_profile_vs_total_ratio')
        
        top_companies = filtered_df.sort_values('net_dev_count', ascending=False).head(10)
        st.table(top_companies[columns_to_display])
    else:
        st.warning("Company data not available")

if __name__ == "__main__":
    main()