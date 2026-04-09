import streamlit as st
import pandas as pd
import urllib.parse
import base64

# Configuración de la página
st.set_page_config(page_title="RealEstate CRM Pro", layout="wide")

# Estilos personalizados para un look profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .contacted { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Inicialización del estado de la sesión
if 'leads' not in st.session_state:
    st.session_state.leads = pd.DataFrame(columns=['Nombre', 'Teléfono', 'Correo', 'Estado', 'Fuente'])
if 'template' not in st.session_state:
    st.session_state.template = "Hola {nombre}, te contacto desde la inmobiliaria para darte seguimiento."

# Sidebar - Configuración
st.sidebar.title("⚙️ Configuración")
st.session_state.template = st.sidebar.text_area("Plantilla de Mensaje", value=st.session_state.template, height=150)
use_first_name = st.sidebar.checkbox("Usar solo primer nombre", value=True)

# Título principal
st.title("🏠 RealEstate CRM Pro")

# Tabs principales
tab_import, tab_manual = st.tabs(["📥 Importar Excel", "👤 Agregar Manual"])

with tab_import:
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        # Validación básica de columnas
        required = ['Nombre', 'Teléfono', 'Correo electrónico']
        if all(col in df.columns for col in required):
            new_leads = df[required].copy()
            new_leads['Estado'] = 'Nuevo'
            new_leads['Fuente'] = 'Excel'
            st.session_state.leads = pd.concat([st.session_state.leads, new_leads]).drop_duplicates().reset_index(drop=True)
            st.success(f"¡{len(new_leads)} leads importados!")
        else:
            st.error(f"El Excel debe tener las columnas: {', '.join(required)}")

with tab_manual:
    with st.form("manual_form"):
        col1, col2, col3 = st.columns(3)
        m_nombre = col1.text_input("Nombre")
        m_tel = col2.text_input("Teléfono")
        m_correo = col3.text_input("Correo")
        submit = st.form_submit_button("Agregar Lead")
        if submit and m_nombre and m_tel:
            new_row = pd.DataFrame([{'Nombre': m_nombre, 'Teléfono': m_tel, 'Correo': m_correo, 'Estado': 'Nuevo', 'Fuente': 'Manual'}])
            st.session_state.leads = pd.concat([st.session_state.leads, new_row]).reset_index(drop=True)
            st.success("Lead agregado correctamente")

# Buscador
search = st.text_input("🔍 Buscar lead por nombre, teléfono o correo...")

# Filtrado
df_display = st.session_state.leads.copy()
if search:
    df_display = df_display[df_display.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]

# Función para generar vCard
def get_vcard_download_link(name, phone, email):
    vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL;TYPE=CELL:{phone}\nEMAIL:{email}\nEND:VCARD"
    b64 = base64.b64encode(vcard.encode()).decode()
    return f'<a href="data:text/vcard;base64,{b64}" download="{name.replace(" ", "_")}.vcf">📇 vCard</a>'

# Mostrar Leads
st.subheader("📋 Gestión de Leads")
t1, t2 = st.tabs(["🆕 Nuevos", "✅ Contactados"])

def render_table(data, status_filter):
    subset = data[data['Estado'] == status_filter]
    if subset.empty:
        st.info(f"No hay leads {status_filter.lower()}s.")
        return

    for i, row in subset.iterrows():
        cols = st.columns([3, 2, 3, 2, 2])
        # 1. Nombre (Editable)
        new_name = cols[0].text_input(f"Nombre_{i}", value=row['Nombre'], label_visibility="collapsed")
        if new_name != row['Nombre']:
            st.session_state.leads.at[i, 'Nombre'] = new_name
        
        cols[1].write(row['Teléfono'])
        cols[2].write(row['Correo'])
        
        # 2. Botón WhatsApp
        name_to_send = row['Nombre'].split(' ')[0] if use_first_name else row['Nombre']
        msg = st.session_state.template.replace("{nombre}", name_to_send)
        wa_url = f"https://wa.me/{str(row['Teléfono']).replace('+', '')}?text={urllib.parse.quote(msg)}"
        
        if cols[3].button("💬 WhatsApp", key=f"wa_{i}"):
            st.session_state.leads.at[i, 'Estado'] = 'Contactado'
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={wa_url}">', unsafe_allow_html=True)
        
        # 3. vCard y Eliminar
        vcard_link = get_vcard_download_link(row['Nombre'], row['Teléfono'], row['Correo'])
        cols[4].markdown(vcard_link, unsafe_allow_html=True)
        if cols[4].button("🗑️", key=f"del_{i}"):
            st.session_state.leads = st.session_state.leads.drop(i).reset_index(drop=True)
            st.rerun()

with t1:
    render_table(df_display, 'Nuevo')

with t2:
    render_table(df_display, 'Contactado')

# Botón para limpiar todo
if st.sidebar.button("🚨 Eliminar todos los datos"):
    st.session_state.leads = pd.DataFrame(columns=['Nombre', 'Teléfono', 'Correo', 'Estado', 'Fuente'])
    st.rerun()
