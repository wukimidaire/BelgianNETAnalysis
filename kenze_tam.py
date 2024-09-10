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


# Set page config as the first Streamlit command, outside of any function
st.set_page_config(layout="wide", page_title="Belgian .NET Organizations Analysis")

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

# Streamlit app
def main():
    try:
        conn = connect_to_db()
        st.success("Successfully connected to the database!")
    except Exception as e:
        st.error(f"Failed to connect to the database: {str(e)}")
        return  # Exit the function if connection fails

    st.title("Belgian Organizations Employing .NET Developers")
    # Custom CSS to style the container
    st.markdown("""
    <style>
        .stContainer {
            background-color: #f21f46f67;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create a container for the entire section
    with st.container():
        # Project Overview
        st.markdown("""
        <div style='background-color: #f21f46f67; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2>🔍 Project Overview</h2>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### Objective
            Maps the Belgian .NET ecosystem, offering data-driven insights to guide strategic decisions.
            The project uses LinkedIn to identify companies with .NET developers and aggregates data from various sources.
            The data is analyzed to reveal .NET developer distribution, company profiles, hiring trends, and department structures.
            """)
            
            st.markdown("""
            ### Key Insights
            
            1. **Company Identification**: 1094 unique companies employing .NET developers identified in Flanders.
            2. **Developer Distribution**: Analysis of .NET developer concentration across companies and industries.
            3. **Company Profiles**: Comprehensive profiles including size, industry, location, and financial standing.
            4. **Market Trends**: Insights into hiring patterns, technology adoption, and growth areas in .NET development.
            """)
            
            st.markdown("""
            ### Business Impact
            
            - 🎯 Targeted market analysis for .NET-related products or services
            - 🤝 Identification of potential clients or partners in the Belgian tech ecosystem
            - 🏆 Understanding of the competitive landscape in .NET development
            """)

        with col2:
            st.markdown("""
            ### Methodology
            
            1. **Data Collection**: 
                - LinkedIn profile searches for .NET developers
                - Company data from LinkedIn Company Pages
                - Employee profiles from identified companies
                - Google My Business (GMB) profiles
                - Company website content
                - Financial data from reliable sources

            2. **Data Processing**:
                - Cleaning and categorization of collected data
                - Identification of .NET skills
                - Classification of employee seniority and departments
                - Tenure calculation

            3. **Data Transformation**: 
                - Aggregation and transformation using dbt (data build tool)
                - Integration of data from multiple sources
                - Implementation of business logic and calculations
            
            4. **Data Activation**:
                - t.b.c.
            """)

        st.markdown("""
            Project Assumptions
            
            This project is based on the following assumptions:
            1. LinkedIn is the most accurate & up-to-date source for company and employee data.
            2. Every .NET developer mentions this on their profile.
            3. Every LinkedIn profile has an associated LinkedIn company identification.
            
            """)

    # Add this at the end of your script
    st.markdown("""
    <style>
        .stMarkdown {
            background-color: #f21f46f67;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)


    # Step 1: Search .NET Profiles
    st.subheader("📊 Step 1: Search .NET Profiles")

    st.info("""
        Starting with a LinkedIn search, profiles are collected using various keywords such as ".NET" or "dotNET." 
        
        However, LinkedIn's search results are not always fully accurate when specific filters are applied. 
        
        The profiles are screened for .NET-related skills and experience, identifying unique companies where employees with .NET skills are employed.
        
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
    st.subheader("📊 Step 2: Company List Creation")

    st.info("""
        After identifying .NET developers from LinkedIn profiles, a list of unique companies that employ developers is compiled. This step involves:

        1. Extracting LinkedIn company identificition (company_id's) from the .NET developers' profiles.
        2. Removing duplicates to create a list of unique companies.
        3. Validating the company information to ensure accuracy.

        This list serves as the foundation for downstream analysis, providing a targeted set of companies known to employ .NET developers in Belgium.
        """)

    # Step 3: Company Data Collection
    st.subheader("📊 Step 3: Company Data Collection")

    st.info("""
        Using a list of companies identified in Step 2, comprehensive data from LinkedIn Company Pages is collected. This process involves:

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
        allowing for more in-depth analysis and insights about the organizations employing .NET developers in Belgium.
        
        Note: Companies associated with .NET developer profiles that have an empty company_id are excluded from the final dataset. 
        
        The impact on completeness is expected to be minimal.
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
    st.subheader("📊 Step 4: Employee Profile Scraping, Data Processing & Labeling")

    st.info("""
        In this step, the data collection process is expanded to include profiles of all employees from the companies identified in Step 2, followed by comprehensive data processing.
        
        This process involves:

        #### 1. Data Collection

        - Systematically scraped public LinkedIn profiles of employees from each company
        - Gathered key data points: job titles, skills, experience, and other relevant information
        - Ensured data privacy compliance by only collecting publicly available information

        ##### Involved Challenges:

        - Varying data availability on LinkedIn profiles
        - LinkedIn API restrictions limiting access to bulk data
        - Need for IP rotation using proxy servers to avoid detection and blocking
        - Careful management of request frequency to avoid temporary bans
        - Development of CAPTCHA handling strategies
        - Ensuring compliance with LinkedIn's terms of service and data protection regulations
        - Dealing with variations in profile structures and incomplete information

        #### 2. Data Cleaning and Categorization
        
        ##### a. .NET Skills Identification:
        - Analyzed profile content to identify employees with .NET-related skills or experience
        - Utilized keyword matching and natural language processing techniques to detect .NET expertise
        - Considered factors such as listed skills, job titles, and project descriptions

        ##### b. Seniority Classification:
        - **Advisor**: Board members, shareholders, chairmen, investors
        - **Executive**: C-level positions, founders, partners, business owners
        - **Senior**: Team leads, heads of departments, senior positions, directors
        - **Specialist**: Default category for roles not matching above criteria    

        ##### c. Tenure Calculation:
        - Converted text-based duration into numeric values (total months within company)

        ##### d. Department Classification:
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
    st.subheader("📊 Step 5: Google My Business (GMB) Profile Scraping")

    st.info("""
        To enhance the accuracy and completeness of company data, this step involves collecting Google My Business (GMB) profiles.  
        
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
    st.subheader("📊 Step 6: Company Website Scraping")

    st.info("""
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
        
        
        
        This JSON structure represents comprehensive data about a website, including business information, job openings, and customer profiles.

        #### Main Components:

        1. **Basic Website Info**: URL, title, description, and keywords.
        2. **Business Details**: Type (B2B, B2C, B2G) and hiring status.
        3. **Career Information**: Job openings and career page URLs.
        4. **Contact Information**: Email and phone number.
        5. **Case Studies**: Customer success stories with challenges and solutions.
        6. **Ideal Customer Profile**: Description and characteristics of target customers.
        7. **Open Positions**: Detailed job listings with requirements and tools.
        8. **About Section**: Company mission overview.
        9. **Pricing and Trial Info**: Availability of pricing details and trial offers.
        10. **Meta Tags**: Additional metadata like author information.
        11. **Content Summary**: Main headings and their corresponding URLs.
        12. **Social Media**: Links to various social media profiles.

        
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
    st.subheader("📊 Step 7: Financial Data Scraping")

    st.info("""
        This step involves collecting unstructured financial data into structured data to assess the economic standing of these companies:

        1. Identifying reliable sources of financial data for Belgian companies such as the Belgian Business Register.
        2. Scraping key financial metrics such as:
           - Annual revenue
           - Profit margins
           - Growth rates
           - Employee count over time
        3. Compiling and standardizing the financial data for comparative analysis.

        This financial information provides context on the economic health and scale of companies employing .NET developers in Flanders, allowing for more comprehensive market analysis.
        """)

    # Execute the query for Step 7
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
            vat_scrape_timestamp,
            website, 
            hq_line1, 
            hq_postalcode, 
            company_name, 
            embed_website_timestamp
        FROM
            cli
    ),
    financial_search AS ( 
        SELECT 
            company_id, 
            year, 
            ROUND(equity, 0) AS equity, 
            employees AS fte_employees, 
            ROUND(profit_loss, 0) AS profit_loss, 
            ROUND(gross_margin, 0) AS gross_margin,
            update_timestamp
        FROM (
            SELECT 
                company_id, 
                year, 
                equity, 
                employees, 
                profit_loss, 
                gross_margin,
                update_timestamp,
                ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) AS rn
            FROM 
                financial_data
        ) AS subquery
        WHERE rn = 1
    )

    SELECT
        count(a.companyid) AS total_companies,
        ROUND(COUNT(CASE WHEN b.vat_scrape_timestamp IS NOT NULL THEN 1 END) * 100.0 / count(a.companyid), 2) AS pct_financial_data_enrichment
    FROM
        kenze_profile_search AS a
    FULL JOIN cli_search AS b
        ON a.companyid = b.company_id::VARCHAR
    LEFT JOIN financial_search AS d
        ON a.companyid = d.company_id::VARCHAR
    WHERE
        a.companyid IS NOT NULL;
    """)

    result = cur.fetchone()
    total_companies, pct_financial_data_enrichment = result

    # Calculate the percentage of companies without financial data
    pct_no_financial_data = 100 - pct_financial_data_enrichment

    # Create a pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Financial Data Available', 'No Financial Data Available'],
        values=[pct_financial_data_enrichment, pct_no_financial_data],
        hole=.3,
        marker_colors=['#66b3ff', '#ff9999']
    )])

    fig.update_layout(
        title="Financial Data Enrichment Progress",
        annotations=[dict(text=f'Total: {total_companies}', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display additional information
    st.info(f"""
    - Total companies: {total_companies}
    - Companies with financial data: {round(pct_financial_data_enrichment, 2)}%
    - Companies without financial data: {round(pct_no_financial_data, 2)}%
    """)





    # Step 8: Data Aggregation and Transformation with dbt
    st.subheader("📊 Step 8: Data Aggregation and Transformation with dbt")

    with st.expander("View Documentation", expanded=False):
        st.info("""
        In this crucial final step, using dbt (data build tool) to aggregate and transform data from multiple sources into a unified, analysis-ready dataset. 
        
        This process is essential for several reasons:

        1. **Data Integration**: 
           - Combines information from various sources (LinkedIn profiles, company data, GMB profiles, financial data, etc.)
           - Creates a single source of truth for all company-related information

        2. **Data Quality and Consistency**:
           - Applies consistent transform           - Ensures data integrity and reduces inconsistencies

        3. **Scalability and Maintainability**:
           - dbt's modular approach allows for easy updates and additions to the data pipeline
           - Version control integration enables tracking changes and collaborating on data transformations

        4. **Performance Optimization**:
           - Pre-aggregates data to improve query performance for end-user analytics
           - Enables efficient data access for the Streamlit dashboard

        5. **Business Logic Implementation**:
           - Centralizes complex calculations and derivations (e.g., .NET developer ratios, company size categories)
           - Ensures consistent application of business rules across all analyses

        ### Why dbt for Data Transformation?

        Selecting dbt is compelling for several reasons:

        1. **SQL-Based Transformations**: 
           - Leverages SQL, a widely known language, making it accessible to data analysts and engineers
           - Allows for complex transformations without the need for a separate programming environment

        2. **Modular and Reusable Code**:
           - Encourages creation of modular, reusable SQL models
           - Simplifies maintenance and promotes code reuse across projects

        3. **Version Control and Collaboration**:
           - Integrates seamlessly with Git for version control
           - Facilitates collaboration among team members on data transformations

        4. **Testing and Documentation**:
           - Built-in testing framework ensures data quality and integrity
           - Automated documentation generation keeps data dictionaries up-to-date

        5. **Scheduling and Orchestration**:
           - Easy integration with scheduling tools for automated runs
           - Supports complex DAGs (Directed Acyclic Graphs) for managing dependencies between models

        ### How Everything Comes Together

        1. **Data Ingestion**: 
           - Raw data from various sources is loaded into our data warehouse

        2. **Staging Models**:
           - dbt creates staging models that clean and standardize raw data from each source

        3. **Intermediate Models**:
           - More complex transformations are applied, joining data from different sources

        4. **Final Models**:
           - Aggregated views are created, incorporating all necessary business logic

        5. **Testing and Documentation**:
           - dbt runs tests to ensure data quality and generates documentation

        6. **Deployment**:
           - Transformed data is made available for the Streamlit dashboard and other analytics tools

        This approach ensures that our final dataset is comprehensive, consistent, and optimized for analysis, 
        providing a solid foundation for insights into the .NET development landscape in Belgium.
        """)

    # You can add a visual representation of the dbt process here if desired
    st.image("dbt_lineage.png", caption="dbt Lineage", width=900)
   
 

    # Connect to the database and fetch data
    conn = connect_to_db()
    cur = conn.cursor()

    # Fetch data from the table, including the new columns
    cur.execute("SELECT * FROM public_dbt.a_final_kenze_companies")
    data = cur.fetchall()

    # Convert data to a pandas DataFrame
    df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])


    # Create a geo map
    if 'latitude' in df.columns and 'longitude' in df.columns:
        # Convert latitude and longitude to float if they're not already
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        # Remove rows with null values in latitude or longitude
        df_map = df.dropna(subset=['latitude', 'longitude'])

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
            col1, col2 = st.columns([1, 2])  # Create two columns

            with col1:  # Left column for filters
                map_filters = st.expander("Map Filters", expanded=True)
                with map_filters:
                    map_industries = st.multiselect("Exclude LinkedIn Industry", df_belgium['industry'].unique())
                    map_categories = st.multiselect("Exclude Google My Business Category", df_belgium['category'].unique())
                    
                    # New text input for GMB address filter
                    gmb_address_filter_include = st.text_input("Include Filter GMB Address", "")
                    gmb_address_filter_exclude = st.text_input("Exclude Filter GMB Address", "")
                    
                    # New text input for description exclusion filter
                    description_filter_exclude = st.text_area("Exclude Filter Description (comma-separated)", "")
                     # Split the input into a list of keywords, removing any extra spaces
                    exclude_keywords = [keyword.strip() for keyword in description_filter_exclude.split(',') if keyword.strip()]
                    
                    
                    # New text area for open positions filter
                    open_positions_filter = st.text_area("Filter Open Positions (comma-separated)", "")
                    # Split the input into a list of keywords, removing any extra spaces
                    open_positions_keywords = [keyword.strip() for keyword in open_positions_filter.split(',') if keyword.strip()]
                    
                    # New text area for excluding keywords in open positions
                    open_positions_exclude_filter = st.text_area("Exclude Filter Open Positions (comma-separated)", "")
                    # Split the input into a list of keywords, removing any extra spaces
                    open_positions_exclude_keywords = [keyword.strip() for keyword in open_positions_exclude_filter.split(',') if keyword.strip()]
                    
                    # New slider for employee count
                    employee_count_range = st.slider("Select Employee Count Range", 0, int(df_belgium['employee_count'].max()), (0, int(df_belgium['employee_count'].max())), 1)
                    
                    if 'net_dev_count' in df_belgium.columns:
                        min_net_devs = st.number_input("Minimum .NET Developers", min_value=0, value=0, key="map_min_net_devs")
                    
                    # New slider filters for ratios
                    net_profile_ratio_range = st.slider("Select .NET Profile vs Total Ratio Range", 0.0, 100.0, (0.0, 100.0), 0.1)
                    it_executive_ratio_range = st.slider("Select IT Executive vs IT Specialist Ratio Range", 0.0, 100.0, (0.0, 100.0), 0.1)
                    it_team_percentage_range = st.slider("Select IT Team Percentage Range",    0.0, 100.0, (0.0, 100.0), 0.1)

            with col2:  # Right column for the map
                filtered_map_df = df_belgium[
                    (~df_belgium['industry'].isin(map_industries) if map_industries else True) &
                    (~df_belgium['category'].isin(map_categories) if map_categories else True) &
                    (df_belgium['gmb_address'].str.lower().str.contains(gmb_address_filter_include.lower()) if gmb_address_filter_include else True) &  # Filter by GMB address
                    (df_belgium['gmb_address'].str.lower().str.contains(gmb_address_filter_exclude.lower()) == False if gmb_address_filter_exclude else True) &  # Exclude by GMB address
                    (~df_belgium['description'].str.lower().str.contains('|'.join(exclude_keywords)) if exclude_keywords else True) &  # Exclude by description
                    (df_belgium['wc_open_positions'].str.lower().str.contains('|'.join(open_positions_keywords)) if open_positions_keywords else True) &  # Filter by open positions
                    (~df_belgium['wc_open_positions'].str.lower().str.contains('|'.join(open_positions_exclude_keywords)) if open_positions_exclude_keywords else True) &  # Exclude by open positions
                    (df_belgium['employee_count'] >= employee_count_range[0]) &
                    (df_belgium['employee_count'] <= employee_count_range[1]) &
                    (df_belgium['net_dev_count'] >= min_net_devs if 'net_dev_count' in df_belgium.columns else True) &
                    (df_belgium['net_profile_vs_total_ratio'] >= net_profile_ratio_range[0]) &
                    (df_belgium['net_profile_vs_total_ratio'] <= net_profile_ratio_range[1]) &
                    (df_belgium['it_executive_vs_it_specialist_ratio'] >= it_executive_ratio_range[0]) &
                    (df_belgium['it_executive_vs_it_specialist_ratio'] <= it_executive_ratio_range[1]) &
                    (df_belgium['it_team_percentage'] >= it_team_percentage_range[0]) &  # Filter by IT Team Percentage
                    (df_belgium['it_team_percentage'] <= it_team_percentage_range[1]) 
    
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

            # Move the filtered data display outside the columns
            st.subheader("Filtered Company Data")
            if not filtered_map_df.empty:
                columns_to_display = ['company_name', 'industry', 'employee_count', 'total', 'it_engineering', 'net_profile', 'net_profile_vs_total_ratio', 'it_team_percentage', 'it_executive_vs_it_specialist_ratio', 'specialist_vs_total_ratio', 'net_profile_vs_it_engineering_ratio', 'technical_executive', 'operations', 'customer_success', 'finance', 'sales', 'marketing', 'human_resources', 'specialist', 'senior', 'executive', 'advisor', 'cli_url', 'founded', 'hq_city', 'tagline', 'cli_website', 'vat_number', 'cover_image', 'description', 'followercount', 'universal_name', 'logo_resulution', 'employee_count_range', 'equity', 'fte_employees', 'profit_loss', 'gross_margin', 'cid', 'gmb_title', 'rating', 'gmb_address', 'category', 'phone_number', 'rating_count', 'wc_description', 'wc_business_type', 'wc_hiring', 'wc_about_section', 'wc_pricing_mentioned', 'wc_trial_available', 'wc_keywords', 'wc_career_urls', 'wc_social_media', 'wc_open_positions', 'wc_ideal_customer_profile', 'wc_case_studies', 'wc_contact_info', 'kar_company_id'] 
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
                            label="Download company data as CSV",
                            data=csv,
                            file_name="company_data.csv",
                            mime="text/csv",
                            disabled=True
                        )
                    with col2:
                        st.info("The download CSV button will be enabled in the final delivery.")

                    # Extract kar_company_id values after the download section
                    kar_company_ids = filtered_map_df['kar_company_id'].dropna().unique().tolist()

                    # Execute the query using the list of kar_company_ids
                    kar_company_ids_str = "', '".join(kar_company_ids)  # Format: 'id1', 'id2', ...
                    query = f"""
                    SELECT * 
                    FROM kenze_pli_profiles 
                    WHERE companyid IN ('{kar_company_ids_str}');
                    """
                    
                    # Connect to the database and fetch data
                    conn = connect_to_db()
                    cur = conn.cursor()
                    cur.execute(query)
                    result_table = cur.fetchall()

                    # Convert the result to a pandas DataFrame
                    result_df = pd.DataFrame(result_table, columns=[desc[0] for desc in cur.description])
                    
                     # Limit the columns to the specified ones
                    columns_to_keep = [
                       'name', 'title', 'summary', 'lastname', 'location', 
                       'firstname', 'ispremium', 'seniority', 'department', 
                       'isopenlink', 'companyname', 'titledescription', 
                       'months_in_company', 'net_profile'
                    ]
                    result_df = result_df[columns_to_keep]

                    # Display the resulting DataFrame with filters
                    st.subheader("Filtered Profile Data")  # Updated title

                    # Create two columns for filters and information
                    col1, col2 = st.columns(2)

                    with col1:  # Left column for filters
                        # Filter by seniority
                        seniority_filter = st.selectbox("Select Seniority", options=["All"] + result_df['seniority'].unique().tolist())
                        if seniority_filter != "All":
                            result_df = result_df[result_df['seniority'] == seniority_filter]

                        # Filter by department
                        department_filter = st.selectbox("Select Department", options=["All"] + result_df['department'].unique().tolist())
                        if department_filter != "All":
                            result_df = result_df[result_df['department'] == department_filter]

                        # Filter by months in company
                        months_in_company_filter = st.slider("Select Months in Company", min_value=int(result_df['months_in_company'].min()), 
                                                              max_value=int(result_df['months_in_company'].max()), 
                                                              value=(int(result_df['months_in_company'].min()), int(result_df['months_in_company'].max())))
                        result_df = result_df[(result_df['months_in_company'] >= months_in_company_filter[0]) & 
                                              (result_df['months_in_company'] <= months_in_company_filter[1])]

                        # Filter by net profile
                        net_profile_filter = st.selectbox("Select Net Profile", options=["All", True, False])
                        if net_profile_filter != "All":
                            result_df = result_df[result_df['net_profile'] == net_profile_filter]

                    with col2:  # Right column for information
                        # Display the total count of profiles in an info box
                        total_count = len(result_df)
                        st.info("sdkflsmjdflmsdkfjlsdkf ")

                    # Display the filtered DataFrame (limit to top 10)
                    st.dataframe(result_df.head(10))

                    # Empty information section with placeholder text
                    st.info(f"Total results: {total_count}. Showing top 10 profiles, all profiles will be enabled in final delivery.")
                    
                    # New download section with info
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="Download profile data as CSV",
                            data=csv,
                            file_name="company_data.csv",
                            mime="text/csv",
                            disabled=True  # Set to True for now, can be enabled later
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

   
if __name__ == "__main__":
    main()

