import pandas as pd
import plotly.express as px

# 1. Cargar el archivo CSV
try:
    df = pd.read_csv('Lista_Ventas_Detalle.csv', encoding='latin1', header=1)
except FileNotFoundError:
    print("Error: El archivo 'Lista_Ventas_Detalle.csv' no fue encontrado.")
    exit()

# 2. Definir las columnas clave
columna_fecha = 'FECHA'
columna_articulos = 'ARTICULOS'
columna_cantidad = 'CANTIDAD'
columna_importe = 'IMPORTE EN SOLES'

# 3. Limpiar y preparar los datos
df.columns = df.columns.str.strip()
df[columna_cantidad] = pd.to_numeric(df[columna_cantidad], errors='coerce')
df[columna_importe] = pd.to_numeric(df[columna_importe], errors='coerce')
df[columna_fecha] = pd.to_datetime(df[columna_fecha], format='%d/%m/%Y', errors='coerce')
df.dropna(subset=[columna_fecha, columna_articulos, columna_importe, columna_cantidad], inplace=True)

# 4. Filtrar por fechas
fecha_inicio = '2024-07-01'
fecha_fin = '2025-07-31'
df_filtrado = df[(df[columna_fecha] >= fecha_inicio) & (df[columna_fecha] <= fecha_fin)].copy()

if df_filtrado.empty:
    print("No se encontraron datos de ventas en el rango de fechas especificado.")
    exit()

# 5. Total mensual y anual
ventas_mensuales = df_filtrado.resample('MS', on=columna_fecha)[columna_importe].sum().fillna(0).reset_index()
ventas_mensuales['FECHA_STR'] = ventas_mensuales[columna_fecha].dt.strftime('%Y-%m')
total_anual = df_filtrado[columna_importe].sum()

print("--- Reporte de Ventas Mensuales (Julio 2024 - Julio 2025) ---")
print(ventas_mensuales.to_string())
print("\n" + "-"*50)
print(f"VENTAS TOTALES DEL PERIODO: {total_anual:,.2f} SOLES")
print("-" * 50)

# 6. Etiquetas de meses
nombres_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']

etiquetas_personalizadas = []
for fecha in ventas_mensuales[columna_fecha]:
    mes_nombre = nombres_meses[fecha.month - 1]
    if fecha.year == 2024 and fecha.month == 7:
        etiquetas_personalizadas.append('julio(2024)')
    elif fecha.year == 2025 and fecha.month == 7:
        etiquetas_personalizadas.append('julio(2025)')
    else:
        etiquetas_personalizadas.append(mes_nombre)

# 7. Gráfico de línea total mensual
fig1 = px.line(ventas_mensuales, x='FECHA_STR', y=columna_importe,
               title='Tendencia de Ventas Mensuales (Julio 2024 - Julio 2025)', markers=True)
fig1.update_xaxes(title_text='Mes', tickmode='array', tickvals=ventas_mensuales['FECHA_STR'], ticktext=etiquetas_personalizadas)
fig1.update_yaxes(title_text='Total de Ventas (Soles)')
fig1.show()

# 8. Gráfico por producto individual mensual (líneas gruesas)
ventas_todos_productos_mensuales = df_filtrado.pivot_table(
    values=columna_importe,
    index=df_filtrado[columna_fecha].dt.to_period('M'),
    columns=columna_articulos,
    aggfunc='sum',
    fill_value=0
).stack().reset_index()

ventas_todos_productos_mensuales.columns = [columna_fecha, columna_articulos, columna_importe]
ventas_todos_productos_mensuales[columna_fecha] = ventas_todos_productos_mensuales[columna_fecha].astype(str)

fig2 = px.line(ventas_todos_productos_mensuales, x=columna_fecha, y=columna_importe, color=columna_articulos,
               title='Historial de Ventas por Producto (Julio 2024 - Julio 2025)', markers=True)
fig2.update_traces(line=dict(width=4))
fig2.update_xaxes(title_text='Mes')
fig2.update_yaxes(title_text='Total de Ventas (Soles)')
fig2.show()

