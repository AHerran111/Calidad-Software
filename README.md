# 🧾 Calidad-Software — Plataforma CFDI 4.0

Sistema distribuido de facturación electrónica CFDI 4.0 desarrollado con Streamlit, FastAPI y PostgreSQL. El proyecto implementa generación, administración y timbrado de facturas electrónicas XML compatibles con el estándar CFDI 4.0 del SAT, integrando pruebas automatizadas, CI/CD y métricas de calidad de software.

---

# 🚀 Tecnologías Utilizadas

- Python 3.11
- Streamlit
- FastAPI
- PostgreSQL
- GitHub Actions
- SonarCloud
- Pytest
- Ruff
- k6
- OWASP ZAP
- DigitalOcean

---

# ☁️ Infraestructura

La solución se encuentra desplegada en DigitalOcean utilizando 3 Droplets:

| Servicio | Descripción |
|---|---|
| PostgreSQL Cliente | Base de datos para Streamlit |
| PostgreSQL PAC | Base de datos para el servidor PAC |
| API PAC | API FastAPI para validación y timbrado |

---

# 📦 Arquitectura del Proyecto

El repositorio principal:

```text
Calidad-Software
```

contiene:

- Aplicación cliente Streamlit
- Generación CFDI
- Generación XML
- Administración de emisores y receptores
- Integración PAC
- Automatización de pruebas
- Integración continua
- Métricas de calidad

Dentro del proyecto existe un módulo adicional:

```text
pac_server_repo/
```

Este módulo corresponde al servidor PAC desarrollado con FastAPI.

---

# 🔄 Despliegue Automático

El servidor PAC está conectado mediante un Git Hook.

Cada vez que se realiza un push hacia:

```text
main
```

el servidor automáticamente:

1. Actualiza el repositorio
2. Descarga la nueva versión
3. Reinicia el servicio FastAPI

---

# 🧾 Funcionalidades

## Cliente Streamlit

- Creación de facturas CFDI 4.0
- Generación XML
- Firma CFDI simulada
- Administración de emisores
- Administración de receptores
- Consulta de facturas
- Timbrado de facturas
- Descarga XML timbrado
- Carga masiva CSV
- Control de infraestructura DigitalOcean

---

## Servidor PAC

- Validación XML
- Validación CFDI
- Validación impuestos
- Validación de totales
- Simulación de timbrado SAT
- Persistencia PostgreSQL

---

# 📊 Flujo General

```text
Usuario
   │
   ▼
Aplicación Streamlit
   │
   ├── Generación CFDI
   ├── Firma XML
   ├── Persistencia PostgreSQL
   │
   ▼
PAC API (FastAPI)
   │
   ├── Parse XML
   ├── Validación CFDI
   ├── Validación impuestos
   ├── Timbrado
   └── Persistencia PAC
   │
   ▼
XML Timbrado
```

---

# 📄 Flujo de Creación de Factura

```text
Usuario
   │
   ▼
Página "Crear Factura"
   │
   ├── Captura datos CFDI
   ├── Captura conceptos
   ├── Cálculo de impuestos
   ├── Cálculo de totales
   │
   ▼
services/cfdi_generator.py
   │
   ▼
services/signer_mock.py
   │
   ▼
utils/xml_utils.py
   │
   ▼
Generación XML CFDI
   │
   ▼
utils/database.py
   │
   ▼
PostgreSQL Cliente
   │
   ▼
Factura almacenada como PENDIENTE
```

---

# 📑 Flujo de Timbrado

```text
Usuario
   │
   ▼
Página "Timbrar Factura"
   │
   ▼
Consulta facturas pendientes
   │
   ▼
PostgreSQL Cliente
   │
   ▼
Obtención XML CFDI
   │
   ▼
services/pac_api.py
   │
   ▼
PAC API FastAPI
   │
   ├── Parse XML
   ├── Validación CFDI
   ├── Validación impuestos
   ├── Simulación timbrado
   └── Persistencia PAC
   │
   ▼
PostgreSQL PAC
   │
   ▼
Respuesta XML Timbrado
   │
   ▼
Actualización factura → TIMBRADO
```

---

# 🧪 Calidad de Software

El proyecto implementa:

- Pruebas unitarias con Pytest
- Cobertura automática
- Ruff Linter
- SonarCloud
- GitHub Actions CI/CD
- Quality Gates
- Pruebas de carga con k6
- Validación de APIs con OWASP ZAP

---

# ⚙️ Integración Continua (CI/CD)

GitHub Actions ejecuta automáticamente:

- Instalación de dependencias
- Ejecución de pruebas unitarias
- Cobertura de código
- Validación de calidad
- Quality Gates
- Verificación de linting

---

# 📂 Estructura del Proyecto

```text
.
├── .github/workflows/     # GitHub Actions
├── pac_server_repo/       # API PAC FastAPI
├── pages/                 # Páginas Streamlit
├── services/              # Servicios CFDI
├── tests/                 # Pruebas unitarias y carga
├── utils/                 # Utilidades y acceso BD
├── streamlit_app.py       # Página principal
├── requirements.txt
├── pyproject.toml
└── ruff.toml
```

---

# 🛠️ Instalación Local

## 1. Clonar repositorio

```bash
git clone https://github.com/<usuario>/Calidad-Software.git
cd Calidad-Software
```

---

## 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 3. Configurar secrets

Crear:

```text
utils/secrets.toml
```

Ejemplo:

```toml
[database]
host = "localhost"
dbname = "cfdi"
user = "postgres"
password = "postgres"
port = 5432
```

---

## 4. Ejecutar Streamlit

```bash
streamlit run streamlit_app.py
```

---

# 🧪 Ejecutar pruebas

```bash
pytest tests/py_test.py -v
```

Con cobertura:

```bash
pytest tests/py_test.py -v \
--cov=services \
--cov=utils \
--cov-report=term-missing
```

---

# 📈 Pruebas de carga

```bash
k6 run tests/load_test.js
```

---

# 🔐 Seguridad

El proyecto incluye:

- Validación XML
- Validación CFDI
- SQL parametrizado
- Integración OWASP ZAP
- Métricas SonarCloud

---

# 📊 Calidad y Métricas

## Métricas de Producto

- Cobertura de pruebas
- Maintainability Index
- Densidad de defectos

Herramienta utilizada:

- SonarCloud

---

## Métricas de Proceso

- Lead Time
- Defect Escape Rate

Herramientas:

- Jira
- GitHub Actions

---

## Auditorías Internas

- Checklist basado en ISO 9001
- Validación de cumplimiento
- Revisión de estándares

---

# ☁️ Control de Infraestructura

La aplicación permite:

- Encender Droplets DigitalOcean
- Apagar Droplets DigitalOcean
- Controlar disponibilidad de infraestructura

---

# 👨‍💻 Tecnologías Principales

| Tecnología | Uso |
|---|---|
| Streamlit | Frontend |
| FastAPI | Backend PAC |
| PostgreSQL | Persistencia |
| GitHub Actions | CI/CD |
| SonarCloud | Calidad |
| Pytest | Testing |
| k6 | Load Testing |
| Ruff | Linting |
| DigitalOcean | Infraestructura |

---

# 📄 Licencia

MIT License
