import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import string
import toml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from streamlit.elements import image

companyName='Maison Lejeune'
Heading="Ouverture de compte pro"

pc=st.set_page_config(page_title=Heading+" - "+companyName,page_icon= "logo.jpg")#,page_icon= ":clipboard:")



# Load the TOML configuration from Streamlit secrets
#secret_config = st.secrets["google_sheets"]
g_secret_config = toml.load("secret.toml")
# Extract service account information
try:
    secret_config = g_secret_config['google_sheets']
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
# Add custom CSS to hide the GitHub icon
hide_github_icon = """ <style>
#GithubIcon, .stAppToolbar, [class^=_profileContainer_]  {
  visibility: hidden;
}
 </style>
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)

    
# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)
sheet_id = "16Ln8V-XTaSKDm1ycu5CNUkki-x2STgVvPHxSnOPKOwM"  # Replace with your actual Google Sheet ID
sheet = client.open_by_key(sheet_id)

def send_email(sender_email, sender_password, recipient_email, subject, body):
    try:
        # Create a MIME object
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        # Attach the body to the message
        message.attach(MIMEText(body, 'plain'))

        # Establish a secure session with Gmail's outgoing SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Log in with app password
            text = message.as_string()
            server.sendmail(sender_email, recipient_email, text)  # Send the email
            print("Email sent successfully!")
    
    except Exception as e:
        print(f"Failed to send email: {e}")

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
    option_name = entry['Computed Column']
    if entry['Status']!='Ongoing':
        continue

    try:
        points = int(entry['Points'])
    except ValueError:
        points = 0
    try:
        if str(entry['Max']).lower() == "n/a":
            max_range = "n/a"
        else:
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
        "computed_months_options": entry.get('Computed Months Options', '').split(','),
        'extra':entry
    }

# Convert sections data into a usable format
event_sections = {}
for entry in sections_data:
    section = entry['Event Name']
    option = entry['Sponsorship Type']
    if section not in event_sections:
        event_sections[section] = []
    event_sections[section].append(option)

# Function to handle months selection without modifying session_state directly
def handle_month_selection(unique_key, max_months, available_months):
    selected_months_key = f"{unique_key}_months"

    # Initialize the selected months in session state if not present
    if selected_months_key not in st.session_state:
        st.session_state[selected_months_key] = []
    ulabel=unique_key.replace("_"," ")
    # Create the multiselect widget
    selected_months = st.multiselect(
        f"Select the months you choose to sponsor for {ulabel}",
        available_months,
        st.session_state[selected_months_key],
        key=selected_months_key,
        max_selections=max_months
    )

    # Enforce maximum selection by Streamlit (not manually)
    #if len(selected_months) > max_months:
    #    st.warning(f"You can select up to {max_months} months.")
    #    # Trim the selection to max_months
    #    selected_months = selected_months[:max_months]
    #    # Update the session state accordingly
    #    st.session_state[selected_months_key] = selected_months

    # No direct modification of st.session_state.remaining_points here
    # Points deduction will be handled separately

# Function to handle months selection without modifying session_state directly
def handle_month_selection2(unique_key,  available_months):
    max_months=1
    selected_months_key = f"{unique_key}_months"

    # Initialize the selected months in session state if not present
    if selected_months_key not in st.session_state:
        st.session_state[selected_months_key] = []
    ulabel=unique_key.replace("_"," ")
    # Create the multiselect widget
    selected_months = st.multiselect(
        f"Select the months you choose to sponsor for {ulabel}",
        available_months,
        st.session_state[selected_months_key],
        key=selected_months_key,
    #    max_selections=max_months
    )


# Function to calculate remaining points
def calculate_remaining_points():
    deducted_points = 0
    for key, selected in st.session_state.selected_options.items():
        if selected:
            #option_name = key.split("_")[1]
            optionKey=key.replace('_',' - ')
            months_key = f"{key}_months"
            multiplier=1
            if months_key in st.session_state:#options[optionKey]['extra']['Multiples']=='Yes' and 
                multiplier=len(st.session_state[months_key])

            deducted_points += (options[optionKey]['points']*multiplier)
            # Check if this option has associated months
            
            #if :
            #    deducted_points += len(st.session_state[months_key]) * 3  # Deduct 3 points per selected month
    st.session_state.remaining_points = st.session_state.total_points - deducted_points



# Streamlit form
col1, col2 = st.columns([3,2])  
with col1:
    st.title(Heading)

with col2:
    st.image("logo-white.svg", width=200)

r2col1, r2col2 = st.columns(2)  
# Basic information inputs with clear labels
no_de_compete = r2col1.text_input("N° DE COMPTE", help="Entrez les 6 premiers chiffres de votre numéro de compte.") # Account No
establissement = r2col1.text_input("ÉTABLISSEMENT", help="Nom de l'établissement bancaire.") # Bank Establishment
pays = r2col1.text_input("PAYS", help="Pays de résidence.") # country

siret = r2col2.text_input("SIRET", help="Numéro SIRET à 14 chiffres.") # SIRET
tva_europeen_FR = r2col2.text_input("TVA EUROPEEN : FR", help="Numéro de TVA intracommunautaire (11 chiffres).") # EUROPEAN VAT:Intracommunity VAT number (11 digits)
r2col2.caption("(pour Union Européenne uniquement)")

line_seperator=st.divider()

r3col1, r3col2 = st.columns(2)  
#r3col1.
no_de_compete1 = r3col1.text_input("N° DE COMPTE1", help="Entrez les 6 premiers chiffres de votre numéro de compte.") # Account No
establissement1 = r3col1.text_input("ÉTABLISSEMENT1", help="Nom de l'établissement bancaire.") # Bank Establishment


contact_name = st.text_input("Your Name", help="Who should be our regular contact when we need names for events, marketing materials, etc.")
st.caption("Who should be our regular contact when we need names for events, marketing materials, etc.")

Contact_Name=st.text_input("Contact Name")
#Contact_Company=st.text_input("Contact Company ")
#Contact_Email=st.text_input("Contact Email")

email = st.text_input("Email", help="Enter a valid email address.")
phone_number = st.text_input('Phone Number', help="Enter your contact number.")

# Total points input
total_points = st.number_input(
    "SSP Points (Please use the number in the email)",
    min_value=0,
    max_value=100,
    value=0,
    help="Please enter a value between 0 and 100."
)
# Initialize session state for total_points and remaining_points
if 'total_points' not in st.session_state or st.session_state.total_points != total_points:
    st.session_state.total_points = total_points
    st.session_state.remaining_points = total_points

# Initialize session state for selected options and months
if 'selected_options' not in st.session_state:
    st.session_state.selected_options = {}
if 'selected_months' not in st.session_state:
    st.session_state.selected_months = {}

# **New:** Calculate remaining points before rendering options
calculate_remaining_points()

# Displaying sections and options
for section, section_options in event_sections.items():
    st.subheader(section)
    for option in section_options:
        optionKey=(section+' - '+option)
        if  optionKey in options:
            unique_key = f"{section}_{option}"
            option_info = options[optionKey]
            points = option_info['points']
            max_range = option_info['max']
            description = option_info["description"]
            uid = option_info['uid']
            
            #if "WEBSITE:  2025 - Member Spotlight-Quarterly" in option_info['extra']['Computed Column']:
            #    ab=2
            # Clean and format the description into bullet points
            formatted_description = "\n".join([f"- {desc.strip()}" for desc in description if desc.strip()])

            # Initialize the session state for the unique key if it doesn't exist
            if unique_key not in st.session_state.selected_options:
                st.session_state.selected_options[unique_key] = False

            # Determine if the checkbox should be disabled
            disabled = False

            # Check for max selection constraints
            if isinstance(max_range, int) :
                current_selection_count = sum(
                    1 for key, selected in st.session_state.selected_options.items()
                    if selected and key.startswith(section)
                )
                if current_selection_count >= max_range and not st.session_state.selected_options[unique_key]:
                    disabled = True

            # **New Logic:** Disable if selecting this option would exceed remaining points
            if not st.session_state.selected_options[unique_key] and points > st.session_state.remaining_points:
                disabled = True

            # Display the checkbox and immediately update the session state based on the checkbox value
            checkbox_label = f"**{option}** - Points: {points}"
            if not (not option_info['extra']['Associated Subtitle']):
                # Modify the label for Luncheon sponsors
                checkbox_label += f" ({option_info['extra']['Associated Subtitle']})"
            
            if max_range!="n/a":
                checkbox_label += f", Max: {option_info['extra']['Default Max']} ({max_range} remaining)"

            selected = st.checkbox(
                checkbox_label,
                value=st.session_state.selected_options[unique_key],
                key=unique_key,
                disabled=disabled
            )

            # Update session state based on the checkbox selection
            if selected != st.session_state.selected_options[unique_key]:
                st.session_state.selected_options[unique_key] = selected
                calculate_remaining_points()

            # Show the dropdown for months if the option is selected and it's a Luncheons option
            isSelectedOpt=unique_key in [so for so in st.session_state.selected_options if st.session_state.selected_options[so]]
            if isSelectedOpt and option_info['max_month_selection']>0 and len([a for a in option_info['computed_months_options'] if a])>0:#and "Luncheon" in option:
                max_months = option_info['max_month_selection']
                available_months = option_info['computed_months_options']
                handle_month_selection(unique_key, max_months, available_months)
            
            if isSelectedOpt and option_info['extra']['Multiples']=='Yes':
                available_months = option_info['extra']['Multiple Options'].split(',')
                handle_month_selection2(unique_key,  available_months)
            
            # Display the formatted description
            st.markdown(formatted_description)

    st.write("---")

# **Removed:** Existing call to calculate_remaining_points() after the loop
# calculate_remaining_points()

# Display remaining points in the sidebar only when total_points > 0
if st.session_state.total_points > 0:
    st.sidebar.title("Submission Details")
    st.sidebar.write(f"**Name:** {contact_name}")
    st.sidebar.write(f"**Email:** {email}")
    st.sidebar.write(f"**Organization:** {company}")
    st.sidebar.write(f"**Total Points Allotted:** {st.session_state.total_points}")
    st.sidebar.write(f"### Remaining Points: {st.session_state.remaining_points}")

# Function to generate a random UID for each submission
def generate_random_uid():
    return "UID-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Submit button
if st.button("Submit"):
    selected_options = [key.replace("_"," - ") for key, selected in st.session_state.selected_options.items() if selected]
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
        "Name": contact_name,
        "Company": company,
        "Email": email,
        "phoneNumber": phone_number,
        "Total Points": st.session_state.total_points,
        "Contact Name":Contact_Name,
       # "Contact Company":Contact_Company,
       # "Contact Email":Contact_Email,
        "Remaining Points": st.session_state.remaining_points,
        "Selected Options": "; ".join([f"{option} (UID: {options[option]['uid']})" for option in selected_options]),
        "UID": ", ".join([f" {options[option]['uid']}" for option in selected_options]),
        "CustomerUID": submission_uid,
        "Selected Months": " | ".join([f"{key.split('_')[1]}: {months}" for key, months in selected_months_data.items()]),
        "Submission Date": submission_date
    }

    # Store data in 'raw info' sheet
    sheet.worksheet("raw info").append_row([
        data["Name"], data["Company"], data["Email"], data["phoneNumber"], data["Total Points"],data["Contact Name"],
        data["Remaining Points"], data["Selected Options"], data["UID"], submission_uid, data["Selected Months"], data["Submission Date"]
    ])

    # Store data in 'Submitted' sheet
    submission_data = [
        submission_uid, data["Name"], data["Company"], data["Email"], data["phoneNumber"],
        data["Total Points"], data["Remaining Points"],data["Contact Name"],"","",#,data["Contact Company"],data["Contact Email"]
    ]

    # Dynamically add columns for each selected option with the formatted event and sponsorship details
    for section, section_options in event_sections.items():
        for option in section_options:
            computed_column = f"{section} - {option}"
            unique_key = f"{section}_{option}"
            col_value = ""
            if unique_key in selected_options_full:
                col_value = "YES"
                # Append selected months if applicable
                selected_months = st.session_state.get(f"{unique_key}_months", [])
                if selected_months:
                    col_value += " (" + ", ".join(selected_months) + ")"
            else:
                col_value = "NO"
            submission_data.append(col_value)

    # Fetch email credentials from Streamlit secrets for security
    # sender_email = st.secrets["email"]["sender"]
    # app_password = st.secrets["email"]["app_password"]
    sender_email = ""
    app_password = ""
    recipient_email = email
    subject = "Form Submitted Successfully"
    body = f"""
UID: {submission_uid}
Name: {contact_name}
Company: {company}
Email: {email}
Total Points: {st.session_state.total_points}
Remaining Points: {st.session_state.remaining_points}

Selected Options:
{", ".join(selected_options)}

Selected Months:
{", ".join([f"{key.split('_')[1]}: {months}" for key, months in selected_months_data.items()])}

Submission Date: {submission_date}
"""


    sheet.worksheet("Submitted").append_row(submission_data)

    # Update Max value in Config sheet based on selected UIDs
    config_worksheet = sheet.worksheet("Config")
    config_data = config_worksheet.get_all_records()

    for i, entry in enumerate(config_data):
        if entry['UID'] in selected_uids:
            try:
                if isinstance(entry['Max'], int):
                    new_max = entry['Max'] - 1
                    config_worksheet.update_cell(i + 2, config_worksheet.find('Max').col, new_max)
            except ValueError:
                pass

    st.success("Form submitted successfully!")
