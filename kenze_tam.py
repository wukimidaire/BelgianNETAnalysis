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

# Function to connect to the database
def connect_to_db():
    conn = psycopg2.connect(
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"]
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

    # Remove the "Complete Dataset" section and associated table

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

    # Step 1: Search .NET Profiles
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

    # Step 2: Company List Creation
    st.markdown("### 📊 Step 2: Company List Creation")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        After identifying .NET developers from LinkedIn profiles, we compiled a list of unique companies that employ these developers. This step involved:

        1. Extracting LinkedIn company identificition (company_id's) from the .NET developers' profiles.
        2. Removing duplicates to create a list of unique companies.
        3. Validating the company information to ensure accuracy.

        This list serves as the foundation for our further analysis, providing a targeted set of companies known to employ .NET developers in Belgium.
        """)

    # Step 3: Company Data Collection
    st.markdown("### 📊 Step 3: Company Data Collection")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        Using the list of companies identified in Step 2, we collected comprehensive data from LinkedIn Company Pages. This process involved:

        1. Scraping public information from each company's LinkedIn page.
        2. Gathering key data points such as:
           - Company size (employee count)
           - Industry
           - Location
           - Founded year
           - Specialties
           - Website URL
           - Company description
           - ...
        3. Organizing and structuring the collected data for analysis.

        This step enriches our dataset with valuable company-level information, 
        allowing for more in-depth analysis and insights about the organizations employing .NET developers in Flanders.
        
        Note: Companies associated with .NET developer profiles that have an empty company_id are excluded from the final dataset. The impact on completeness is expected to be minimal.
        """)

    # Add this new section for the query visualization
    conn = connect_to_db()
    cur = conn.cursor()

    # Execute the query
    cur.execute("""
    WITH kenze_profile_search AS (
        SELECT DISTINCT
            companyid
        FROM
            kenze_profile_search
        WHERE
            companyid IS NOT NULL
            AND companyid != ''
            AND net_profile = TRUE
    ),
    cli_search AS (
        SELECT
            company_id,
            enrichment_timestamp
        FROM
            cli
    )
    SELECT
        count(a.companyid) as companies_found,
        count(b.company_id) as companies_enirched,
        CASE 
        WHEN count(a.companyid) > 0 THEN
            ROUND((count(b.company_id)::DECIMAL / count(a.companyid)::DECIMAL) * 100, 1)
        ELSE
            0
    END as percentage_complete
    FROM
        kenze_profile_search AS a
        FULL JOIN cli_search AS b on a.companyid = b.company_id::VARCHAR
    where a.companyid is not null
    """)

    result = cur.fetchone()
    companies_found, companies_enriched, percentage_complete = result

    # Create a more fancy bar chart
    fig = go.Figure()

    # Add bars
    fig.add_trace(go.Bar(
        x=['Companies'],
        y=[companies_found],
        name='Companies Found',
        marker_color='royalblue',
        text=[companies_found],
        textposition='outside',
        hoverinfo='y+name'
    ))

    fig.add_trace(go.Bar(
        x=['Companies'],
        y=[companies_enriched],
        name='Companies Enriched',
        marker_color='lightgreen',
        text=[companies_enriched],
        textposition='outside',
        hoverinfo='y+name'
    ))

    # Customize the layout
    fig.update_layout(
        title={
            'text': 'Company Data Enrichment Progress',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        xaxis_title='',
        yaxis_title='Number of Companies',
        barmode='group',
        bargap=0.3,
        bargroupgap=0.1,
        legend=dict(
            x=0.5,
            y=-0.15,
            xanchor='center',
            yanchor='top',
            orientation='h'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
            dict(
                x=0.5,
                y=max(companies_found, companies_enriched) * 1.1,
                xref="paper",
                yref="y",
                text=f"Completion: {percentage_complete}%",
                showarrow=False,
                font=dict(size=20, color='green')
            )
        ]
    )

    # Update axes
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    # Add a shape to show the target
    fig.add_shape(
        type="line",
        x0=-0.5, y0=companies_found, x1=0.5, y1=companies_found,
        line=dict(color="red", width=3, dash="dash"),
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display additional information
    st.info(f"""
    - Total companies found: {companies_found}
    - Companies enriched with LinkedIn data: {companies_enriched}
    - Percentage complete: {percentage_complete}%
    """)

    # Step 4: Employee Profile Scraping and Data Processing
    st.markdown("### 📊 Step 4: Employee Profile Scraping, Data Processing & Labeling")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        In this step, we expanded our data collection to include profiles of all employees from the companies identified in Step 2, followed by comprehensive data processing. This process involved:

        ### 1. Data Collection

        - Systematically scraped public LinkedIn profiles of employees from each company
        - Gathered key data points: job titles, skills, experience, and other relevant information
        - Ensured data privacy compliance by only collecting publicly available information

        #### Involved Challenges:

        - Varying data availability on LinkedIn profiles
        - LinkedIn API restrictions limiting access to bulk data
        - Need for IP rotation using proxy servers to avoid detection and blocking
        - Careful management of request frequency to avoid temporary bans
        - Development of CAPTCHA handling strategies
        - Ensuring compliance with LinkedIn's terms of service and data protection regulations
        - Dealing with variations in profile structures and incomplete information

        ### 2. Data Cleaning and Categorization
        
        #### a. .NET Skills Identification:
        - Analyzed profile content to identify employees with .NET-related skills or experience
        - Utilized keyword matching and natural language processing techniques to detect .NET expertise
        - Considered factors such as listed skills, job titles, and project descriptions

        #### b. Seniority Classification:
        - **Advisor**: Board members, shareholders, chairmen, investors
        - **Executive**: C-level positions, founders, partners, business owners
        - **Senior**: Team leads, heads of departments, senior positions, directors
        - **Specialist**: Default category for roles not matching above criteria    

        #### c. Tenure Calculation:
        - Converted text-based duration into numeric values (total months within company)

        #### d. Department Classification:
        - Marketing
        - Sales
        - Customer Success
        - Finance
        - Human Resources
        - Legal
        - IT/Engineering
        - Operations (default if multiple/no clear department)

        This comprehensive approach provides a deeper understanding of workforce composition in companies employing .NET developers. 
        It enables more accurate analysis of seniority levels, tenure, and departmental distribution, offering valuable insights into the structure and expertise within these organizations.
        """)
        
    # Execute the query
    cur.execute("""
    WITH subquery1 AS (
        SELECT 
            companyid, 
            min(vmid) as vmid, 
            min(employee_scrape_timestamp) as min_timestamp
        FROM
            kenze_profile_search
        WHERE
            companyid IS NOT NULL 
            AND companyid != ''
            AND employee_scrape_timestamp IS NULL 
            AND net_profile = TRUE
        GROUP BY companyid
    ),
    subquery2 AS (
        SELECT 
            companyid, 
            COUNT(companyid) AS kenze_pli_employee_count
        FROM
            kenze_pli_profiles
        WHERE
            companyid IS NOT NULL
        GROUP BY companyid
    ),
    cli_search AS (
        SELECT
            company_id AS companyid_c,
            hq_country,
            employee_count,
            enrichment_timestamp
        FROM
            cli
        WHERE
            hq_country = 'BE'
    )
    SELECT 
        COUNT(DISTINCT subquery1.companyid) AS companies_found, 
        COUNT(DISTINCT CASE WHEN  subquery2.companyid IS NOT NULL THEN cli_search.companyid_c END) AS collected,
        COUNT(DISTINCT CASE WHEN  subquery2.companyid IS NULL THEN cli_search.companyid_c END) AS to_collect,
        SUM(subquery2.kenze_pli_employee_count) AS profiles_collected
    FROM
        subquery1
        LEFT JOIN subquery2 ON subquery1.companyid = subquery2.companyid
        FULL JOIN cli_search ON subquery1.companyid = cli_search.companyid_c::VARCHAR
    WHERE
        subquery1.companyid IS NOT NULL 
        AND subquery1.companyid != ''
    """)

    result = cur.fetchone()
    companies_found, collected, to_collect, profiles_collected = result

    # Convert profiles_collected to float
    profiles_collected = float(profiles_collected)

    # Create two columns for the graphs
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Company Data")
        
        # Create a pie chart for company data
        fig1 = go.Figure(data=[go.Pie(
            labels=['Collected', 'To Collect'],
            values=[collected, to_collect],
            hole=.3,
            marker_colors=['#66b3ff', '#ff9999']
        )])
        
        fig1.update_layout(
            title="Employee Collection Status",
            annotations=[dict(text=f'Total: {companies_found}', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Profile Data")
        
        # Create a gauge chart for profile collection progress
        fig2 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = profiles_collected,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Profiles Collected", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, profiles_collected * 1.5], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, profiles_collected], 'color': 'cyan'},
                    {'range': [profiles_collected, profiles_collected * 1.5], 'color': 'royalblue'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': profiles_collected}}))

        fig2.update_layout(font = {'color': "darkblue", 'family': "Arial"})
        
        st.plotly_chart(fig2, use_container_width=True)

    # Display additional information
    st.info(f"""
    - Total companies found: {companies_found}
    - Companies with employees collected: {collected}
    - Companies remaining to collect employees: {to_collect}
    - Total profiles collected: {profiles_collected}
    """)

    # Step 5: Google My Business (GMB) Profile Scraping
    st.markdown("### 📊 Step 5: Google My Business (GMB) Profile Scraping")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        To enhance the accuracy and completeness of our company data, we collect Google My Business (GMB) profiles. 
        This step is crucial for obtaining additional financial data and gaining a more comprehensive view of each company's size, industry, and location.

        Key aspects of this process include:

        1. Automated searches:
           - Developed a system to automatically search for each company on Google My Business
           - Implemented measures to handle rate limiting and ensure efficient data collection

        2. Data extraction:
           - Google My Business activity description
           - Precise address and contact details
           - Customer reviews and overall ratings
           - ...

        3. Data integration:
           - Merged GMB data with our existing dataset
           - Resolved conflicts and discrepancies between different data sources
           - Standardized data formats for consistent analysis

        Benefits of this approach:
        - Improved data accuracy: Cross-referencing information from multiple sources
        - Enhanced company profiles: More detailed and up-to-date information
        - Better location data: Precise addresses for improved geographical analysis
        - Customer insights: Reviews and ratings provide a sense of company reputation

        This step significantly enriches our dataset, providing valuable context about each company's public presence, customer perception, and local business operations. 
        The additional data points allow for more nuanced analysis and insights into the .NET development landscape in Belgium.
        """)

    # Execute the query
    cur.execute("""
    WITH kenze_profile_search AS (
        SELECT DISTINCT
            companyid
        FROM
            kenze_profile_search
        WHERE
            companyid IS NOT NULL
            AND companyid != ''
            AND net_profile = TRUE
    ),
    cli_search AS (
        SELECT
            company_id,
            enrichment_timestamp, 
            serper_addressscrape_timestamp, 
            website, 
            hq_line1, 
            hq_postalcode, 
            company_name
        FROM
            cli
    ),
    gmb_search AS ( 
        SELECT 
            company_id AS gmb_company_id 
        FROM 
            google_my_business_locations
    ),
    joined_data AS (
        SELECT
            a.companyid,
            b.company_id,
            c.gmb_company_id
        FROM
            kenze_profile_search AS a
            LEFT JOIN cli_search AS b ON a.companyid = b.company_id::VARCHAR
            LEFT JOIN gmb_search AS c ON a.companyid = c.gmb_company_id::VARCHAR
        WHERE
            a.companyid IS NOT NULL
            AND b.company_id IS NOT NULL
            AND b.serper_addressscrape_timestamp IS NOT NULL
    )
    SELECT
        COUNT(*) AS total_companies,
        ROUND(
            (COUNT(CASE WHEN gmb_company_id IS NULL THEN 1 END) * 100.0) / COUNT(*),
            2
        ) AS gmb_companies_not_found 
    FROM
        joined_data
    """)

    result = cur.fetchone()
    total_companies, gmb_companies_not_found = result

    # Calculate the percentage of companies found on GMB
    gmb_companies_found = 100 - gmb_companies_not_found

    # Create a pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Found on GMB', 'Not Found on GMB'],
        values=[gmb_companies_found, gmb_companies_not_found],
        hole=.3,
        marker_colors=['#66b3ff', '#ff9999']
    )])

    fig.update_layout(
        title="Google My Business (GMB) Profile Coverage",
        annotations=[dict(text=f'Total: {total_companies}', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display additional information
    st.info(f"""
    - Total companies: {total_companies}
    - Companies found on GMB: {round(gmb_companies_found, 2)}%
    - Companies not found on GMB: {gmb_companies_not_found}%
    """)

    # Step 6: Company Website Scraping
    st.markdown("### 📊 Step 6: Company Website Scraping")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        This step provides insights into the companies' current needs and growth trajectories, especially in relation to .NET development.
        Company website scraping, with a particular focus on job pages, is a crucial step in gathering highly valuable information:

        1. Website content provides essential insights into:
           - Company business type and industry focus
           - Products or services offered
           - Company culture and values
           - Recent news or developments

        2. Job postings, especially for .NET positions, offer critical data on:
           - Current hiring needs and growth areas
           - Technical stack and programming languages used
           - Cloud environments and infrastructure preferences
           - Security compliance requirements
           - Other relevant technologies and tools

        3. This information is vital for:
           - Accurately identifying business types and market positioning
           - Understanding companies' technical setups and preferences
           - Analyzing trends in hiring practices and technology adoption
           - Assessing companies' growth trajectories and focus areas

        The process involves:
        1. Developing tailored web scrapers for different website structures
        2. Extracting and analyzing relevant information
        3. Identifying patterns and insights across multiple companies

        Challenges in this process include:
        - Varying website structures and data availability
        - Rate limiting and IP rotation requirements
        - CAPTCHA handling
        - Dealing with incomplete or inconsistent data
        - Differences in website layouts and structures

        
        Note: 
        Initially, HTML text is extracted. 
        After setup, the software stack used to manage the website can be identified and analyzed by checking for specific software vendor website snippets. 
        This analysis can reveal additional insights into the company's technical preferences and infrastructure. 
        """)

    # Execute the query for Step 6
    cur.execute("""
    WITH kenze_profile_search AS (
        SELECT DISTINCT
            companyid
        FROM
            kenze_profile_search
        WHERE
            companyid IS NOT NULL
            AND companyid != ''
            AND net_profile = TRUE
    ),
    cli_search AS (
        SELECT
            company_id,
            enrichment_timestamp, 
            serper_addressscrape_timestamp, 
            website, 
            hq_line1, 
            hq_postalcode, 
            company_name,
            embed_website_timestamp
        FROM
            cli
        where website is not null and website != ''
    ),
    joined_data AS (
        SELECT
            a.companyid,
            b.company_id,
            b.embed_website_timestamp,b.website
        FROM
            kenze_profile_search AS a
            LEFT JOIN cli_search AS b ON a.companyid = b.company_id::VARCHAR
            
        WHERE
            a.companyid IS NOT NULL
            AND b.company_id IS NOT NULL
    )
    SELECT 
        COUNT(*) AS total_companies,
        ROUND((COUNT(CASE WHEN embed_website_timestamp IS NULL THEN 1 END) * 100.0) / COUNT(*), 2 ) AS websites_to_embed 
    FROM
        joined_data
    """)

    result = cur.fetchone()
    total_companies, websites_to_embed = result

    # Calculate the percentage of websites embedded
    websites_embedded = 100 - websites_to_embed

    # Create a pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Websites Embedded', 'Websites to Embed'],
        values=[websites_embedded, websites_to_embed],
        hole=.3,
        marker_colors=['#66b3ff', '#ff9999']
    )])

    fig.update_layout(
        title="Company Website Embedding Progress",
        annotations=[dict(text=f'Total: {total_companies}', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display additional information
    st.info(f"""
    - Total companies: {total_companies}
    - Websites embedded: {round(websites_embedded, 2)}%
    - Websites to embed: {websites_to_embed}%
""")

    # Step 7: Financial Data Scraping
    st.markdown("### 📊 Step 7: Financial Data Scraping")

    with st.expander("View Documentation", expanded=False):
        st.markdown("""
        The final step involved collecting financial data to assess the economic standing of these companies:

        1. Identifying reliable sources of financial data for Belgian companies.
        2. Scraping key financial metrics such as:
           - Annual revenue
           - Profit margins
           - Growth rates
           - Employee count over time
        3. Compiling and standardizing the financial data for comparative analysis.

        This financial information provides context on the economic health and scale of companies employing .NET developers in Flanders, allowing for more comprehensive market analysis.
        """)

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
