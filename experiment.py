import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml
import io

# Access secrets from Streamlit's secret management
google_sheets_config = st.secrets["google_sheets"]

# Parse the TOML content
#secret_config = toml.loads(secret_toml)

# Extract service account information
service_account_info = {
    "type": google_sheets_config["type"],
    "project_id": google_sheets_config["project_id"],
    "private_key_id": google_sheets_config["private_key_id"],
    "private_key": google_sheets_config["private_key"].replace("\n", "\n"),
    "client_email": google_sheets_config["client_email"],
    "client_id": google_sheets_config["client_id"],
    "auth_uri": google_sheets_config["auth_uri"],
    "token_uri": google_sheets_config["token_uri"],
    "auth_provider_x509_cert_url": google_sheets_config["auth_provider_x509_cert_url"],
    "client_x509_cert_url": google_sheets_config["client_x509_cert_url"]
}

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("16Ln8V-XTaSKDm1ycu5CNUkki-x2STgVvPHxSnOPKOwM")

# Fetching options and descriptions from the sheet
def fetch_options(sheet, tab_name):
    worksheet = sheet.worksheet(tab_name)
    data = worksheet.get_all_records()
    return data

# Update tab names based on your sheet
options_data = fetch_options(sheet, "Config")  # Ensure this tab exists
sections_data = fetch_options(sheet, "Config")  # Ensure this tab exists

if not options_data or not sections_data:
    st.error("Unable to fetch data from Google Sheets.")
    st.stop()

# Convert options data into a usable format
options = {}
for entry in options_data:
    # Use 'Sponsorship Type' as the key for options
    option_name = entry['Sponsorship Type']
    options[option_name] = {
        "points": entry['Points'],
        "max": entry['Max'],  # Assuming 'Max' value is available
        "uid": entry['UID'],  # Assuming 'UID' value is available
        "description": entry.get('Details', '').split(',')  # Use 'Details' instead of 'Description'
    }

# Convert sections data into a usable format
event_sections = {}
for entry in sections_data:
    section = entry['Event Name']
    option = entry['Sponsorship Type']
    if section not in event_sections:
        event_sections[section] = []
    event_sections[section].append(option)

# Streamlit form
st.title("Sponsorship Selection Form")

# Basic information inputs
name = st.text_input("Name")
company = st.text_input("Company")
email = st.text_input("Email")

# Total points input
total_points = st.number_input("Enter Total Points Allotted", min_value=0, value=0)

# Initialize session state for total_points and remaining_points
if 'total_points' not in st.session_state or st.session_state.total_points != total_points:
    st.session_state.total_points = total_points
    st.session_state.remaining_points = total_points

# Initialize session state for selected options
if 'selected_options' not in st.session_state:
    st.session_state.selected_options = {}

# Function to update remaining points
def update_remaining_points():
    # Calculate total deducted points based on selected options
    deducted_points = sum(
        options[option_key.split("_")[1]]['points']
        for option_key, selected in st.session_state.selected_options.items()
        if selected
    )
    st.session_state.remaining_points = st.session_state.total_points - deducted_points

# Displaying sections and options
for section, section_options in event_sections.items():
    st.subheader(section)  # Ensure this is rendered correctly
    for option in section_options:
        if option in options:
            # Use a unique key combining the section and option name
            unique_key = f"{section}_{option}"
            option_info = options[option]
            points = option_info['points']
            max_range = option_info['max']
            description = option_info["description"]
            uid = option_info['uid']

            # Clean and format the description into bullet points
            formatted_description = "\n".join([f"- {desc.strip()}" for desc in description if desc.strip()])

            # Display the checkbox and associated details
            st.session_state.selected_options[unique_key] = st.checkbox(
                f"**{option}** - Points: {points}, Max: {max_range}",  # Keep the UID in a separate section if needed
                value=st.session_state.selected_options.get(unique_key, False),
                key=unique_key
            )
            
            # Use st.markdown to ensure correct rendering of the formatted description
            st.markdown(formatted_description)

    # Add a clear divider between sections
    st.write("---")

# Update remaining points after rendering options
update_remaining_points()

# Display remaining points
st.write(f"### Remaining Points: {st.session_state.remaining_points}")

# Submit button
if st.button("Submit"):
    # Collect selected options and their UIDs
    selected_options = [key.split("_")[1] for key, selected in st.session_state.selected_options.items() if selected]
    selected_uids = [options[option]['uid'] for option in selected_options]

    # Prepare data to store in Google Sheets
    data = {
        "Name": name,
        "Company": company,
        "Email": email,
        "Total Points": st.session_state.total_points,
        "Remaining Points": st.session_state.remaining_points,
        "Selected Options": ", ".join([f"{option} (UID: {options[option]['uid']})" for option in selected_options]),
        "UID": ", ".join(selected_uids)
    }

    # Store data in Google Sheets
    sheet.worksheet("Sheet1").append_row([data["Name"], data["Company"], data["Email"], data["Total Points"], data["Remaining Points"], data["Selected Options"], data["UID"]])

    # Update Max value in Config sheet based on selected UIDs
    config_worksheet = sheet.worksheet("Config")
    config_data = config_worksheet.get_all_records()

    # Loop through config_data and find the matching UIDs
    for i, entry in enumerate(config_data):
        if entry['UID'] in selected_uids:
            # Subtract 1 from the Max field for the selected UID
            new_max = entry['Max'] - 1
            # Update the Max value in the sheet
            config_worksheet.update_cell(i + 2, config_worksheet.find('Max').col, new_max)

    # Reset form inputs by clearing session state values
    st.session_state.selected_options = {}
    st.session_state.total_points = 0
    st.session_state.remaining_points = 0
    st.success("Form submitted successfully!")
