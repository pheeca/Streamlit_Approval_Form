import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml

# Load the credentials from Streamlit secrets
secret_toml = st.secrets.get("secret_toml")

# Parse the TOML content
secret_config = toml.loads(io.StringIO(secret_toml))

# Extract service account information
try:
    google_sheets_config = secret_config['google_sheets']
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
except KeyError as e:
    st.error(f"Missing key in TOML file: {e}")
    st.stop()

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
options_data = fetch_options(sheet, "Config")
sections_data = fetch_options(sheet, "Config")

if not options_data or not sections_data:
    st.error("Unable to fetch data from Google Sheets.")
    st.stop()

# Convert options data into a usable format
options = {}
for entry in options_data:
    option_name = entry['Sponsorship Type']
    options[option_name] = {
        "points": entry['Points'],
        "max": entry['Max'],
        "uid": entry['UID'],
        "description": entry.get('Details', '').split(',')
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
if 'total_points' not in st.session_state:
    st.session_state.total_points = total_points

if 'remaining_points' not in st.session_state:
    st.session_state.remaining_points = total_points

# Initialize session state for selected options
if 'selected_options' not in st.session_state:
    st.session_state.selected_options = {option: False for option in options.keys()}

# Function to update remaining points
def update_remaining_points():
    deducted_points = sum(option_info['points'] for option, option_info in options.items() if st.session_state.selected_options[option])
    st.session_state.remaining_points = st.session_state.total_points - deducted_points

# Update session state values
st.session_state.total_points = total_points
update_remaining_points()

# Displaying sections and options
for section, section_options in event_sections.items():
    st.subheader(section)
    for option in section_options:
        if option in options:
            unique_key = f"{section}_{option}"
            option_info = options[option]
            points = option_info['points']
            max_range = option_info['max']
            description = option_info["description"]
            uid = option_info['uid']

            formatted_description = "\n".join([f"- {desc.strip()}" for desc in description if desc.strip()])

            st.session_state.selected_options[option] = st.checkbox(
                f"**{option}** - Points: {points}, Max: {max_range}",
                value=st.session_state.selected_options[option],
                key=unique_key
            )
            st.markdown(formatted_description)

    st.write("---")
update_remaining_points()

# Display remaining points
st.write(f"### Remaining Points: {st.session_state.remaining_points}")

# Submit button
if st.button("Submit"):
    selected_options = [option for option, selected in st.session_state.selected_options.items() if selected]
    selected_uids = [options[option]['uid'] for option in selected_options]

    data = {
        "Name": name,
        "Company": company,
        "Email": email,
        "Total Points": st.session_state.total_points,
        "Remaining Points": st.session_state.remaining_points,
        "Selected Options": ", ".join([f"{option} (UID: {options[option]['uid']})" for option in selected_options]),
        "UID": ", ".join(selected_uids)
    }

    worksheet = sheet.worksheet("Sheet1")
    worksheet.append_row(list(data.values()))

    config_data = worksheet.get_all_records()
    for i, entry in enumerate(config_data):
        if entry['UID'] in selected_uids:
            new_max = entry['Max'] - 1
            worksheet.update_cell(i + 2, worksheet.find("Max").col, new_max)  # Adjust row and column accordingly

    st.session_state.selected_options = {option: False for option in options.keys()}
    st.session_state.total_points = 0
    st.session_state.remaining_points = 0
    st.success("Form submitted successfully!")