# 9. Clasificación de productos
ventas_totales_por_producto = df_filtrado.groupby(columna_articulos)[columna_cantidad].sum().sort_values(ascending=False).reset_index()
ventas_totales_por_producto.rename(columns={columna_cantidad: 'Cantidad Vendida'}, inplace=True)

# Criterios de categorías
num_mas_vendidos = 10
num_intermedio = 20
mas_vendidos_list = ventas_totales_por_producto.head(num_mas_vendidos)[columna_articulos].tolist()
intermedio_list = ventas_totales_por_producto.iloc[num_mas_vendidos:num_mas_vendidos + num_intermedio][columna_articulos].tolist()

def asignar_categoria(producto):
    if producto in mas_vendidos_list:
        return 'Más Vendido'
    elif producto in intermedio_list:
        return 'Intermedio'
    else:
        return 'Casi Nada'

ventas_totales_por_producto['Categoria_Venta'] = ventas_totales_por_producto[columna_articulos].apply(asignar_categoria)

# Unir al DataFrame filtrado
df_filtrado = df_filtrado.merge(ventas_totales_por_producto[[columna_articulos, 'Categoria_Venta']], on=columna_articulos, how='left')

# Definir el orden y el mapeo de colores
categorias_ordenadas = ['Más Vendido', 'Intermedio', 'Casi Nada']
mapeo_colores = {'Más Vendido': 'blue', 'Intermedio': 'green', 'Casi Nada': 'red'}

# Crear la columna 'MES' aquí para que esté disponible para los gráficos posteriores
df_filtrado['MES'] = df_filtrado[columna_fecha].dt.to_period('M').astype(str)

# 10. Gráfico horizontal de productos clasificados por cantidad total
fig3 = px.bar(
    ventas_totales_por_producto,
    x='Cantidad Vendida',
    y=columna_articulos,
    color='Categoria_Venta',
    color_discrete_map=mapeo_colores,
    category_orders={'Categoria_Venta': categorias_ordenadas},
    orientation='h',
    title='Productos Más Vendidos por Cantidad (Clasificado por Categoría)',
    hover_data={columna_articulos: True, 'Categoria_Venta': True, 'Cantidad Vendida': True},
    height=max(600, len(ventas_totales_por_producto) * 40),
    width=1600
)

fig3.update_layout(
    bargap=0.1,
    font=dict(size=14),
    title_font=dict(size=24),
    margin=dict(l=300, r=50, t=80, b=50),
    xaxis=dict(title='Cantidad de Unidades Vendidas', zeroline=True),
    yaxis=dict(title='Producto', automargin=True),
    showlegend=True
)
fig3.update_yaxes(autorange='reversed')
fig3.show()

# La sección del código que generaba y mostraba la figura 4 ha sido eliminada.

# 11. Gráfico de barras por MES, CATEGORÍA y PRODUCTO con hover interactivo
# Agrupar por MES, PRODUCTO y CATEGORÍA
ventas_detalladas = df_filtrado.groupby(
    ['MES', columna_articulos, 'Categoria_Venta']
)[columna_cantidad].sum().reset_index()

# Gráfico interactivo con hover que muestra el producto
# Definir el orden correcto de las categorías
orden_categorias = ['Casi Nada', 'Intermedio', 'Más Vendido']

# Crear el gráfico
fig5 = px.bar(
    ventas_detalladas.sort_values('Categoria_Venta'),
    x='MES',
    y=columna_cantidad,
    color='Categoria_Venta',
    category_orders={'Categoria_Venta': orden_categorias},
    hover_data={columna_articulos: True, columna_cantidad: True, 'Categoria_Venta': True},
    labels={columna_cantidad: 'Cantidad Vendida', 'MES': 'Mes'},
    title='Ventas Mensuales por Categoría y Producto (Hover con Nombre del Producto)',
    barmode='stack',
    height=600,
    width=1100,
    color_discrete_map={
        'Casi Nada': 'red',
        'Intermedio': 'green',
        'Más Vendido': 'blue'
    }
)

# Ajustes de diseño
fig5.update_layout(
    bargap=0.15,
    font=dict(size=13),
    xaxis=dict(title='Mes'),
    yaxis=dict(title='Cantidad Vendida'),
    legend_title='Categoría'
)

# Mostrar el gráfico
fig5.show()