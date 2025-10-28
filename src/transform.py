import pandas as pd

def _create_date_key(df, date_column):
    """Función auxiliar para crear la 'fecha_key' como YYYYMMDD."""
    dates = pd.to_datetime(df[date_column], errors='coerce')
    # Convertir NaT (fechas nulas) a un valor que podamos manejar
    # Usaremos 0 o -1 para "Fecha Desconocida"
    return dates.dt.strftime('%Y%m%d').fillna('0').astype(int)

# --- Funciones de Creación de Dimensiones (con Surrogate Keys) ---

def create_dim_fecha(data):
    """
    Crea la Dimensión de Fecha.
    La 'fecha_key' (YYYYMMDD) actúa como nuestra Surrogate Key "inteligente".
    """
    print("  -> Creando Dim_Fecha...")
    
    # Recolectar todas las fechas
    all_dates = pd.concat([
        pd.to_datetime(data['sales_order']['order_date'], errors='coerce'),
        pd.to_datetime(data['web_session']['started_at'], errors='coerce'),
        pd.to_datetime(data['nps_response']['responded_at'], errors='coerce'),
        pd.to_datetime(data['payment']['paid_at'], errors='coerce'),
        pd.to_datetime(data['shipment']['shipped_at'], errors='coerce'),
        pd.to_datetime(data['shipment']['delivered_at'], errors='coerce')
    ]).dropna()
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Aplicamos normalize() usando el accesor .dt
    all_dates_normalized = all_dates.dt.normalize()
    # --- FIN DE LA CORRECCIÓN ---

    if all_dates_normalized.empty:
        print("Advertencia: No se encontraron fechas válidas.")
        return pd.DataFrame(columns=['fecha_key', 'fecha_completa', 'año', 'mes', 'dia'])

    min_date = all_dates_normalized.min()
    max_date = all_dates_normalized.max()
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    df_fecha = pd.DataFrame(date_range, columns=['fecha_completa'])
    
    # La fecha_key (YYYYMMDD) es nuestra SK.
    df_fecha['fecha_key'] = df_fecha['fecha_completa'].dt.strftime('%Y%m%d').astype(int)
    df_fecha['año'] = df_fecha['fecha_completa'].dt.year
    df_fecha['mes'] = df_fecha['fecha_completa'].dt.month
    df_fecha['mes_nombre'] = df_fecha['fecha_completa'].dt.strftime('%B')
    df_fecha['dia'] = df_fecha['fecha_completa'].dt.day
    df_fecha['dia_semana'] = df_fecha['fecha_completa'].dt.dayofweek
    df_fecha['trimestre'] = df_fecha['fecha_completa'].dt.quarter
    
    # Añadir registro para fechas desconocidas (SK = 0)
    unknown_date = pd.DataFrame([{
        'fecha_key': 0, 'fecha_completa': pd.NaT, 'año': 0, 'mes': 0, 
        'mes_nombre': 'Desconocido', 'dia': 0, 'dia_semana': -1, 'trimestre': 0
    }])
    df_fecha = pd.concat([unknown_date, df_fecha], ignore_index=True)
    
    return df_fecha

def create_dim_cliente(data):
    """Crea Dim_Cliente con Surrogate Key (cliente_sk)."""
    print("  -> Creando Dim_Cliente...")
    df = data['customer'].copy()
    df = df[['customer_id', 'email', 'first_name', 'last_name', 'status']]
    
    # Crear la Surrogate Key (SK)
    df = df.sort_values(by='customer_id')
    df.reset_index(drop=True, inplace=True)
    df['cliente_sk'] = df.index + 1 # SKs empiezan en 1
    
    # Añadir registro para "Desconocido"
    unknown = pd.DataFrame([{'cliente_sk': -1, 'customer_id': 'N/A', 'email': 'N/A'}])
    df = pd.concat([unknown, df], ignore_index=True)
    
    return df

def create_dim_canal(data):
    """Crea Dim_Canal con Surrogate Key (canal_sk)."""
    print("  -> Creando Dim_Canal...")
    df = data['channel'].copy()
    df = df[['channel_id', 'code', 'name']].rename(columns={'name': 'canal_nombre'})
    
    df = df.sort_values(by='channel_id')
    df.reset_index(drop=True, inplace=True)
    df['canal_sk'] = df.index + 1
    
    unknown = pd.DataFrame([{'canal_sk': -1, 'channel_id': -1, 'code': 'N/A'}])
    df = pd.concat([unknown, df], ignore_index=True)
    
    return df

