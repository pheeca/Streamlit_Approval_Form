import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import string
import toml
# Load the TOML configuration from Streamlit secrets
secret_config = st.secrets["google_sheets"]
# Extract service account information
try:
    
    service_account_info = {
        "type": secret_config["type"],
        "project_id": secret_config["project_id"],
        "private_key_id": secret_config["private_key_id"],
        "private_key": secret_config["private_key"].replace("\\n", "\n"),
        "client_email": secret_config["client_email"],
        "client_id": secret_config["client_id"],
        "auth_uri": secret_config["auth_uri"],
        "token_uri": secret_config["token_uri"],
        "auth_provider_x509_cert_url": secret_config["auth_provider_x509_cert_url"],
        "client_x509_cert_url": secret_config["client_x509_cert_url"]
    }
except KeyError as e:
    st.error(f"Missing key in TOML file: {e}")
    st.stop()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)
sheet_id = "16Ln8V-XTaSKDm1ycu5CNUkki-x2STgVvPHxSnOPKOwM"  # Replace with your actual Google Sheet ID
sheet = client.open_by_key(sheet_id)
#sheet.batch_update
# Fetching options and descriptions from the sheet
def fetch_options(sheet, tab_name):
    try:
        worksheet = sheet.worksheet(tab_name)
        data = worksheet.get_all_records()
        return data
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet {tab_name} not found in Google Sheets.")
        st.stop()

options_data = fetch_options(sheet, "Config")
sections_data = fetch_options(sheet, "Config")

if not options_data or not sections_data:
    st.error("Unable to fetch data from Google Sheets.")
    st.stop()

# Convert options data into a usable format
options = {}
for entry in options_data:
    option_name = entry['Sponsorship Type']
    try:
        points = int(entry['Points'])
    except ValueError:
        points = 0
    try:
        max_range = int(entry['Max'])
    except ValueError:
        max_range = 0
    try:
        max_month_selection = int(entry.get('Max Month Selection', 0))
    except ValueError:
        max_month_selection = 0
    
    options[option_name] = {
        "points": points,
        "max": max_range,
        "uid": entry['UID'],
        "description": entry.get('Details', '').split(','),
        "max_month_selection": max_month_selection,
        "computed_months_options": entry.get('Computed Months Options', '').split(',')
    }

# Convert sections data into a usable format
event_sections = {}
for entry in sections_data:
    section = entry['Event Name']
    option = entry['Sponsorship Type']
    if section not in event_sections:
        event_sections[section] = []
    event_sections[section].append(option)

# Function to handle months selection and session state update
def handle_month_selection(unique_key, max_months, available_months):
    selected_months_key = f"{unique_key}_months"
    
    if selected_months_key not in st.session_state:
        st.session_state[selected_months_key] = []

    selected_months = st.multiselect(
        f"Select up to {max_months} months",
        available_months,
        default=st.session_state[selected_months_key],
        max_selections=max_months
    )

    st.session_state[selected_months_key] = selected_months

# Streamlit form
st.image("logo.jpg", width=200)
st.title("Westchester Chamber Alliance Sponsorship")

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

# Initialize session state for selected options and months
if 'selected_options' not in st.session_state:
    st.session_state.selected_options = {}
if 'selected_months' not in st.session_state:
    st.session_state.selected_months = {}

# Function to update remaining points
def update_remaining_points():
    deducted_points = sum(
        options[option_key.split("_")[1]]['points']
        for option_key, selected in st.session_state.selected_options.items()
        if selected
    )
    st.session_state.remaining_points = st.session_state.total_points - deducted_points

