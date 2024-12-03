import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dateutil.parser import parse
import random
import string
import toml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from streamlit.elements import image
import os
import pandas as pd
#pip install streamlit-drawable-canvas==0.9.3
from streamlit_drawable_canvas import st_canvas
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import uuid
import png
from PIL import Image
import numpy as np
import json
import io
from xhtml2pdf import pisa
from email.mime.image import MIMEImage

# Function to generate a random UID for each submission
def generate_random_uid():
    return uuid.uuid4().hex

if "edit" not in list(st.query_params.keys()):
    currentID=generate_random_uid()
else:
    currentID=st.query_params["edit"]

companyName='Maison Lejeune'
Heading="Ouverture de compte pro"

pc=st.set_page_config(page_title=Heading+" - "+companyName,page_icon= "logo.jpg")#,page_icon= ":clipboard:")

is_localhost = os.getenv('STREAMLIT_HOST') in ['localhost', '127.0.0.1']


# Load the TOML configuration from Streamlit secrets
if is_localhost:
    g_secret_config = toml.load("secret.toml")
    secret_config = g_secret_config['google_sheets']
else:
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
    sheetId =  secret_config["sheetId"]
    UploadPDFfolder =  secret_config["UploadPDFfolder"]
    UploadSignfolder =  secret_config["UploadSignfolder"]
except KeyError as e:
    st.error(f"Missing key in TOML file: {e}")
    st.stop()