def create_dim_geografia(data):
    """Crea Dim_Geografia con Surrogate Key (geografia_sk)."""
    print("  -> Creando Dim_Geografia...")
    address = data['address'].copy()
    province = data['province'].copy()
    
    df = pd.merge(address, province, on='province_id', how='left')
    df = df[['address_id', 'line1', 'city', 'postal_code', 'name', 'code']]
    df = df.rename(columns={'name': 'provincia_nombre', 'code': 'provincia_code'})
    
    df = df.sort_values(by='address_id')
    df.reset_index(drop=True, inplace=True)
    df['geografia_sk'] = df.index + 1
    
    unknown = pd.DataFrame([{'geografia_sk': -1, 'address_id': -1, 'city': 'N/A'}])
    df = pd.concat([unknown, df], ignore_index=True)
    
    return df

def create_dim_producto(data):
    """Crea Dim_Producto con Surrogate Key (producto_sk)."""
    print("  -> Creando Dim_Producto...")
    product = data['product'].copy()
    category = data['product_category'].copy()
    
    df = pd.merge(product, category, on='category_id', how='left', suffixes=('_producto', '_categoria'))
    df = df[['product_id', 'sku', 'name_producto', 'list_price', 'status', 'name_categoria']]
    df = df.rename(columns={'name_producto': 'producto_nombre', 'status': 'producto_status', 'name_categoria': 'categoria_nombre'})
    df['categoria_nombre'] = df['categoria_nombre'].fillna('Sin Categoría')

    df = df.sort_values(by='product_id')
    df.reset_index(drop=True, inplace=True)
    df['producto_sk'] = df.index + 1
    
    unknown = pd.DataFrame([{'producto_sk': -1, 'product_id': -1, 'sku': 'N/A'}])
    df = pd.concat([unknown, df], ignore_index=True)

    return df

def create_dim_tienda(data, dim_geografia):
    """Crea Dim_Tienda con Surrogate Key (tienda_sk)."""
    print("  -> Creando Dim_Tienda...")
    store = data['store'].copy()
    # Usamos la Dim_Geografia (que ya tiene su SK)
    df = pd.merge(store, dim_geografia[['address_id', 'geografia_sk', 'provincia_nombre', 'city']], 
                  on='address_id', how='left')
    
    df = df[['store_id', 'name', 'geografia_sk', 'provincia_nombre', 'city']]
    df = df.rename(columns={'name': 'tienda_nombre'})

    df = df.sort_values(by='store_id')
    df.reset_index(drop=True, inplace=True)
    df['tienda_sk'] = df.index + 1
    
    unknown = pd.DataFrame([{'tienda_sk': -1, 'store_id': -1, 'tienda_nombre': 'N/A'}])
    df = pd.concat([unknown, df], ignore_index=True)
    
    return df

# --- Funciones de Creación de Hechos (con Surrogate Keys) ---

def create_fact_pedidos(data, dim_fecha, dim_cliente, dim_canal, dim_geografia, dim_tienda):
    """Crea Fact_Pedidos (Cabecera) usando SKs."""
    print("  -> Creando Fact_Pedidos...")
    df = data['sales_order'].copy()
    
    # 1. Filtrar por status
    df = df[df['status'].isin(['PAID', 'FULFILLED'])]
    
    # 2. Reemplazar NKs (Natural Keys) con SKs (Surrogate Keys)
    df['fecha_key'] = _create_date_key(df, 'order_date')
    
    df = pd.merge(df, dim_cliente[['customer_id', 'cliente_sk']], on='customer_id', how='left')
    df = pd.merge(df, dim_canal[['channel_id', 'canal_sk']], on='channel_id', how='left')
    df = pd.merge(df, dim_geografia[['address_id', 'geografia_sk']], left_on='shipping_address_id', right_on='address_id', how='left')
    df = pd.merge(df, dim_tienda[['store_id', 'tienda_sk']], on='store_id', how='left')

    # 3. Manejar nulos (asignar SK "Desconocido" = -1)
    df['cliente_sk'] = df['cliente_sk'].fillna(-1).astype(int)
    df['canal_sk'] = df['canal_sk'].fillna(-1).astype(int)
    df['geografia_sk'] = df['geografia_sk'].fillna(-1).astype(int)
    df['tienda_sk'] = df['tienda_sk'].fillna(-1).astype(int)

    # 4. Crear SK para la tabla de hechos
    df.reset_index(drop=True, inplace=True)
    df['pedido_sk'] = df.index + 1
    
    # 5. Seleccionar columnas finales
    df = df[[
        'pedido_sk',          # PK (SK)
        'order_id',           # NK (Dimension Degenerada)
        'fecha_key',          # FK (Dim_Fecha)
        'cliente_sk',         # FK (Dim_Cliente)
        'canal_sk',           # FK (Dim_Canal)
        'geografia_sk',       # FK (Dim_Geografia, por envío)
        'tienda_sk',          # FK (Dim_Tienda)
        'subtotal', 'tax_amount', 'shipping_fee', 'total_amount' # Métricas
    ]]
    return df

