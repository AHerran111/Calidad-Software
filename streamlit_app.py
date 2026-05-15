import streamlit as st

from utils.server_control import start_infrastructure, stop_infrastructure


st.set_page_config(
    page_title="Sistema CFDI",
    page_icon="🧾",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 20px;
        color: #666;
        margin-top: 0;
        margin-bottom: 30px;
    }


    div.stButton > button {
        height: 70px;
        font-size: 22px;
        font-weight: 700;
        border-radius: 14px;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🧾 Sistema de Facturación CFDI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Aplicación para crear, administrar, consultar y timbrar facturas electrónicas CFDI 4.0.</p>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="status-card">
        <h3>Descripción general</h3>
        <p>
        Esta plataforma permite gestionar el flujo completo de facturación electrónica:
        creación de CFDI, administración de emisores y receptores, generación de XML,
        almacenamiento en PostgreSQL, envío al servidor PAC y actualización del estado
        de las facturas timbradas.
        </p>
        <p>
        El sistema está integrado con servicios desplegados en DigitalOcean y utiliza
        un backend PAC desarrollado con FastAPI para validar y procesar los XML.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.info("📄 Crear facturas CFDI desde formulario o CSV.")

with col2:
    st.info("✅ Timbrar facturas pendientes mediante el PAC.")

with col3:
    st.info("📊 Consultar facturas por estado, RFC y fecha.")

st.divider()

st.header("Control de infraestructura")

st.warning(
    "Usa estos botones para encender o apagar los servicios asociados a la aplicación. En caso de dar error al acceder los modulos y tener prendida la aplicación, recargar la pagina y volver a intentar"
)

col_on, col_off = st.columns(2)

with col_on:
    if st.button("🟢 PRENDER APLICACIÓN", type="primary"):
        try:
            start_infrastructure()
            st.success("Solicitud enviada: la infraestructura se está encendiendo. Espera 1 minuto por favor.")
        except Exception as e:
            st.error(f"Error al prender la aplicación: {e}")

with col_off:
    if st.button("🔴 APAGAR APLICACIÓN"):
        try:
            stop_infrastructure()
            st.success("Solicitud enviada: la infraestructura se está apagando.")
        except Exception as e:
            st.error(f"Error al apagar la aplicación: {e}")

st.divider()

st.sidebar.success("Selecciona una página del menú.")

st.markdown(
    """
    ### Módulos disponibles

    - **Crear Factura:** captura de datos fiscales, conceptos, totales y generación XML.
    - **Timbrar Factura:** envío de facturas pendientes al servidor PAC.
    - **Facturas:** consulta y filtrado de facturas almacenadas.
    - **Catálogos:** administración de emisores y receptores.
    """
)

st.success("Expande el menu ubicado a la izquierda para acceder a los modulos")