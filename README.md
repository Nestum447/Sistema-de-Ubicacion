# 📦 Sistema Automático de Asignación de Productos en Bodega (Con Racks)

Aplicación en **Streamlit** para asignar productos a ubicaciones disponibles dentro de una bodega con racks, tomando en cuenta la **altura útil**, la **disponibilidad de espacio** y el **orden por rack, nivel, fila y posición**.  

El sistema procesa archivos **Excel** de productos y ubicaciones, realiza las asignaciones automáticamente y permite exportar los resultados a un nuevo archivo Excel.

---

## 🚀 Características principales

- Subida de archivos Excel desde la barra lateral:
  - **UBICACIONES.xlsx** → Contiene la estructura de la bodega (racks, niveles, posiciones, alturas, disponibilidad).
  - **PRODUCTOS.xlsx** → Lista de productos con nombre, altura y cantidad en existencia.
- Algoritmo de asignación:
  - Busca la **ubicación más ajustada en altura** para cada producto.
  - Ordena las asignaciones por **Rack → Nivel → Fila → Posición**.
  - Marca las ubicaciones como ocupadas una vez asignadas.
- Resultados:
  - Estado actualizado de las **ubicaciones**.
  - Estado de **productos** (asignados, pendientes, racks asignados, alturas utilizadas).
  - Listado de **ubicaciones asignadas**.
- Exportación de resultados en un solo archivo Excel con 3 hojas:
  - `Asignaciones`
  - `Resumen_Productos`
  - `Ubicaciones_Final`

---

## 🛠️ Tecnologías utilizadas

- [Streamlit](https://streamlit.io/) – Interfaz web interactiva en Python.  
- [Pandas](https://pandas.pydata.org/) – Manipulación de datos.  
- [XlsxWriter](https://xlsxwriter.readthedocs.io/) – Escritura de archivos Excel.  
- [BytesIO](https://docs.python.org/3/library/io.html) – Exportación de archivos en memoria.

---

## 📂 Requisitos de archivos de entrada

### 1. **UBICACIONES.xlsx**
Debe contener al menos las siguientes columnas:

| Rack | Nivel | Fila | Posición | Altura_útil | Disponible |
|------|-------|------|----------|-------------|------------|
| A1   | 1     | 1    | 1        | 120         | TRUE       |
| A1   | 1     | 1    | 2        | 150         | TRUE       |
| B2   | 2     | 1    | 1        | 180         | TRUE       |

---

### 2. **PRODUCTOS.xlsx**
Debe contener al menos las siguientes columnas:

| Producto         | Altura | Existencia |
|------------------|--------|------------|
| Caja pequeña     | 100    | 3          |
| Caja mediana     | 140    | 2          |
| Pallet grande    | 170    | 5          |

---

## 📦 Instalación y uso

1. Clona este repositorio:

   ```bash
   git clone https://github.com/tuusuario/tu-repo.git
   cd tu-repo