# Pre-calculate remaining points before rendering the UI
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

            # Clean and format the description into bullet points
            formatted_description = "\n".join([f"- {desc.strip()}" for desc in description if desc.strip()])

            # Initialize the session state for the unique key if it doesn't exist
            if unique_key not in st.session_state.selected_options:
                st.session_state.selected_options[unique_key] = False

            # Determine if the checkbox should be disabled
            disabled = ((max_range == 0)or (st.session_state.remaining_points < points))and (str(max_range.lower()!="n/a"))

            # Display the checkbox and immediately update the session state based on the checkbox value
            selected = st.checkbox(
                f"**{option}** - Points: {points}, Max: {max_range}",
                value=st.session_state.selected_options[unique_key],
                key=unique_key,
                disabled=disabled
            )

            # Update session state based on the checkbox selection
            if selected != st.session_state.selected_options[unique_key]:
                st.session_state.selected_options[unique_key] = selected
                update_remaining_points()

            # Show the dropdown for months if the option is selected and it's a Luncheons option
            if st.session_state.selected_options[unique_key] and "Luncheon" in option:
                max_months = option_info['max_month_selection']
                available_months = option_info['computed_months_options']
                handle_month_selection(unique_key, max_months, available_months)

            # Display the formatted description
            st.markdown(formatted_description)

    st.write("---")

# Update remaining points again after rendering options
update_remaining_points()

# Display remaining points in the sidebar only when total_points > 0
if st.session_state.total_points > 0:
    st.sidebar.title("Submission Details")
    st.sidebar.write(f"**Name:** {name}")
    st.sidebar.write(f"**Email:** {email}")
    st.sidebar.write(f"**Company:** {company}")
    st.sidebar.write(f"**Total Points Allotted:** {st.session_state.total_points}")
    st.sidebar.write(f"### Remaining Points: {st.session_state.remaining_points}")

# Function to generate a random UID for each submission
def generate_random_uid():
    return "UID-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Submit button
if st.button("Submit"):
    selected_options = [key.split("_")[1] for key, selected in st.session_state.selected_options.items() if selected]
    selected_options_full = [key for key, selected in st.session_state.selected_options.items() if selected]
    selected_uids = [options[option]['uid'] for option in selected_options]

    # Collect selected months data
    selected_months_data = {
        key: " - ".join(months) for key, months in st.session_state.items() if months and key.endswith("_months")
    }

    # Add current date and time to the data
    submission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate a random UID for the submission
    submission_uid = generate_random_uid()

    # Prepare data to store in Google Sheets
    data = {
        "Name": name,
        "Company": company,
        "Email": email,
        "Total Points": st.session_state.total_points,
        "Remaining Points": st.session_state.remaining_points,
        "Selected Options": "; ".join([f"{option} (UID: {options[option]['uid']})" for option in selected_options]),
        "UID": ", ".join([f" {options[option]['uid']}" for option in selected_options]),
        "CustomerUID": submission_uid,
        "Selected Months": " | ".join([f"{key.split('_')[1]}: {months}" for key, months in selected_months_data.items()]),
        "Submission Date": submission_date
    }

    # Store data in 'raw info' sheet
    sheet.worksheet("raw info").append_row([
        data["Name"], data["Company"], data["Email"], data["Total Points"],
        data["Remaining Points"], data["Selected Options"], data["UID"],submission_uid, data["Selected Months"], data["Submission Date"]
    ])

    # Store data in 'Submitted' sheet
    submission_data = [
        submission_uid, data["Name"], data["Company"], data["Email"],
        data["Total Points"], data["Remaining Points"]
    ]

    # Dynamically add columns for each selected option with the formatted event and sponsorship details
    for section, section_options in event_sections.items():
        for option in section_options:
            col_value = ""
            print(section+"_"+option,selected_options_full)
            #bas check karna hai that option of same type isnt seleceted 
            if section+"_"+option in selected_options_full:
                
                col_value = "YES"
                #print(selected_months_data.items(),section,option,32)
                month_current=  [months for key, months in selected_months_data.items() if key==section+"_"+option+"_months"]
                
                if len(month_current)>0:
                    print(month_current,section,option,33)
                    col_value+=month_current[0]

                    
            else:
                col_value="NO"    
            submission_data.append(col_value)

    sheet.worksheet("Submitted").append_row(submission_data)

    # Update Max value in Config sheet based on selected UIDs
    config_worksheet = sheet.worksheet("Config")
    config_data = config_worksheet.get_all_records()

    for i, entry in enumerate(config_data):
        if entry['UID'] in selected_uids:
            try:
                max_value = int(entry['Max'])
                new_max = max_value - 1
                config_worksheet.update_cell(i + 2, config_worksheet.find('Max').col, new_max)
            except ValueError:
                pass

    st.success("Form submitted successfully!")
