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
from email.mime.base import MIMEBase
from email import encoders
from xhtml2pdf.files import getFile, pisaFileObject
import webbrowser

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
    EmailRecieve =  secret_config["EmailRecieve"]
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
     display: none;
}
 </style>
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)
fileA = []
fileB = []
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
    scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA,fileB =  st.session_state['gdrivesetup'] 
    st.session_state['gdrivesetup'] = [scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA,fileB]
    if len(dataSubmission)==0:
        no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in,uploadedstamp_in  = [ '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'False', '', '', '','']
    else:
        submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in,uploadedstamp_in = dataSubmission[2:20]+dataSubmission[45:51]

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
        submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in,uploadedstamp_in = dataSubmission[2:20]+dataSubmission[45:51]
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
            
        if uploadedstamp_in:
            files = drive.ListFile({'q': "'"+UploadPDFfolder+"' in parents and trashed=false"}).GetList()
            fileB = []
            for uploadedstamppdfItem in files:
                if uploadedstamppdfItem['id'] in uploadedstamp_in.split(','):
                    #metadata = dict( id = uploadedpdfItem )
                    fileB.append({ 'gid':uploadedstamppdfItem['id'], 'gname':uploadedstamppdfItem['title'],'uname':uploadedstamppdfItem['title'][:-33]})
            st.session_state['uploadedstamps'] = fileB
        
        if uploadedsign_in:
            st.session_state['uploadedsign'] = uploadedsign_in
        #print(uploadedpdf_in,date_in,uploadedsign_in)
    else:
        uploadedsign_in = ''
        fileA = []
        fileB = []
        no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures,uploadedpdf_in,accpeted,representePar,date_in,uploadedsign_in,uploadedstamp_in  = [ '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'False', '', '', '','']

    st.session_state['gdrivesetup'] = [scope,gauth,client,drive,sheet_id,sheet,worksheet,IdDValues,IsEdit,editIndex,edit_date,submission_date,dataSubmission,uploadedsign_in,arrdf,fileA,fileB]

def send_email(sender_email, sender_password, recipient_email, subject, body):
    try:
        # Create a MIME object
        message = MIMEMultipart('alternative')
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        # Attach the body to the message
        message.attach(MIMEText(body, 'html'))
        im = MIMEImage(open("logo-white.jpg", 'rb').read(),  name=os.path.basename("logo-white.jpg"))
        im.add_header('Content-ID', '<logo-white.jpg>')
        message.attach(im)

        uploadedsign = st.session_state['uploadedsign'] 
        if uploadedsign:  
            file6 = drive.CreateFile({'id': uploadedsign}) 
            file6.GetContentFile('uploads/'+uploadedsign+'.jpg')
            im2 = MIMEImage(open('uploads/'+uploadedsign+'.jpg', 'rb').read(), name=os.path.basename("signature.jpg"))
            im2.add_header('Content-ID', '<signature.jpg>')
            message.attach(im2)
            os.remove('uploads/'+uploadedsign+'.jpg')
        
        #with open('uploads/'+currentID+'signature.jpg', "rb") as attachment:
            # Create a MIMEBase object
            part = MIMEBase("application", "octet-stream")
            part.set_payload(output.getbuffer().tobytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", 'attachment', filename=os.path.basename(Heading+".pdf")
               # f"attachment; filename= {os.path.basename(attachment.name)}",
            )
            message.attach(part)
        #message.attach(MIMEText(open("./static/conditions-générales-de-vente.pdf", encoding="utf8").read()))
        for upedfile in st.session_state['uploadedpdf']:
            upfile = drive.CreateFile({'id': upedfile['gid']}) 
            upfile.GetContentFile('uploads/'+upedfile['uname'])
            if upedfile['uname'].lower().endswith(".pdf"):
                with open('uploads/'+upedfile['uname'], "rb") as attachment2:
                    part2 = MIMEBase("application", "octet-stream")
                    part2.set_payload(attachment2.read())
                    encoders.encode_base64(part2)
                    part2.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {os.path.basename(attachment2.name)}",
                    )
                    message.attach(part2)
            else:
                message.attach(MIMEImage(open('uploads/'+upedfile['uname']).read()))
            os.remove('uploads/'+upedfile['uname'])

        
        for upedfile in st.session_state['uploadedstamps']:
            upfile = drive.CreateFile({'id': upedfile['gid']}) 
            upfile.GetContentFile('uploads/'+upedfile['uname'])
            if upedfile['uname'].lower().endswith(".png"):
                with io.BytesIO() as f:
                    Image.open('uploads/'+upedfile['uname'], mode='r', formats=None).convert('RGB').save(f,format="JPEG")
                    im2 = MIMEImage(f.getvalue(), name=os.path.basename(upedfile['uname'].lower().replace('.png','.jpg')))
                    im2.add_header('Content-ID', '<stamp.jpg>')
                    message.attach(im2)
            elif upedfile['uname'].lower().endswith(".jpg"):
                
                with open('uploads/'+upedfile['uname'], "rb") as attachment2:
                    
                    im2 = MIMEImage(open('uploads/'+uploadedsign+'.jpg', 'rb').read(), name=os.path.basename(attachment2.name))
                    
                    im2.add_header('Content-ID', '<stamp.jpg>')
                    message.attach(im2)
                    
                    break
            else:
                st.write(11,'uploads/'+upedfile['uname'])
                message.attach(MIMEImage(open('uploads/'+upedfile['uname'],'rb').read(), name=os.path.basename(attachment2.name)))
            
            os.remove('uploads/'+upedfile['uname'])
            
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
                   'Autre'],default=envoi_des_factures.split(','), selection_mode="multi",key="envoi_des_factures")
