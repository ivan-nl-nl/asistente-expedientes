"""Interfaz de demostración del asistente de expedientes."""

from datetime import date
from pathlib import Path

import streamlit as st

from expedientes import STATES, export_csv, filter_records, read_csv, read_excel

st.set_page_config(page_title="Expedientes | Control documental", page_icon="📁", layout="wide")
st.title("📁 Control de expedientes")
st.caption("Importa, revisa y encuentra expedientes antes de que venzan.")
st.info("Demo de portafolio con datos ficticios. No cargues información personal ni documentos institucionales.")

with st.sidebar:
    st.header("Origen de los datos")
    demo = st.checkbox("Usar datos de demostración", value=True)
    uploaded = st.file_uploader("Importar archivo", type=["csv", "xlsx"], disabled=demo)
    st.caption("Columnas: numero, asunto, estado, fecha_ingreso, fecha_vencimiento. Fechas: AAAA-MM-DD. Excel: primera hoja.")
    today = st.date_input("Fecha de referencia", value=date.today())
    st.caption("Vencido: fecha anterior a la referencia y estado distinto de finalizado.")
    sample = Path(__file__).parent / "data" / "expedientes_demo.csv"
    st.download_button("Descargar CSV de ejemplo", sample.read_bytes(), "expedientes_demo.csv", "text/csv")

if not demo and uploaded is None:
    st.warning("Selecciona un archivo CSV o Excel para comenzar.")
    st.stop()

try:
    if demo:
        result = read_csv(sample.read_bytes())
    elif uploaded.name.lower().endswith(".xlsx"):
        result = read_excel(uploaded.getvalue())
    else:
        result = read_csv(uploaded.getvalue())
except Exception as error:
    st.error(f"No se pudo importar el archivo: {error}")
    st.stop()

records = result.expedientes
a, b, c, d = st.columns(4)
a.metric("Filas revisadas", result.total_filas)
b.metric("Expedientes válidos", len(records))
c.metric("Filas con incidencias", len(result.incidencias))
d.metric("Vencidos", sum(record.vencido(today) for record in records))

if result.incidencias:
    with st.expander(f"Revisar {len(result.incidencias)} filas excluidas"):
        st.caption("Se conserva la primera fila válida de cada número. Las filas con errores se excluyen; corrige el archivo y vuelve a cargarlo.")
        st.dataframe([{"Fila": item.fila, "Número": item.numero, "Detalle": item.detalle}
                      for item in result.incidencias], use_container_width=True, hide_index=True)

st.subheader("Consulta de expedientes")
left, middle, right = st.columns([2, 1, 1])
query = left.text_input("Buscar por número o asunto", placeholder="Ej.: DEMO-001 o mantenimiento")
state = middle.selectbox("Estado", ["Todos", *STATES])
due = right.selectbox("Vencimiento", ["Todos", "Vencidos", "Próximos 7 días"])
filtered = filter_records(records, query, state, due, today)
st.caption(f"{len(filtered)} de {len(records)} expedientes válidos · ordenados por vencimiento")
if filtered:
    st.dataframe([{
        "Número": record.numero, "Asunto": record.asunto, "Estado": record.estado,
        "Ingreso": record.fecha_ingreso.isoformat(), "Vencimiento": record.fecha_vencimiento.isoformat(),
        "Plazo": "Finalizado" if record.estado == "finalizado" else "Vencido" if record.vencido(today)
        else "Vence hoy" if record.fecha_vencimiento == today else f"En {(record.fecha_vencimiento - today).days} días",
    } for record in filtered], use_container_width=True, hide_index=True)
else:
    st.warning("No hay expedientes que coincidan con estos filtros.")
st.download_button("Exportar resultados", export_csv(filtered), "expedientes_filtrados.csv", "text/csv")
st.caption("Los archivos se procesan en memoria. Esta versión no tiene base de datos, cuentas ni conexión a sistemas municipales.")
