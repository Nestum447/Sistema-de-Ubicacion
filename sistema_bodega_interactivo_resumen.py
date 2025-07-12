
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Sistema de Asignación de Bodega", layout="wide")
st.title("📦 Sistema Automático de Asignación de Productos en Bodega")

# --- 1. Subida de archivos ---
st.sidebar.header("📂 Cargar archivos Excel")

file_ubicaciones = st.sidebar.file_uploader("Cargar ubicaciones.xlsx", type=["xlsx"])
file_productos = st.sidebar.file_uploader("Cargar productos.xlsx", type=["xlsx"])

if file_ubicaciones and file_productos:
    ubicaciones = pd.read_excel(file_ubicaciones)
    productos = pd.read_excel(file_productos)

    # --- 2. Asignar productos a ubicaciones óptimas (altura más ajustada) ---
    asignaciones = []

    for idx, row in productos.iterrows():
        nombre = row["Producto"]
        altura = row["Altura"]
        cantidad = row["Existencia"]
        asignados = 0

        # Filtrar ubicaciones disponibles donde quepa el producto
        ubic_disponibles = ubicaciones[
            (ubicaciones["Disponible"] == True) & 
            (ubicaciones["Altura_útil"] >= altura)
        ]

        # Ordenar por la diferencia mínima entre altura útil y producto
        ubic_disponibles = ubic_disponibles.copy()
        ubic_disponibles["Diferencia"] = ubic_disponibles["Altura_útil"] - altura
        ubic_disponibles = ubic_disponibles.sort_values(by=["Diferencia", "Nivel", "Fila", "Posición"])

        alturas_utilizadas = []
        niveles_asignados = []

        for i, ubic in ubic_disponibles.iterrows():
            if asignados >= cantidad:
                break
            ubicaciones.at[i, "Disponible"] = False
            ubicaciones.at[i, "Producto_asignado"] = nombre
            asignados += 1
            alturas_utilizadas.append(ubic["Altura_útil"])
            niveles_asignados.append(ubic["Nivel"])
            asignaciones.append({
                "Producto": nombre,
                "Nivel": ubic["Nivel"],
                "Fila": ubic["Fila"],
                "Posición": ubic["Posición"],
                "Altura_útil": ubic["Altura_útil"]
            })

        productos.loc[idx, "Asignado"] = asignados
        productos.loc[idx, "Pendiente"] = cantidad - asignados
        productos.loc[idx, "Alturas_útiles"] = ", ".join(map(str, sorted(set(alturas_utilizadas))))
        productos.loc[idx, "Niveles_asignados"] = ", ".join(map(str, sorted(set(niveles_asignados))))

    # --- 3. Mostrar resultados ---
    st.subheader("📊 Estado de las ubicaciones")
    st.dataframe(ubicaciones)

    st.subheader("📦 Estado de productos")
    st.dataframe(productos)

    st.subheader("✅ Ubicaciones asignadas")
    df_asign = pd.DataFrame(asignaciones)
    st.dataframe(df_asign)

    # --- 4. Botón para descargar resultados ---
    st.subheader("⬇️ Exportar asignaciones")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_asign.to_excel(writer, sheet_name="Asignaciones", index=False)
        productos.to_excel(writer, sheet_name="Resumen_Productos", index=False)
        ubicaciones.to_excel(writer, sheet_name="Ubicaciones_Final", index=False)
    output.seek(0)

    st.download_button(
        label="📥 Descargar archivo Excel con resultados",
        data=output,
        file_name="resultado_asignaciones_resumen.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("📑 Por favor carga los archivos de productos y ubicaciones desde la barra lateral.")