else:
    envoi_des_factures = r3col2.pills('Envoi des factures :',
                  ['Courrier',
                   'Email',
                   'Chorus',
                   'Autre'],selection_mode="multi",key="envoi_des_factures")


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
        cache[-2] = []
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
                st.toast(f"fichier téléchargé avec succès.")

accpeted=form.checkbox("J’accepte les conditions générales de ventes dont un exemplaire m’a été remis (fourni avec chaque devis ou proforma)",str(accpeted).lower()=='true')
form.write('<a href="https://www.lejeune.tm.fr/CGV.pdf">conditions générales de ventes</a>', unsafe_allow_html = True)

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
            background_image=None, #'uploads/'+currentID+'signature.jpg'
            update_streamlit=True,
            height=200,
            drawing_mode='freedraw',
            point_display_radius=0,
            display_toolbar=True,
            key="full_app",
        )
    
    #down_button = form.form_submit_button(label="download")
    #if down_button:
    #    a = 1

date = r4col1.date_input("Date",date)

visadirection1 = r4col2.caption("VISA DIRECTION")
visadirection2 = r4col2.caption("MAISON LEJEUNE")

def getEmail(submittedData,tmp):
    tmp2=tmp.replace("{"+str(45)+"}",str(datetime.now().year))
    for i,v in enumerate(submittedData):
        if i>=4:
            tmp2 =tmp2.replace("{"+str(i-4)+"}",str(v))
    return tmp2
pisaFileObject.getNamedFile = lambda self: self.uri

output = io.BytesIO()
dd = json.loads(edited_df.to_json())
dfdata = [x for xs in list(map(lambda kv:[dd['Nom'][kv[0]],dd['Prénom'][kv[0]],dd['fonction'][kv[0]],dd['Tel'][kv[0]],dd['@'][kv[0]]] ,dd['designation'].items())) for x in xs]
if 'uploadedsign' in st.session_state.keys():
    file6 = drive.CreateFile({'id': st.session_state['uploadedsign']}) 
    file6.GetContentFile('uploads/'+currentID+'signature.jpg')





if not 'uploadedstamps' in st.session_state.keys():
    st.session_state['uploadedstamps'] = []

if len(fileB)>0:
    isRemovedFiles2 = form.checkbox("remove "+str(len(fileB))+" stamps files uploaded already.",len(fileB)>0)
    if not isRemovedFiles2:
        fileB = []
        st.session_state['uploadedstamps'] = []
        cache = st.session_state['gdrivesetup']
        cache[-1] = []
        st.session_state['gdrivesetup'] = cache
    else:
        file6 = drive.CreateFile({'id': st.session_state['uploadedstamps'][0]['gid']}) 
        file6.GetContentFile('uploads/'+currentID+'stamp.jpg')
