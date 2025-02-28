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

# Set page configuration
st.set_page_config(
    page_title="War Desk",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode
st.markdown("""
<style>
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    .stSelectbox, .stMultiselect {
        background-color: transparent;
        color: white;
        border-radius: 5px;
    }
    .floating-filters {
        background-color: rgba(42, 42, 42, 0.8);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
        width: 100%;
    }
    .dialog-box {
        background-color: rgba(42, 42, 42, 0.9);
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        border: 1px solid #444;
    }
    .doc-content {
        background-color: rgba(42, 42, 42, 0.9);
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        border: 1px solid #444;
        max-height: 1000px;
        overflow-y: auto;
    }
    .doc-content img {
        max-width: 100%;
        height: auto;
    }
    .doc-content * {
        color: #ffffff !important;
        background-color: transparent !important;
        font-family: 'Arial', sans-serif !important;
    }
    .doc-content p, .doc-content span, .doc-content div {
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    .doc-content h1, .doc-content h2, .doc-content h3, .doc-content h4 {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    .doc-content a {
        color: #4da6ff !important;
        text-decoration: underline !important;
    }
    h1, h2, h3 {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("War Desk")
st.markdown("### Mapping Armed Actors in Spring Revolution")

# Cache the drive service creation
@st.cache_resource
def get_drive_service():
    try:
        # Create credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            'war-desk-mk.json',
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
            #st.info(f"No document found for acronym: {acronym}")
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
            
            #st.success("Successfully loaded data from Google Drive!")
            
        except Exception as e:
            st.error(f"Error loading data from Google Drive: {e}")
            st.info("Attempting to load from direct URL...")
            
            # Alternative: try to download directly from the public URL
            try:
                url = "https://docs.google.com/spreadsheets/d/1ucEOV4c1ayKizMtV0Z5k7j-sKcnNniMs/export?format=xlsx"
                profiles_df = pd.read_excel(url, sheet_name="Profile")
                st.success("Successfully loaded data from direct URL!")
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

# State management for filters
if 'selected_region' not in st.session_state:
    st.session_state.selected_region = 'All'
if 'selected_actor' not in st.session_state:
    st.session_state.selected_actor = 'All'
if 'selected_acronym' not in st.session_state:
    st.session_state.selected_acronym = 'All'

# Function to update filter options based on current selections
def get_filtered_options(df, selected_region, selected_actor, selected_acronym):
    temp_df = df.copy()
    
    # Apply filters incrementally
    if selected_region != 'All':
        temp_df = temp_df[temp_df['admin1'] == selected_region]
    
    if selected_actor != 'All':
        temp_df = temp_df[temp_df['name'] == selected_actor]
    
    if selected_acronym != 'All':
        temp_df = temp_df[temp_df['acronym'] == selected_acronym]
    
    # Get unique values for each filter from the filtered dataframe
    regions = ['All'] + sorted(temp_df['admin1'].dropna().unique().tolist())
    actors = ['All'] + sorted(temp_df['name'].dropna().unique().tolist())
    acronyms = ['All'] + sorted([acr for acr in temp_df['acronym'].dropna().unique().tolist() if acr.strip() != ""])
    
    return regions, actors, acronyms

# Filter callback functions
def on_region_change():
    # Update the selected region in session state
    region_val = st.session_state.region_selector
    st.session_state.selected_region = region_val
    
    # Reset actor and acronym when region changes
    st.session_state.selected_actor = 'All'
    st.session_state.selected_acronym = 'All'

def on_actor_change():
    # Update the selected actor in session state
    actor_val = st.session_state.actor_selector
    st.session_state.selected_actor = actor_val
    
    # If an actor is selected, automatically select its acronym if it exists
    if actor_val != 'All':
        actor_info = actors_df[actors_df['name'] == actor_val]
        if not actor_info.empty and pd.notna(actor_info.iloc[0]['acronym']):
            st.session_state.selected_acronym = actor_info.iloc[0]['acronym']
    else:
        # If actor is reset to 'All', also reset acronym
        st.session_state.selected_acronym = 'All'

def on_acronym_change():
    # Update the selected acronym in session state
    acronym_val = st.session_state.acronym_selector
    st.session_state.selected_acronym = acronym_val
    
    # If an acronym is selected, automatically select its actor if it exists
    if acronym_val != 'All':
        acronym_matches = actors_df[actors_df['acronym'] == acronym_val]
        if not acronym_matches.empty:
            st.session_state.selected_actor = acronym_matches.iloc[0]['name']
    else:
        # If acronym is reset to 'All', also reset actor
        st.session_state.selected_actor = 'All'

# Filters at the top
st.subheader("Filters")

# Create three columns for filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

# Get initial filter options
regions, actors, acronyms = get_filtered_options(
    actors_df, 
    st.session_state.selected_region, 
    st.session_state.selected_actor, 
    st.session_state.selected_acronym
)

with filter_col1:
    # Region filter (admin1)
    if st.session_state.selected_region in regions:
        index = regions.index(st.session_state.selected_region)
    else:
        index = 0
        st.session_state.selected_region = regions[0]
    
    selected_region = st.selectbox(
        "Select Region", 
        regions,
        index=index,
        key="region_selector",
        on_change=on_region_change
    )
    # Update session state after widget is created
    st.session_state.selected_region = selected_region

with filter_col2:
    # Actor name filter
    if st.session_state.selected_actor in actors:
        index = actors.index(st.session_state.selected_actor)
    else:
        index = 0
        st.session_state.selected_actor = actors[0]
    
    selected_actor = st.selectbox(
        "Select Actor Name", 
        actors,
        index=index,
        key="actor_selector",
        on_change=on_actor_change
    )
    # Update session state after widget is created
    st.session_state.selected_actor = selected_actor

with filter_col3:
    # Acronym filter
    if st.session_state.selected_acronym in acronyms:
        index = acronyms.index(st.session_state.selected_acronym)
    else:
        index = 0
        st.session_state.selected_acronym = acronyms[0]
    
    selected_acronym = st.selectbox(
        "Select Acronym", 
        acronyms,
        index=index,
        key="acronym_selector",
        on_change=on_acronym_change
    )
    # Update session state after widget is created
    st.session_state.selected_acronym = selected_acronym

# Main layout with two columns for map and profile
col1, col2 = st.columns([3, 1])

# Determine which actor to display profile for
display_actor = None
if selected_actor != 'All':
    display_actor = selected_actor
elif selected_acronym != 'All':
    # Find full name from acronym
    acronym_matches = actors_df[actors_df['acronym'] == selected_acronym]
    if not acronym_matches.empty:
        display_actor = acronym_matches.iloc[0]['name']

with col2:
    # Display profile information
    st.subheader("Actor Profile")
    
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
            st.write(f"**Name:** {profile_data['Armed Group Name']}")
            
            # Display available profile information
            for col in profile_data.index:
                if col != 'Armed Group Name' and pd.notna(profile_data[col]) and profile_data[col] != "":
                    # Clean up column name for display
                    display_col = col.replace('_', ' ').strip()
                    if display_col == "":
                        display_col = "Location"
                    st.write(f"**{display_col}:** {profile_data[col]}")
        else:
            st.info(f"No profile information found for {display_actor}")
    else:
        st.info("Select an actor to view profile information")

with col1:
    # Filter data based on selections
    filtered_df = actors_df.copy()
    
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['admin1'] == selected_region]
    
    if selected_actor != 'All':
        filtered_df = filtered_df[filtered_df['name'] == selected_actor]
    
    if selected_acronym != 'All':
        filtered_df = filtered_df[filtered_df['acronym'] == selected_acronym]
    
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
            #'Junta': [255, 0, 0],  # Red for Junta
            'Pro-Democracy': [185, 49, 27],  # Blue for Pro-Democracy
            #'Ethnic': [0, 255, 0],  # Green for Ethnic
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
            radius_min_pixels=2,
            radius_max_pixels=10,
        )
        
        # Create the deck
        view_state = pdk.ViewState(
            latitude=myanmar_center[0],
            longitude=myanmar_center[1],
            zoom=4,
            pitch=0,
        )
        
        # Tooltip
        tooltip = {
            "html": "<b>Actor:</b> {name}<br>"
                   "<b>Acronym:</b> {acronym}<br>"
                   "<b>Location:</b> {location}<br>"
                   "<b>Region:</b> {admin1}<br>"
                   "<b>Date:</b> {event_date}<br>"
                   "<b>Event:</b> {event_type}",
            "style": {
                "backgroundColor": "rgba(42, 42, 42, 0.9)",
                "color": "white",
                "borderRadius": "5px",
                "padding": "10px",
                "fontSize": "12px",
            }
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
        
        # Legend
        st.markdown("""
        <div style="display: flex; gap: 20px; margin-top: 10px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: rgb(185, 49, 27); border-radius: 50%;"></div>
                <span>Pro-Democracy Actors</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display data stats
        #st.markdown(f"**Showing {len(filtered_df)} battle events out of {len(actors_df)} total battle events**")

        # Display Google Doc content if an actor is selected
        if selected_acronym != 'All' or selected_actor != 'All':
            # Get the acronym to use for fetching the doc
            doc_acronym = selected_acronym if selected_acronym != 'All' else None
            
            # If we have a selected actor but no acronym, try to get the acronym
            if not doc_acronym and selected_actor != 'All':
                actor_info = actors_df[actors_df['name'] == selected_actor]
                if not actor_info.empty and pd.notna(actor_info.iloc[0]['acronym']):
                    doc_acronym = actor_info.iloc[0]['acronym']
            
            if doc_acronym:
                st.markdown("---")
                st.subheader(f"Detailed Information: {doc_acronym}")
                
                # Get Google Drive service
                drive_service = get_drive_service()
                
                if drive_service:
                    # Folder ID from the shared link
                    folder_id = "1oG4H-FS5V_t9LRLkLYyO0kxyzzE7NoVf"
                    
                    # Get document content
                    doc_content = get_google_doc_content(drive_service, folder_id, doc_acronym)
                    
                    if doc_content:
                        # Clean up the HTML content from Google Docs
                        # Remove all inline styles first
                        import re
                        # Remove style attributes
                        doc_content = re.sub(r'style="[^"]*"', '', doc_content)
                        
                        # Replace Google Docs' complex structure with simpler HTML
                        # This helps with rendering in Streamlit
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
                        st.info(f"No detailed information available for {doc_acronym}")
                else:
                    st.error("Unable to access Google Drive for detailed information.")

# About the Project Section
st.markdown("---")
st.subheader("About the Project")
st.markdown("""
This interactive visualization tool maps armed actors involved in battles throughout the Spring Revolution across Myanmar since 2021.

The profiles and detailed information about armed actors are products of Burma Civil War Museum's ongoing research into emergance, political aspirations, alliances and operations of emerging armed actors in Central Myanmar. The mapping data for known locations of battles involving the armed actors is sourced from ACLED (Armed Conflict Location & Event Data).  

This tool is designed for researchers, journalists, policy makers, and anyone seeking to understand the 
current situation in Myanmar. For inquiry, please contact office@burmacivilwarmuseum.org.
""")

# Footer
st.markdown("---")
st.markdown("War Desk | Co-Developed by Burma Civil War Museum and Spring Sprouts")