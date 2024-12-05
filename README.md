# The Belgian .NET Ecosystem Analysis

## Overview

This data mining project aims to map the Belgian .NET ecosystem, offering data-driven insights to guide strategic decisions. The analysis identifies companies in Belgium employing .NET developers, aggregates data from various sources, and reveals insights into developer distribution, company profiles, hiring trends, and department structures.

## Objectives

- **Company Identification**: Identify unique companies employing .NET developers in Belgium.
- **Developer Distribution**: Analyze the concentration of .NET developers across companies and industries.
- **Company Profiles**: Compile comprehensive profiles, including size, industry, location, and financial standing.
- **Market Trends**: Provide insights into hiring patterns, technology adoption, and growth areas in .NET development.

## Technologies Used

### Backend

- **PostgreSQL**: Database hosted on Google Cloud Platform (GCP) for storing and managing collected data.
- **n8n Workflow Automation**: Automates data scraping, processing, and loading workflows.

### Frontend

- **Streamlit**: Used to create an interactive data science application for visualizing data and progress overviews.
- **Python Libraries**:
  - Data Manipulation: `pandas`, `numpy`
  - Data Visualization: `seaborn`, `matplotlib`, `plotly`, `folium`
  - Database Connectivity: `psycopg2`
  - Web Integration: `streamlit-folium`

### Data Transformation

- **dbt (Data Build Tool)**: For data aggregation and transformation, integrating data from multiple sources into a unified, analysis-ready dataset.

## Data Collection and Processing Steps

### Step 1: Search .NET Profiles

- **Data Source**: LinkedIn profiles are collected using keywords like ".NET" and "dotNET".
- **Process**:
  - Scrape LinkedIn profiles mentioning .NET skills.
  - Identify unique companies where these developers are employed.
- **Challenges**:
  - Inaccuracies in LinkedIn search results when specific filters are applied.
  - Some profiles may not include employer details, limiting company-level analysis.

### Step 2: Company List Creation

- **Process**:
  - Extract LinkedIn company IDs from .NET developers' profiles.
  - Remove duplicates to create a unique list of companies.
  - Validate company information for accuracy.
- **Outcome**: A targeted set of companies known to employ .NET developers in Belgium.

### Step 3: Company Data Collection

- **Data Source**: LinkedIn Company Pages.
- **Process**:
  - Scrape public information from each company's page.
  - Collect data points such as company size, industry, location, founded year, specialties, website URL, and company description.
- **Challenges**:
  - Companies without LinkedIn company IDs are excluded, but impact on completeness is minimal.

### Step 4: Employee Profile Scraping and Data Processing

- **Data Source**: Public LinkedIn profiles of employees from identified companies.
- **Process**:
  - Scrape employee profiles, gathering job titles, skills, experience, etc.
  - **Data Cleaning and Categorization**:
    - **.NET Skills Identification**: Detect .NET expertise using keyword matching and NLP techniques.
    - **Seniority Classification**:
      - **Advisor**: Board members, shareholders.
      - **Executive**: C-level positions, founders.
      - **Senior**: Team leads, department heads.
      - **Specialist**: Default category for others.
    - **Department Classification**: Marketing, Sales, IT/Engineering, etc.
    - **Tenure Calculation**: Convert duration texts into numeric months.
- **Challenges**:
  - Varying data availability on profiles.
  - LinkedIn API restrictions and need for proxy servers.

### Step 5: Google My Business (GMB) Profile Scraping

- **Data Source**: Google My Business.
- **Process**:
  - Automate searches for each company on GMB.
  - Extract activity descriptions, addresses, contact details, customer reviews, etc.
- **Benefits**:
  - Improved data accuracy by cross-referencing multiple sources.
  - Enhanced company profiles with detailed and up-to-date information.
- **Challenges**:
  - Handling rate limiting and ensuring efficient data collection.
  - Resolving conflicts between different data sources.

### Step 6: Company Website Scraping

- **Data Source**: Company websites, focusing on job pages.
- **Process**:
  - Develop tailored web scrapers for different website structures.
  - Extract insights on:
    - Business type and industry focus.
    - Products or services offered.
    - Current hiring needs and technical stacks.
    - Company culture and values.
- **Benefits**:
  - Provides insights into companies' growth trajectories and technical preferences.
- **Challenges**:
  - Varying website structures and data availability.
  - Dealing with incomplete or inconsistent data.

### Step 7: Financial Data Scraping

- **Data Source**: Financial records from reliable sources (e.g., Belgian Business Register).
- **Process**:
  - Collect key financial metrics: annual revenue, profit margins, growth rates, employee count over time.
  - Compile and standardize data for comparative analysis.
- **Benefits**:
  - Assess economic standing of companies employing .NET developers.
- **Challenges**:
  - Ensuring data accuracy and resolving discrepancies.

### Step 8: Data Aggregation and Transformation with dbt

- **Process**:
  - Use dbt to integrate and transform data from multiple sources.
  - Create a unified, analysis-ready dataset.
- **Benefits**:
  - **Data Integration**: Combines information into a single source of truth.
  - **Data Quality**: Applies consistent transformations to ensure data integrity.
  - **Performance Optimization**: Pre-aggregates data for improved query performance.

![DBT Lineage](https://github.com/wukimidaire/data_mining_project/blob/development/dbt_lineage.png)

## Streamlit Application

An interactive dashboard built with Streamlit to visualize data and track progress through each step.

### Features

- **Interactive Maps**: Visualize the geographical distribution of companies using Folium.
- **Charts and Graphs**: Display statistics and trends with Plotly and Seaborn.
- **Data Filters**: Apply various filters to explore specific data segments.
- **Progress Tracking**: Overviews of data collection and processing progress.

### How to Run the Application

1. **Clone the Repository**

   ```bash
   git clone https://github.com/wukimidaire/data_mining_streamlit_app.git
   ```

2. **Install Dependencies**

   Ensure you have Python 3.7 or higher installed.

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Database Credentials**

   Create a `.streamlit/secrets.toml` file with your database credentials:

   ```toml
   [DB]
   DB_NAME = "your_database_name"
   DB_USER = "your_username"
   DB_PASSWORD = "your_password"
   DB_HOST = "your_host"
   DB_PORT = "your_port"
   ```

   Alternatively, you can set environment variables or use a `.env` file.

4. **Run the Application**

   ```bash
   streamlit run app.py
   ```

## Database Setup

- **PostgreSQL Database**: Hosted on Google Cloud Platform.
- **Access**: Ensure your IP is whitelisted and you have the correct credentials in `secrets.toml`.

## Workflow Automation with n8n

- **Data Collection**: Automated scraping of profiles, company data, GMB profiles, financial data, etc.
- **Data Processing**: Cleaning, categorization, and transformation of collected data.
- **Data Loading**: Automated loading of processed data into the PostgreSQL database.

## Project Structure


├── app.py # Main Streamlit application

├── requirements.txt # Python dependencies

├── .gitignore # Git ignore file

├── README.md # Project documentation (this file)

└── .streamlit/

└── secrets.toml # Database credentials (not included in version control)




## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**
2. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
4. **Commit Your Changes**

   ```bash
   git commit -m "Add your commit message"
   ```

5. **Push to the Branch**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or support, please contact:

- **Victor De Coster**
- **LinkedIn**: [Victor De Coster](https://www.linkedin.com/in/victordecoster)

---

*Note: The `.streamlit/secrets.toml` file is included in the `.gitignore` to prevent sensitive information from being uploaded to version control.*