# Add custom CSS to hide the GitHub icon
hide_github_icon = """ <style>

[data-testid=stElementToolbarButton] {
    display: none;
}
[data-testid="stMainBlockContainer"] {
    max-width: 55rem
}
[data-testid="stToolbar"] {
    max-width: 55rem
}
 </style>
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)
fileA = []
dataSubmission = []

IsEdit = False
editIndex = 0
edit_date = ''
submission_date = ''
date = datetime.now()
arrdf = [
        {"designation": "DIRECTION", "Nom": '', "Prénom": '', "fonction": '', "Tel": '', "@": '' },
        {"designation": "ACHATS", "Nom": '', "Prénom": '', "fonction": '', "Tel": '', "@": '' },
        {"designation": "STEWARDING", "Nom": '', "Prénom": '', "fonction": '', "Tel": '', "@": '' },
        {"designation": "LIVRAISON", "Nom": '', "Prénom": '', "fonction": '', "Tel": '', "@": '' },
        {"designation": "COMPTABILITÉ", "Nom": '', "Prénom": '', "fonction": '', "Tel": '', "@": '' }
    ]


# Google Sheets setup
if all( map(lambda l: l in list(st.session_state.keys()),['gdrivesetup']) ):
    scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA =  st.session_state['gdrivesetup'] 
    st.session_state['gdrivesetup'] = [scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA]
    if len(dataSubmission)==0:
        no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in  = [ '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'False', '', '', '']
    else:
        submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in = dataSubmission[2:20]+dataSubmission[45:50]

    if date_in:
        date = parse(date_in)
else:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    gauth = GoogleAuth()
    gauth.credentials  = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(gauth.credentials)

    drive = GoogleDrive(gauth)
    sheet_id = sheetId  # Replace with your actual Google Sheet ID
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)
    IdDValues = worksheet.col_values(1)

    if currentID in IdDValues:
        editIndex = IdDValues.index(currentID)+1
        dataSubmission = worksheet.row_values(editIndex)
        IsEdit = True
        #arrdf
        submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in = dataSubmission[2:20]+dataSubmission[45:50]
        i=0
        for ak in arrdf:
            j=0
            for akk in list(ak.keys()):
                if j>0:
                    ak[akk] = dataSubmission[20:45][i]
                    i+=1
                j=+1
        if date_in:
            date = parse(date_in)
        if uploadedpdf_in:
            files = drive.ListFile({'q': "'"+UploadPDFfolder+"' in parents and trashed=false"}).GetList()
            fileA = []
            for uploadedpdfItem in files:
                if uploadedpdfItem['id'] in uploadedpdf_in.split(','):
                    #metadata = dict( id = uploadedpdfItem )
                    fileA.append({ 'gid':uploadedpdfItem['id'], 'gname':uploadedpdfItem['title'],'uname':uploadedpdfItem['title'][:-33]})
            st.session_state['uploadedpdf'] = fileA
        if uploadedsign_in:
            st.session_state['uploadedsign'] = uploadedsign_in
        #print(uploadedpdf_in,date_in,uploadedsign_in)
    else:
        uploadedsign_in = ''
        fileA = []
        no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in  = [ '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'False', '', '', '']

    st.session_state['gdrivesetup'] = [scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA]

def send_email(sender_email, sender_password, recipient_email, subject, body):
    try:
        # Create a MIME object
        message = MIMEMultipart('alternative')
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        # Attach the body to the message
        message.attach(MIMEText(body, 'html'))
        im = MIMEImage(open("logo-white.svg", 'rb').read(),_subtype=False, name=os.path.basename("logo-white.svg"))
        im.add_header('Content-ID', 'logo-white.svg')
        message.attach(im)
        #message.attach(MIMEMultipart())
        # Establish a secure session with Gmail's outgoing SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Log in with app password
            text = message.as_string()
            #server.sendmail()
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

#options_data = fetch_options(sheet, "soumission de formulaire")


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

col1, col2 = st.columns([3,1])  
with col1:
    st.title(Heading)

with col2:
    st.image("logo-white.svg", width=200)

# Streamlit form
form = st.form(key='my_form')


r2col1, r2col2 = form.columns(2)  
# Basic information inputs with clear labels
no_de_compete = r2col1.text_input("N° DE COMPTE",no_de_compete, help="Entrez les 6 premiers chiffres de votre numéro de compte.") # Account No
establissement = r2col1.text_input("ÉTABLISSEMENT",establissement, help="Nom de l'établissement bancaire.") # Bank Establishment
pays = r2col1.text_input("PAYS",pays, help="Pays de résidence.") # country

siret = r2col2.text_input("SIRET",siret, help="Numéro SIRET à 14 chiffres.") # SIRET
tva_europeen_FR = r2col2.text_input("TVA EUROPEEN : FR",tva_europeen_FR, help="Numéro de TVA intracommunautaire (11 chiffres).") # EUROPEAN VAT:Intracommunity VAT number (11 digits)
r2col2.caption("(pour Union Européenne uniquement)")

line_seperator=form.divider()

r3col1, r3col2 = form.columns(2)  

livraison = r3col1.caption("LIVRAISON")
nom = r3col1.text_input("Nom :",nom, help="") 
adresse = r3col1.text_input("Adresse :",adresse, help="") 
code_postal = r3col1.text_input("Code Postal :",code_postal, help="")
ville = r3col1.text_input("Ville :",ville, help="")
livraisonpays = r3col1.text_input("Pays :",pays, help="")

facturation = r3col2.caption("FACTURATION (si différente)")
societe = r3col2.text_input("SOCIÉTÉ :",societe, help="") 
facturation_adresse = r3col2.text_input("Adresse :",facturation_adresse,key="Adresse2" , help="") 
facturation_code_postal = r3col2.text_input("Code Postal :",facturation_code_postal,key="CodePostal2" ,help="")
facturation_ville = r3col2.text_input("Ville :",facturation_ville,key="Ville2" ,help="")

if envoi_des_factures:
    envoi_des_factures = r3col2.pills('Envoi des factures :',
                  ['Courrier',
                   'Email',
                   'Chorus',
                   'Autre'],default=envoi_des_factures, selection_mode="single",key="envoi_des_factures")
else:
    envoi_des_factures = r3col2.pills('Envoi des factures :',
                  ['Courrier',
                   'Email',
                   'Chorus',
                   'Autre'],selection_mode="single",key="envoi_des_factures")
mail_factures = r3col2.text_input("MAIL FACTURES :",mail_factures,key="mailfactures" ,help="")
                   

line_seperator2=form.divider()



edited_df = form.data_editor(
    pd.DataFrame(arrdf),
    column_config={
        "designation": "désignation"
    },
    disabled=["designation"],
    hide_index=True,
    key="de",
    use_container_width=True
)

if not 'uploadedpdf' in st.session_state.keys():
    st.session_state['uploadedpdf'] = []

if len(fileA)>0:
    isRemovedFiles = form.checkbox("remove "+str(len(fileA))+" files uploaded already.",len(fileA)>0)
    if not isRemovedFiles:
        fileA = []
        st.session_state['uploadedpdf'] = []
        cache = st.session_state['gdrivesetup']
        cache[-1] = []
        st.session_state['gdrivesetup'] = cache
else:
    uploaded_files = form.file_uploader(
      "JOINDRE 1 K-BIS - 3 mois et un RIB", accept_multiple_files=True
    )
    for uploaded_file in uploaded_files:
        uploadedInfo = next(filter(lambda up:up['uname']==uploaded_file.name,list(st.session_state['uploadedpdf'])),None)
        if uploadedInfo is None:
            bytes_data = uploaded_file.read()
            fname = uploaded_file.name+"-"+generate_random_uid()
            gfile = drive.CreateFile({"parents": [{'id': UploadPDFfolder}], "title": fname, 'mimeType':uploaded_file.type})
            with open('uploads/'+fname, "wb") as binary_file:
                binary_file.write(bytes_data)
            gfile.SetContentFile('uploads/'+fname)
            try:
                gfile.Upload()
            finally:
                gfile.content.close()
        
            if gfile.uploaded:
                li = st.session_state['uploadedpdf']
                li.append({ 'gid':gfile['id'], 'gname':fname,'uname':uploaded_file.name})
                st.session_state['uploadedpdf'] = li
                os.remove('uploads/'+fname)
                st.toast(f"Fichier téléchargé.")

accpeted=form.checkbox("J’accepte les conditions générales de ventes dont un exemplaire m’a été remis (fourni avec chaque devis ou proforma)",str(accpeted).lower()=='true')

line_seperator3=form.divider()

form.caption("LE CLIENT")
r4col1, r4col2 = form.columns(2)  

representePar = r4col1.text_input("Représenté par",representePar)
with form:
    # Create a canvas component
    canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            stroke_width=3,
            stroke_color='#000000',
            background_color="#EEEEEE",
            background_image=None,
            update_streamlit=True,
            height=200,
            drawing_mode='freedraw',
            point_display_radius=0,
            #display_toolbar=False,
            key="full_app",
        )
date = r4col1.date_input("Date",date)

visadirection1 = r4col2.caption("VISA DIRECTION")
visadirection2 = r4col2.caption("MAISON LEJEUNE")

submit_button = form.form_submit_button(label='Submit')

def getEmail(submittedData,tmp):
    tmp2=tmp.replace("{"+str(45)+"}",str(datetime.now().year))
    for i,v in enumerate(submittedData):
        if i>=4:
            tmp2 =tmp2.replace("{"+str(i-4)+"}",str(v))
    return tmp2


output = io.BytesIO()
dd = json.loads(edited_df.to_json())
dfdata = [x for xs in list(map(lambda kv:[dd['Nom'][kv[0]],dd['Prénom'][kv[0]],dd['fonction'][kv[0]],dd['Tel'][kv[0]],dd['@'][kv[0]]] ,dd['designation'].items())) for x in xs]
submission_data = [currentID,'https://ouverture-de-compte-pro-maison-lejeune.streamlit.app/?edit='+currentID,submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures]+dfdata+[','.join(list(map(lambda g:g['gid'],st.session_state['uploadedpdf']))),accpeted,representePar,date.strftime("%Y-%m-%d %H:%M:%S"),'']#st.session_state['uploadedsign']

pisa.CreatePDF(
    getEmail(submission_data,open("htmltemplate.tmp", "r").read()),  # page data
    dest=output,                                              # destination "file"
)
st.download_button('Download PDF', output.getbuffer().tobytes(), file_name='example.pdf', mime='application/pdf')

# Submit button
if submit_button:
    if all( map(lambda l: l in list(st.session_state.keys()),['uploadedpdf']) ) and len(st.session_state['uploadedpdf'])>0 and accpeted:
    
        # Upload Image
        # Signature Upload
        if canvas_result.image_data is not None and len(canvas_result.image_data[canvas_result.image_data<238])>0:
            fname = currentID+" - sign - "+generate_random_uid()+".jpg"
            gfile = drive.CreateFile({"parents": [{'id': UploadSignfolder}], "title": fname})
            drawing = Image.fromarray((canvas_result.image_data).astype(np.uint8))
            drawing.convert('RGB').save('uploads/'+fname)
            gfile.SetContentFile('uploads/'+fname)
            try:
                gfile.Upload()
            finally:
                gfile.content.close()
        
            if gfile.uploaded:
                st.session_state['uploadedsign'] = gfile['id']
                os.remove('uploads/'+fname)
                st.toast(f"signature terminée")
            # Add current date and time to the data
        elif uploadedsign_in:
            st.session_state['uploadedsign'] = uploadedsign_in

    if all( map(lambda l: l in list(st.session_state.keys()),['uploadedsign','uploadedpdf']) ) and len(st.session_state['uploadedpdf'])>0 and accpeted:
        if not IsEdit:
            submission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            edit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dd = json.loads(edited_df.to_json())
        dfdata = [x for xs in list(map(lambda kv:[dd['Nom'][kv[0]],dd['Prénom'][kv[0]],dd['fonction'][kv[0]],dd['Tel'][kv[0]],dd['@'][kv[0]]] ,dd['designation'].items())) for x in xs]
        submission_data = [currentID,'https://ouverture-de-compte-pro-maison-lejeune.streamlit.app/?edit='+currentID,submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures]+dfdata+[','.join(list(map(lambda g:g['gid'],st.session_state['uploadedpdf']))),accpeted,representePar,date.strftime("%Y-%m-%d %H:%M:%S"),st.session_state['uploadedsign']]
        emailSub="Form Submitted"
        if IsEdit:
            emailSub="Form Edited"
            #worksheet.update(submission_data,range_name= 'A'+str(editIndex+1)+':AX'+str(editIndex+1))
            worksheet.update('A'+str(editIndex),[submission_data])
        else:
            worksheet.append_row(submission_data)
        send_email(secret_config["EmailSender"],secret_config["EmailPass"],secret_config["EmailRecieve"],emailSub,getEmail(submission_data,open("pdftemplate.tmp", "r").read()))  
        st.success("Form submitted successfully!")
