import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from io import BytesIO
import base64
import gspread
from google.oauth2 import service_account
import tempfile
import os
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import html
import re

# Set page configuration
st.set_page_config(
    page_title="War Desk",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced modern dark mode UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1 {
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 1rem !important;
        color: #f0f6fc !important;
    }
    
    h2, h3, h4 {
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        color: #f0f6fc !important;
    }
    
    .stSelectbox, .stMultiselect {
        background-color: transparent;
        color: white;
        border-radius: 5px;
    }
    
    .stSelectbox > div > div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
    }
    
    .stSelectbox > div > div > div {
        color: #f0f6fc !important;
    }
    
    .css-1d391kg, div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }
    
    .floating-filters {
        background-color: rgba(22, 27, 34, 0.9);
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(8px);
        width: 100%;
        border: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .dialog-box {
        background-color: rgba(22, 27, 34, 0.95);
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1.5rem;
        border: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .doc-content {
        background-color: rgba(22, 27, 34, 0.95);
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1.5rem;
        border: 1px solid #30363d;
        max-height: 800px;
        overflow-y: auto;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .doc-content img {
        max-width: 100%;
        height: auto;
        border-radius: 4px;
    }
    
    .doc-content * {
        color: #f0f6fc !important;
        background-color: transparent !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .doc-content p, .doc-content span, .doc-content div {
        font-size: 14px !important;
        line-height: 1.8 !important;
    }
    
    .doc-content h1, .doc-content h2, .doc-content h3, .doc-content h4 {
        color: #f0f6fc !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    .doc-content a {
        color: #58a6ff !important;
        text-decoration: none !important;
        border-bottom: 1px solid rgba(88, 166, 255, 0.3) !important;
        transition: border-color 0.2s ease;
    }
    
    .doc-content a:hover {
        border-bottom: 1px solid rgba(88, 166, 255, 0.8) !important;
    }
    
    /* Label styling */
    div.stSelectbox label, div.stMultiselect label {
        color: #8b949e !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    /* Card styling for profile */
    .profile-card {
        background-color: rgba(22, 27, 34, 0.95);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #30363d;
        height: 100%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Legend styling */
    .map-legend {
        background-color: rgba(22, 27, 34, 0.9);
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border: 1px solid #30363d;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    /* About section styling */
    .about-section {
        background-color: rgba(22, 27, 34, 0.95);
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 2rem;
        border: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Footer styling */
    .footer {
        padding: 1.5rem 0;
        text-align: center;
        color: #8b949e;
        font-size: 0.875rem;
        border-top: 1px solid #30363d;
        margin-top: 2rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 0.375rem 1rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        transition: background-color 0.2s ease !important;
    }
    
    .stButton button:hover {
        background-color: #2ea043 !important;
    }
    
    /* Tooltip styling */
    div[data-testid="stTooltipIcon"] {
        color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

# Title with more modern styling
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
    <h1 style="margin: 0;">War Desk</h1>
    <div style="background-color: #238636; color: white; font-size: 0.75rem; font-weight: 600; padding: 0.25rem 0.5rem; border-radius: 1rem; margin-left: 1rem;">BETA</div>
</div>
<p style="font-size: 1.1rem; color: #8b949e; margin-top: -0.5rem; margin-bottom: 2rem;">Mapping Armed Actors in Myanmar's Spring Revolution</p>
""", unsafe_allow_html=True)

# Cache the drive service creation
@st.cache_resource
def get_drive_service():
    try:
        # Create credentials from service account file
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["google_credentials"],
            scopes=['https://www.googleapis.com/auth/spreadsheets', 
                   'https://www.googleapis.com/auth/drive', 
                   'https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Create Drive API client
        drive_service = build('drive', 'v3', credentials=credentials)
        return drive_service
    except Exception as e:
        st.error(f"Error creating Drive service: {e}")
        return None

# Function to get Google Doc content
def get_google_doc_content(drive_service, folder_id, acronym):
    if not acronym or acronym == 'All':
        return None
    
    try:
        # Search for files with the acronym as the name in the specified folder
        query = f"'{folder_id}' in parents and name contains '{acronym}' and mimeType='application/vnd.google-apps.document'"
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            return None
        
        # Get the first matching document
        doc_id = files[0]['id']
        
        # Export the document as HTML
        request = drive_service.files().export_media(fileId=doc_id, mimeType='text/html')
        content = request.execute()
        
        # Return the HTML content
        return content.decode('utf-8')
    
    except Exception as e:
        st.error(f"Error retrieving Google Doc: {e}")
        return None

# Function to load data
@st.cache_data
def load_data():
    # Load CSV data
    actors_df = pd.read_csv("cleaned_myanmar_actors.csv")
    
    # Filter to only include events with "Battles"
    actors_df = actors_df[actors_df['event_type'] == "Battles"]
    actors_df = actors_df[actors_df['side'] == "Pro-Democracy"]
    
    # Get Drive service
    drive_service = get_drive_service()
    
    if drive_service:
        try:
            # File ID from the URL
            file_id = '1ucEOV4c1ayKizMtV0Z5k7j-sKcnNniMs'
            
            # Create a temporary file to store the downloaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                temp_path = temp_file.name
            
            # Download the file to the temporary location
            request = drive_service.files().get_media(fileId=file_id)
            with open(temp_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            # Read the Excel file
            profiles_df = pd.read_excel(temp_path, sheet_name="Profile")
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
        except Exception as e:
            st.error(f"Error loading data from Google Drive: {e}")
            st.info("Attempting to load from direct URL...")
            
            # Alternative: try to download directly from the public URL
            try:
                url = "https://docs.google.com/spreadsheets/d/1ucEOV4c1ayKizMtV0Z5k7j-sKcnNniMs/export?format=xlsx"
                profiles_df = pd.read_excel(url, sheet_name="Profile")
            except Exception as e2:
                st.error(f"Error loading from direct URL: {e2}")
                profiles_df = pd.DataFrame(columns=["Armed Group Name"])
    else:
        st.warning("Unable to create Drive service. Using empty profile data.")
        profiles_df = pd.DataFrame(columns=["Armed Group Name"])
    
    return actors_df, profiles_df

# Load data
actors_df, profiles_df = load_data()

# Ensure we have valid coordinates
actors_df = actors_df.dropna(subset=['latitude', 'longitude'])
actors_df = actors_df[(actors_df['latitude'] != 0) & (actors_df['longitude'] != 0)]

# Create combined actor options for the new filter
# First, create a mapping from acronyms to full names
acronym_to_name = {}
for _, row in actors_df.iterrows():
    if pd.notna(row['acronym']) and row['acronym'].strip() != "":
        acronym_to_name[row['acronym']] = row['name']

# Now create combined options
combined_actor_options = ['All']
for _, row in actors_df.iterrows():
    if pd.notna(row['acronym']) and row['acronym'].strip() != "":
        # Format: "Acronym - Full Name"
        combined_option = f"{row['acronym']} - {row['name']}"
        if combined_option not in combined_actor_options:
            combined_actor_options.append(combined_option)
    else:
        # Just use the full name if no acronym
        if row['name'] not in combined_actor_options:
            combined_actor_options.append(row['name'])

# Sort options alphabetically (after 'All')
combined_actor_options[1:] = sorted(combined_actor_options[1:])

# State management for filters
if 'selected_region' not in st.session_state:
    st.session_state.selected_region = 'All'
if 'selected_combined_actor' not in st.session_state:
    st.session_state.selected_combined_actor = 'All'

# Filter callback functions
def on_region_change():
    # Update the selected region in session state
    region_val = st.session_state.region_selector
    st.session_state.selected_region = region_val
    
    # Reset actor when region changes
    st.session_state.selected_combined_actor = 'All'

def on_combined_actor_change():
    # Update the selected combined actor in session state
    st.session_state.selected_combined_actor = st.session_state.combined_actor_selector

# Function to filter actors based on the combined selection
def filter_by_combined_actor(df, combined_actor):
    if combined_actor == 'All':
        return df
    
    if " - " in combined_actor:
        # Split the combined value to get acronym and name
        acronym, _ = combined_actor.split(" - ", 1)
        return df[df['acronym'] == acronym]
    else:
        # If no acronym in the option, just match by name
        return df[df['name'] == combined_actor]

# Get unique regions
regions = ['All'] + sorted(actors_df['admin1'].dropna().unique().tolist())

# Create a container with a nicer design for the filters
with st.container():
    # st.markdown('<div style="background-color: rgba(22, 27, 34, 0.95); padding: 1.5rem; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">', unsafe_allow_html=True)
    
    st.markdown("### Filters")
    
    # Create two columns for filters
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Region filter (admin1)
        if st.session_state.selected_region in regions:
            index = regions.index(st.session_state.selected_region)
        else:
            index = 0
            st.session_state.selected_region = regions[0]
        
        selected_region = st.selectbox(
            "Region", 
            regions,
            index=index,
            key="region_selector",
            on_change=on_region_change,
            help="Filter by administrative region"
        )
        # Update session state after widget is created
        st.session_state.selected_region = selected_region
    
    with filter_col2:
        # Combined actor filter (acronym + name)
        if 'selected_combined_actor' not in st.session_state or st.session_state.selected_combined_actor not in combined_actor_options:
            st.session_state.selected_combined_actor = 'All'
        
        index = combined_actor_options.index(st.session_state.selected_combined_actor)
        
        selected_combined_actor = st.selectbox(
            "Armed Actor", 
            combined_actor_options,
            index=index,
            key="combined_actor_selector",
            on_change=on_combined_actor_change,
            help="Filter by armed group name or acronym"
        )
        # Update session state after widget is created
        st.session_state.selected_combined_actor = selected_combined_actor
    
    st.markdown('</div>', unsafe_allow_html=True)

# Filter data based on selections
filtered_df = actors_df.copy()

if selected_region != 'All':
    filtered_df = filtered_df[filtered_df['admin1'] == selected_region]

if selected_combined_actor != 'All':
    filtered_df = filter_by_combined_actor(filtered_df, selected_combined_actor)

# Extract the acronym and actor name from the combined selection
selected_acronym = None
selected_actor = None

if selected_combined_actor != 'All':
    if " - " in selected_combined_actor:
        selected_acronym, selected_actor = selected_combined_actor.split(" - ", 1)
    else:
        selected_actor = selected_combined_actor
        # Try to find acronym from the name
        actor_info = actors_df[actors_df['name'] == selected_actor]
        if not actor_info.empty and pd.notna(actor_info.iloc[0]['acronym']):
            selected_acronym = actor_info.iloc[0]['acronym']

# Main layout with two columns for map and profile
col1, col2 = st.columns([3, 1])

# Determine which actor to display profile for
display_actor = selected_actor

with col2:
    # Display profile information in a card
    # st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top: 0;">Actor Profile</h3>', unsafe_allow_html=True)
    
    # Match with Excel data and display profile
    if display_actor:
        # Check if we need to extract acronym from name
        actor_parts = display_actor.split(': ', 1)
        if len(actor_parts) > 1 and actor_parts[0] in profiles_df['Armed Group Name'].values:
            profile_match = profiles_df[profiles_df['Armed Group Name'] == actor_parts[0]]
        else:
            # Try exact match
            profile_match = profiles_df[profiles_df['Armed Group Name'] == display_actor]
            
            # Try matching with acronym in name
            if profile_match.empty and ': ' in display_actor:
                actor_with_acronym = display_actor.split(': ', 1)[1]
                profile_match = profiles_df[profiles_df['Armed Group Name'].str.contains(actor_with_acronym, na=False)]
        
        if not profile_match.empty:
            profile_data = profile_match.iloc[0]
            
            # Show acronym if available
            if selected_acronym:
                st.markdown(f'<div style="background-color: #30363d; display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 500; margin-bottom: 0.75rem;">{selected_acronym}</div>', unsafe_allow_html=True)
            
            st.markdown(f"**Name:** {profile_data['Armed Group Name']}")
            
            # Display available profile information
            for col in profile_data.index:
                if col != 'Armed Group Name' and pd.notna(profile_data[col]) and profile_data[col] != "":
                    # Clean up column name for display
                    display_col = col.replace('_', ' ').strip()
                    if display_col == "":
                        display_col = "Location"
                    st.markdown(f"**{display_col}:** {profile_data[col]}")
        else:
            if selected_acronym:
                st.markdown(f'<div style="background-color: #30363d; display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 500; margin-bottom: 0.75rem;">{selected_acronym}</div>', unsafe_allow_html=True)
            st.markdown(f"**Name:** {display_actor}")
            st.info("No additional profile information found for this actor")
    else:
        st.info("Select an actor to view profile information")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col1:
    # If no data after filtering
    if filtered_df.empty:
        st.warning("No data available for the selected filters")
    else:
        # Create a map centered on Myanmar
        myanmar_center = [19.7633, 96.0785]  # Coordinates for center of Myanmar
        
        # Prepare data for PyDeck
        filtered_df['size'] = 100  # Size of the markers
        
        # Create color mapping based on side column
        side_colors = {
            'Pro-Democracy': [185, 49, 27],  # Red for Pro-Democracy
        }
        
        # Apply color mapping, default to gray if side not in mapping
        filtered_df['color'] = filtered_df['side'].apply(
            lambda x: side_colors.get(x, [150, 150, 150])
        )
        
        # Create scatter plot layer
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position=["longitude", "latitude"],
            get_color="color",
            get_radius="size",
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=1,
            radius_min_pixels=3,
            radius_max_pixels=12,
        )
        
        # Create the deck
        view_state = pdk.ViewState(
            latitude=myanmar_center[0],
            longitude=myanmar_center[1],
            zoom=4.5,
            pitch=0,
        )
        
        # Tooltip with enhanced styling
        tooltip = {
            "html": """
                <div style="background-color: rgba(22, 27, 34, 0.95); color: #f0f6fc; border-radius: 6px; padding: 12px; border: 1px solid #30363d; font-family: 'Inter', sans-serif; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">
                    <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px;">{name}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">{acronym}</div>
                    <div style="display: flex; margin-top: 8px;">
                        <div style="min-width: 80px; font-weight: 500; font-size: 12px;">Location:</div>
                        <div style="font-size: 12px;">{location}</div>
                    </div>
                    <div style="display: flex; margin-top: 4px;">
                        <div style="min-width: 80px; font-weight: 500; font-size: 12px;">Region:</div>
                        <div style="font-size: 12px;">{admin1}</div>
                    </div>
                    <div style="display: flex; margin-top: 4px;">
                        <div style="min-width: 80px; font-weight: 500; font-size: 12px;">Date:</div>
                        <div style="font-size: 12px;">{event_date}</div>
                    </div>
                    <div style="display: flex; margin-top: 4px;">
                        <div style="min-width: 80px; font-weight: 500; font-size: 12px;">Event:</div>
                        <div style="font-size: 12px;">{event_type}</div>
                    </div>
                </div>
            """,
        }
        
        # Create the map with dark style
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v10",
            tooltip=tooltip,
        )
        
        # Display the map
        st.pydeck_chart(r)
        
        # Legend with improved styling
        # st.markdown("""
        # <div class="map-legend">
        #    <div style="display: flex; align-items: center; gap: 8px;">
        #        <div style="width: 12px; height: 12px; background-color: rgb(185, 49, 27); border-radius: 50%;"></div>
        #        <span style="font-size: 0.875rem;">Pro-Democracy Actors</span>
        #    </div>
        #</div>
        # """, unsafe_allow_html=True)
        
        # Display data stats
        st.markdown(f"<div style='font-size: 0.875rem; color: #8b949e; margin-top: 0.75rem;'>Showing {len(filtered_df)} battle events</div>", unsafe_allow_html=True)

        # Display Google Doc content if an actor is selected
        if selected_acronym:
            # Get Google Drive service
            drive_service = get_drive_service()
            
            if drive_service:
                # Folder ID from the shared link
                folder_id = "1oG4H-FS5V_t9LRLkLYyO0kxyzzE7NoVf"
                
                # Get document content
                doc_content = get_google_doc_content(drive_service, folder_id, selected_acronym)
                
                if doc_content:
                    st.markdown("<hr style='margin: 2rem 0; border-color: #30363d; opacity: 0.5;'>", unsafe_allow_html=True)
                    st.markdown(f"### Detailed Information: {selected_acronym}")
                    
                    # Clean up the HTML content from Google Docs
                    # Remove all inline styles first
                    doc_content = re.sub(r'style="[^"]*"', '', doc_content)
                    
                    # Replace Google Docs' complex structure with simpler HTML
                    doc_content = doc_content.replace('<p class="c', '<p class="doc-paragraph c')
                    doc_content = doc_content.replace('<span class="c', '<span class="doc-span c')
                    
                    # Ensure headers are properly styled
                    for i in range(1, 7):
                        doc_content = doc_content.replace(f'<h{i}', f'<h{i} class="doc-header"')
                    
                    # Add a wrapper that applies our styling
                    doc_content = f"""
                    <div class="doc-content">
                        {doc_content}
                    </div>
                    """
                    
                    # Display the document content
                    st.markdown(doc_content, unsafe_allow_html=True)
                else:
                    st.info(f"No detailed information available for {selected_acronym}")
            else:
                st.error("Unable to access Google Drive for detailed information.")

# About the Project Section with improved styling
st.markdown("<hr style='margin: 2rem 0; border-color: #30363d; opacity: 0.5;'>", unsafe_allow_html=True)
# st.markdown('<div class="about-section">', unsafe_allow_html=True)
st.markdown("### About the Project")
st.markdown("""
This interactive visualization tool maps armed actors involved in battles throughout the Spring Revolution across Myanmar since 2021.

The profiles and detailed information about armed actors are products of Burma Civil War Museum's ongoing research into emergence, political aspirations, alliances and operations of emerging armed actors in Central Myanmar. The mapping data for known locations of battles involving the armed actors is sourced from ACLED (Armed Conflict Location & Event Data).  

This tool is designed for researchers, journalists, policy makers, and anyone seeking to understand the 
current situation in Myanmar. For inquiry, please contact office@burmacivilwarmuseum.org.
""")
st.markdown('</div>', unsafe_allow_html=True)

# Footer with improved styling
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("""
<div style="display: flex; justify-content: center; align-items: center; gap: 8px;">
    <span>War Desk</span>
    <span style="font-size: 1.25rem; opacity: 0.5;">•</span>
    <span>Co-Developed by Burma Civil War Museum and Spring Sprouts</span>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