def create_fact_ventas_items(data, dim_fecha, dim_producto):
    """Crea Fact_Ventas_Items (Detalle) usando SKs."""
    print("  -> Creando Fact_Ventas_Items...")
    items = data['sales_order_item'].copy()
    orders = data['sales_order'][['order_id', 'order_date', 'status']]
    
    df = pd.merge(items, orders, on='order_id', how='inner')
    df = df[df['status'].isin(['PAID', 'FULFILLED'])]
    
    # 2. Reemplazar NKs con SKs
    df['fecha_key'] = _create_date_key(df, 'order_date')
    df = pd.merge(df, dim_producto[['product_id', 'producto_sk']], on='product_id', how='left')
    df['producto_sk'] = df['producto_sk'].fillna(-1).astype(int)
    
    # 3. Crear SK para la tabla de hechos
    df.reset_index(drop=True, inplace=True)
    df['ventas_item_sk'] = df.index + 1
    
    # 4. Seleccionar columnas finales
    df = df[[
        'ventas_item_sk',     # PK (SK)
        'order_item_id',    # NK
        'order_id',         # NK (Dimension Degenerada)
        'fecha_key',        # FK (Dim_Fecha)
        'producto_sk',      # FK (Dim_Producto)
        'quantity', 'unit_price', 'discount_amount', 'line_total' # Métricas
    ]]
    return df

def create_fact_pagos(data, dim_fecha):
    """Crea Fact_Pagos usando SKs."""
    print("  -> Creando Fact_Pagos...")
    df = data['payment'].copy()
    
    df['fecha_key'] = _create_date_key(df, 'paid_at')
    
    df.reset_index(drop=True, inplace=True)
    df['pago_sk'] = df.index + 1
    
    df = df[[
        'pago_sk',            # PK (SK)
        'payment_id',         # NK
        'order_id',           # NK (Dimension Degenerada)
        'fecha_key',          # FK (Dim_Fecha, de pago)
        'method', 'status', 'amount' # Atributos y Métrica
    ]]
    return df

def create_fact_envios(data, dim_fecha):
    """Crea Fact_Envios usando SKs."""
    print("  -> Creando Fact_Envios...")
    df = data['shipment'].copy()
    
    df['shipped_at'] = pd.to_datetime(df['shipped_at'], errors='coerce')
    df['delivered_at'] = pd.to_datetime(df['delivered_at'], errors='coerce')

    # 2. Crear fecha_keys
    df['fecha_key_shipped'] = _create_date_key(df, 'shipped_at')
    df['fecha_key_delivered'] = _create_date_key(df, 'delivered_at')

    df['dias_de_entrega'] = (df['delivered_at'] - df['shipped_at']).dt.days
    
    df.reset_index(drop=True, inplace=True)
    df['envio_sk'] = df.index + 1
    
    df = df[[
        'envio_sk',           # PK (SK)
        'shipment_id',        # NK
        'order_id',           # NK (Dimension Degenerada)
        'fecha_key_shipped',  # FK (Dim_Fecha, rol "Despacho")
        'fecha_key_delivered',# FK (Dim_Fecha, rol "Entrega")
        'carrier', 'status', 'dias_de_entrega' # Atributos y Métrica
    ]]
    return df