else:
    uploaded_stamps = form.file_uploader(
      "mettre un upload du cachet de l'entreprise + un upload d'un KBIS ou registre de commerce", accept_multiple_files=True
    )
    for uploaded_stamps_file in uploaded_stamps:
        uploaded_stamps_Info = next(filter(lambda up:up['uname']==uploaded_stamps_file.name,list(st.session_state['uploadedstamps'])),None)
        if uploaded_stamps_Info is None:
            bytes_data = uploaded_stamps_file.read()
            fname = uploaded_stamps_file.name+"-"+generate_random_uid()
            gfile = drive.CreateFile({"parents": [{'id': UploadPDFfolder}], "title": fname, 'mimeType':uploaded_stamps_file.type})
            with open('uploads/'+fname, "wb") as binary_file:
                binary_file.write(bytes_data)
            gfile.SetContentFile('uploads/'+fname)
            try:
                gfile.Upload()
            finally:
                gfile.content.close()
        
            if gfile.uploaded:
                li = st.session_state['uploadedstamps']
                li.append({ 'gid':gfile['id'], 'gname':fname,'uname':uploaded_stamps_file.name})
                st.session_state['uploadedstamps'] = li
                os.remove('uploads/'+fname)
                st.toast(f"fichiers de tampons téléchargés avec succès.")



submit_button = form.form_submit_button(label="envoyer ma demande d'ouverture")
submission_data = [currentID,'https://ouverture-de-compte-pro-maison-lejeune.streamlit.app/?edit='+currentID,submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,envoi_des_factures,mail_factures]+dfdata+[','.join(list(map(lambda g:g['gid'],st.session_state['uploadedpdf']))),accpeted,representePar,date.strftime("%Y-%m-%d %H:%M:%S"),'',','.join(list(map(lambda g:g['gid'],st.session_state['uploadedstamps'])))]#st.session_state['uploadedsign']

pdfinfo = getEmail(submission_data, open("pdftemplate.tmp", "r").read()).replace('src="signature.jpg"','src="uploads/'+currentID+'signature.jpg"').replace('src="stamp.jpg"','src="uploads/'+currentID+'stamp.jpg"')
pisa.CreatePDF(pdfinfo,
     # page data
    dest=output, encoding='UTF-8'                                              # destination "file"
)
st.download_button('Download PDF', output.getbuffer().tobytes(), file_name=Heading+'.pdf', mime='application/pdf')

if os.path.isfile('uploads/'+currentID+'signature.jpg'):
    st.download_button('Download Signature', data=open('uploads/'+currentID+'signature.jpg','rb').read(), file_name=Heading+' Sign.jpg')

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
        submission_data = [currentID,'https://ouverture-de-compte-pro-maison-lejeune.streamlit.app/?edit='+currentID,submission_date,edit_date,no_de_compete,establissement,pays,siret,tva_europeen_FR,nom,adresse,code_postal,ville,livraisonpays,societe,facturation_adresse,facturation_code_postal,facturation_ville,','.join(list(envoi_des_factures)),mail_factures]+dfdata+[','.join(list(map(lambda g:g['gid'],st.session_state['uploadedpdf']))),accpeted,representePar,date.strftime("%Y-%m-%d %H:%M:%S"),st.session_state['uploadedsign'],','.join(list(map(lambda g:g['gid'],st.session_state['uploadedstamps'])))]   
        emailSub="Form Submitted"
        if IsEdit:
            emailSub="Form Edited"
            #worksheet.update(submission_data,range_name= 'A'+str(editIndex+1)+':AX'+str(editIndex+1))
            worksheet.update('A'+str(editIndex),[submission_data])
        else:
            worksheet.append_row(submission_data)
            #mail_factures
        send_email(secret_config["EmailSender"],secret_config["EmailPass"],EmailRecieve,emailSub,getEmail(submission_data,open("htmltemplate.tmp", "r").read()))  
        st.success("Form submitted successfully!")
        webbrowser.open(submission_data[1], new = 0)
        if IsEdit:
            scriptrun="window.location.reload();"
        else:
            scriptrun='location.origin+location.pathname+"??edit='+currentID+';'
        st.markdown(
            """
            <div id="div"></div>
            <script>
                """+scriptrun+"""

            </script>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("formulaire non remis, veillez à signer, JOINDRE 1 K-BIS - 3 mois et un RIB dûment remis. L'acceptation des conditions générales de vente est également requise.")