def create_fact_sesiones(data, dim_fecha, dim_cliente):
    """Crea Fact_Sesiones usando SKs."""
    print("  -> Creando Fact_Sesiones...")
    df = data['web_session'].copy()
    
    df['fecha_key'] = _create_date_key(df, 'started_at')
    df = pd.merge(df, dim_cliente[['customer_id', 'cliente_sk']], on='customer_id', how='left')
    df['cliente_sk'] = df['cliente_sk'].fillna(-1).astype(int) # -1 para anónimos
    
    df.reset_index(drop=True, inplace=True)
    df['session_sk'] = df.index + 1
    
    df = df[[
        'session_sk',         # PK (SK)
        'session_id',         # NK
        'fecha_key',          # FK (Dim_Fecha)
        'cliente_sk',         # FK (Dim_Cliente)
        'source', 'device'    # Atributos
    ]]
    return df

def create_fact_nps(data, dim_fecha, dim_cliente, dim_canal):
    """Crea Fact_NPS usando SKs."""
    print("  -> Creando Fact_NPS...")
    df = data['nps_response'].copy()
    
    df['fecha_key'] = _create_date_key(df, 'responded_at')
    df = pd.merge(df, dim_cliente[['customer_id', 'cliente_sk']], on='customer_id', how='left')
    df = pd.merge(df, dim_canal[['channel_id', 'canal_sk']], on='channel_id', how='left')

    df['cliente_sk'] = df['cliente_sk'].fillna(-1).astype(int)
    df['canal_sk'] = df['canal_sk'].fillna(-1).astype(int)

    df.reset_index(drop=True, inplace=True)
    df['nps_sk'] = df.index + 1

    df = df[[
        'nps_sk',             # PK (SK)
        'nps_id',             # NK
        'fecha_key',          # FK (Dim_Fecha)
        'cliente_sk',         # FK (Dim_Cliente)
        'canal_sk',           # FK (Dim_Canal)
        'score'               # Métrica
    ]]
    return df

# --- Función Orquestadora (ACTUALIZADA) ---

def transform_all_data(data):
    """
    Orquesta todas las transformaciones y devuelve un diccionario
    con los DataFrames del DW.
    """
    if data is None:
        print("No hay datos para transformar.")
        return None
        
    print("Iniciando proceso de transformación (T)...")
    
    dw_tables = {}
    
    # 1. Dimensiones (El orden importa)
    # Dim_Geografia debe existir antes que Dim_Tienda
    dw_tables['Dim_Fecha'] = create_dim_fecha(data)
    dw_tables['Dim_Cliente'] = create_dim_cliente(data)
    dw_tables['Dim_Canal'] = create_dim_canal(data)
    dw_tables['Dim_Producto'] = create_dim_producto(data)
    dw_tables['Dim_Geografia'] = create_dim_geografia(data)
    dw_tables['Dim_Tienda'] = create_dim_tienda(data, dw_tables['Dim_Geografia'])
    
    # 2. Hechos (Ahora dependen de las dimensiones)
    dw_tables['Fact_Pedidos'] = create_fact_pedidos(
        data, dw_tables['Dim_Fecha'], dw_tables['Dim_Cliente'], 
        dw_tables['Dim_Canal'], dw_tables['Dim_Geografia'], dw_tables['Dim_Tienda']
    )
    dw_tables['Fact_Ventas_Items'] = create_fact_ventas_items(
        data, dw_tables['Dim_Fecha'], dw_tables['Dim_Producto']
    )
    dw_tables['Fact_Pagos'] = create_fact_pagos(
        data, dw_tables['Dim_Fecha']
    )
    dw_tables['Fact_Envios'] = create_fact_envios(
        data, dw_tables['Dim_Fecha']
    )
    dw_tables['Fact_Sesiones'] = create_fact_sesiones(
        data, dw_tables['Dim_Fecha'], dw_tables['Dim_Cliente']
    )
    dw_tables['Fact_NPS'] = create_fact_nps(
        data, dw_tables['Dim_Fecha'], dw_tables['Dim_Cliente'], dw_tables['Dim_Canal']
    )
    
    print("Proceso de transformación completado.\n")
    return dw_tables

if __name__ == '__main__':
    print("Este módulo contiene las funciones de transformación.")
    print("Ejecútalo a través de main.py para un ETL completo.")