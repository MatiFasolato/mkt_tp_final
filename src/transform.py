import pandas as pd

# --- Funciones Auxiliares ---

def _get_date_id(date_series, dim_calendar):
    """
    Función auxiliar para buscar el 'id' (Surrogate Key) de dim_calendar
    basado en una serie de fechas.
    Devuelve NaN si la fecha no se encuentra.
    """
    dates = pd.to_datetime(date_series, errors='coerce').dt.normalize()
    dates_df = pd.DataFrame({'date_lookup': dates})
    
    merged = pd.merge(
        dates_df,
        dim_calendar[['date', 'id']],
        left_on='date_lookup',
        right_on='date',
        how='left'
    )
    return merged['id']

def _get_time(date_series):
    """Extrae el time HH:MM:SS."""
    times = pd.to_datetime(date_series, errors='coerce')
    return times.dt.strftime('%H:%M:%S').fillna('00:00:00')


# --- Funciones de Creación de Dimensiones (Optimizadas) ---

def create_dim_calendar(data):
    """Crea la Dimensión de Calendario (dim_calendar)."""
    print("  -> Creando dim_calendar...")
    
    all_dates = pd.concat([
        pd.to_datetime(data['sales_order']['order_date'], errors='coerce'),
        pd.to_datetime(data['web_session']['started_at'], errors='coerce'),
        pd.to_datetime(data['nps_response']['responded_at'], errors='coerce'),
        pd.to_datetime(data['payment']['paid_at'], errors='coerce'),
        pd.to_datetime(data['shipment']['shipped_at'], errors='coerce'),
        pd.to_datetime(data['shipment']['delivered_at'], errors='coerce'),
        pd.to_datetime(data['customer']['created_at'], errors='coerce'),
        pd.to_datetime(data['address']['created_at'], errors='coerce'),
        pd.to_datetime(data['product']['created_at'], errors='coerce'),
    ]).dropna()
    
    all_dates_normalized = all_dates.dt.normalize()

    if all_dates_normalized.empty:
        print("Advertencia: No se encontraron fechas válidas.")
        return pd.DataFrame(columns=['id', 'date', 'day', 'month', 'year', 'day_name', 'month_name', 'quarter', 'week_number', 'year_month', 'is_weekend'])

    min_date = all_dates_normalized.min()
    max_date = all_dates_normalized.max()
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    df_calendar = pd.DataFrame(date_range, columns=['date'])
    
    df_calendar['day'] = df_calendar['date'].dt.day
    df_calendar['month'] = df_calendar['date'].dt.month
    df_calendar['year'] = df_calendar['date'].dt.year
    df_calendar['day_name'] = df_calendar['date'].dt.day_name()
    df_calendar['month_name'] = df_calendar['date'].dt.month_name()
    df_calendar['quarter'] = df_calendar['date'].dt.quarter
    df_calendar['week_number'] = df_calendar['date'].dt.isocalendar().week.astype(int)
    df_calendar['year_month'] = df_calendar['date'].dt.strftime('%Y-%m')
    df_calendar['is_weekend'] = df_calendar['day_name'].isin(['Saturday', 'Sunday'])
    
    df_calendar.reset_index(drop=True, inplace=True)
    df_calendar['id'] = df_calendar.index + 1
    
    cols = ['id'] + [col for col in df_calendar if col != 'id']
    df_calendar = df_calendar[cols]
    
    return df_calendar

def create_dim_customer(data): # <-- CAMBIO DE NOMBRE
    """Crea dim_customer con 'id' (SK) y 'customer_key' (NK)."""
    print("  -> Creando dim_customer...") # <-- CAMBIO DE NOMBRE
    df = data['customer'].copy()
    
    df = df[['customer_id', 'email', 'first_name', 'last_name', 'phone', 'status', 'created_at']]
    df = df.rename(columns={'customer_id': 'customer_key'})
    
    df = df.sort_values(by='customer_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    cols = ['id', 'customer_key'] + [col for col in df if col not in ['id', 'customer_key']]
    df = df[cols]
    
    return df

def create_dim_channel(data):
    """Crea dim_channel con 'id' (SK) y 'channel_key' (NK)."""
    print("  -> Creando dim_channel...")
    df = data['channel'].copy()
    
    df = df.rename(columns={'channel_id': 'channel_key'})
    
    df = df.sort_values(by='channel_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    cols = ['id', 'channel_key', 'code', 'name']
    df = df[cols]
    
    return df

def create_dim_address(data):
    """Crea dim_address (para direcciones de cliente) con 'id' (SK)."""
    print("  -> Creando dim_address...")
    address = data['address'].copy()
    province = data['province'].copy()
    
    df = pd.merge(address, province, on='province_id', how='left')
    
    df = df.rename(columns={
        'address_id': 'address_key',
        'name': 'province_name',
        'code': 'province_code'
    })
    
    df = df[['address_key', 'line1', 'line2', 'city', 'province_name', 'province_code', 'postal_code', 'country_code', 'created_at']]

    df = df.sort_values(by='address_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    cols = ['id', 'address_key'] + [col for col in df if col not in ['id', 'address_key']]
    df = df[cols]
    
    return df

def create_dim_product(data): # <-- CAMBIO DE NOMBRE
    """Crea dim_product con 'id' (SK), 'product_key' (NK) y categorías."""
    print("  -> Creando dim_product...") # <-- CAMBIO DE NOMBRE
    product = data['product'].copy()
    category = data['product_category'].copy()

    # 1. FORZAR TIPO DE DATO (dtype)
    product['category_id'] = product['category_id'].astype(str)
    category['category_id'] = category['category_id'].astype(str)
    category['parent_id'] = category['parent_id'].astype(str)
    
    # 2. Preparar categorías padre
    parent_cats = category[['category_id', 'name']].rename(
        columns={'category_id': 'parent_id', 'name': 'parent_category_name'}
    )
    
    categories_enriched = pd.merge(
        category,
        parent_cats,
        on='parent_id',
        how='left',
        suffixes=('_cat', '_parent')
    )

    # 3. Unir productos con categorías
    df = pd.merge(
        product,
        categories_enriched,
        on='category_id',
        how='left',
        suffixes=('_prod', '') 
    )
    
    # 4. Renombrar y seleccionar columnas
    df = df.rename(columns={
        'product_id': 'product_key',
        'name_prod': 'name',      
        'name': 'category_name'   
    })
    
    # 5. Seleccionar columnas
    df = df[['product_key', 'sku', 'name', 'list_price', 'status', 'created_at', 'category_name', 'parent_category_name']]
    
    df['category_name'] = df['category_name'].fillna('Sin Categoría')
    df['parent_category_name'] = df['parent_category_name'].fillna('Sin Categoría')

    # 6. Crear la Surrogate Key (SK) 'id'
    df = df.sort_values(by='product_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1

    # 7. Reordenar columnas
    cols = ['id', 'product_key'] + [col for col in df if col not in ['id', 'product_key']]
    df = df[cols]

    return df

def create_dim_store(data):
    """
    Crea dim_store denormalizada con 'id' (SK).
    Renombra 'line1' a 'line' y excluye 'line2'.
    """
    print("  -> Creando dim_store...")
    store = data['store'].copy()
    address = data['address'].copy()
    province = data['province'].copy()
    
    store_addr = pd.merge(store, address, on='address_id', how='left')
    df = pd.merge(store_addr, province, on='province_id', how='left')
    
    df = df.rename(columns={
        'store_id': 'store_key',
        'name_x': 'name',
        'line1': 'line',
        'name_y': 'province_name',
        'code': 'province_code'
    })
    
    df = df[['store_key', 'name', 'line', 'city', 'province_name', 'province_code', 'postal_code', 'country_code', 'created_at']]

    df = df.sort_values(by='store_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    cols = ['id', 'store_key'] + [col for col in df if col not in ['id', 'store_key']]
    df = df[cols]
    
    return df

# --- Funciones de Creación de "Hechos" (Tablas Denormalizadas) ---

def create_fact_sales_order(data, dim_calendar):
    """Crea fact_sales_order (denormalizada)."""
    print("  -> Creando fact_sales_order...")
    df = data['sales_order'].copy()
    
    df = df.rename(columns={'order_id': 'id', 'status': 'status_order'})
    
    df['order_date_id'] = _get_date_id(df['order_date'], dim_calendar)
    df['order_time'] = _get_time(df['order_date'])
    
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['billing_address_id'] = df['billing_address_id'].fillna(-1).astype(int)
    df['shipping_address_id'] = df['shipping_address_id'].fillna(-1).astype(int)

    cols = [
        'id', 'customer_id', 'channel_id', 'store_id', 'order_date_id', 'order_time',
        'billing_address_id', 'shipping_address_id', 'status_order', 'currency_code',
        'subtotal', 'tax_amount', 'shipping_fee', 'total_amount'
    ]
    return df[cols]

def create_fact_sales_order_item(data, dim_calendar):
    """Crea fact_sales_order_item (denormalizada)."""
    print("  -> Creando fact_sales_order_item...")
    items = data['sales_order_item'].copy()
    orders = data['sales_order'][['order_id', 'customer_id', 'channel_id', 'store_id', 'order_date']]
    
    df = pd.merge(items, orders, on='order_id', how='left')
    
    df = df.rename(columns={'order_item_id': 'id'})
    df['order_date_id'] = _get_date_id(df['order_date'], dim_calendar)
    
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['product_id'] = df['product_id'].fillna(-1).astype(int)

    # ESTA LISTA AHORA ESTÁ COMPLETA
    cols = [
        'id', 'order_id', 'customer_id', 'channel_id', 'store_id', 'product_id', 'order_date_id',
        'quantity', 'unit_price', 'discount_amount', 'line_total'
    ]
    return df[cols]

def create_fact_payment(data, dim_calendar):
    """Crea fact_payment (denormalizada)."""
    print("  -> Creando fact_payment...")
    payments = data['payment'].copy()
    orders = data['sales_order'][['order_id', 'customer_id', 'billing_address_id', 'channel_id', 'store_id']]
    
    df = pd.merge(payments, orders, on='order_id', how='left')
    
    df = df.rename(columns={'payment_id': 'id', 'status': 'status_payment'})
    
    df['paid_at_date_id'] = _get_date_id(df['paid_at'], dim_calendar)
    df['paid_at_time'] = _get_time(df['paid_at'])
    
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['billing_address_id'] = df['billing_address_id'].fillna(-1).astype(int)

    cols = [
        'id', 'customer_id', 'billing_address_id', 'channel_id', 'store_id',
        'method', 'status_payment', 'amount', 'paid_at_date_id', 'paid_at_time',
        'transaction_ref'
    ]
    return df[cols]

def create_fact_shipment(data, dim_calendar):
    """Crea fact_shipment (denormalizada)."""
    print("  -> Creando fact_shipment...")
    shipments = data['shipment'].copy()
    # Traer campos de la cabecera
    orders = data['sales_order'][['order_id', 'customer_id', 'shipping_address_id', 'channel_id']]
    
    df = pd.merge(shipments, orders, on='order_id', how='left')
    
    df = df.rename(columns={'shipment_id': 'id'})
    
    # Convertir a datetime ANTES de calcular la diferencia
    df['shipped_at'] = pd.to_datetime(df['shipped_at'], errors='coerce')
    df['delivered_at'] = pd.to_datetime(df['delivered_at'], errors='coerce')

    # FKs a dim_calendar
    df['shipped_at_date_id'] = _get_date_id(df['shipped_at'], dim_calendar)
    df['delivered_at_date_id'] = _get_date_id(df['delivered_at'], dim_calendar)
    
    # Extraer tiempos
    df['shipped_at_time'] = _get_time(df['shipped_at'])
    df['delivered_at_time'] = _get_time(df['delivered_at'])

    # --- CÁLCULO DE LA MÉTRICA (Aquí estaba el error) ---
    df['dias_de_entrega'] = (df['delivered_at'] - df['shipped_at']).dt.days

    # Relleno de claves naturales
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['shipping_address_id'] = df['shipping_address_id'].fillna(-1).astype(int)

    cols = [
        'id', 'customer_id', 'shipping_address_id', 'channel_id', 'carrier',
        'shipped_at_date_id', 'shipped_at_time',
        'delivered_at_date_id', 'delivered_at_time', 'tracking_number', 
        'dias_de_entrega'
    ]
    return df[cols]

def create_fact_web_session(data, dim_calendar):
    """Crea fact_web_session (denormalizada)."""
    print("  -> Creando fact_web_session...")
    df = data['web_session'].copy()
    
    df = df.rename(columns={'session_id': 'id'})
    
    df['started_at_date_id'] = _get_date_id(df['started_at'], dim_calendar)
    df['ended_at_date_id'] = _get_date_id(df['ended_at'], dim_calendar)
    
    df['started_at_time'] = _get_time(df['started_at'])
    df['ended_at_time'] = _get_time(df['ended_at'])
    
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)

    cols = [
        'id', 'customer_id', 'started_at_date_id', 'started_at_time',
        'ended_at_date_id', 'ended_at_time', 'source', 'device'
    ]
    return df[cols]

def create_fact_nps_response(data, dim_calendar):
    """Crea fact_nps_response (denormalizada, inferida)."""
    print("  -> Creando fact_nps_response...")
    df = data['nps_response'].copy()
    
    df = df.rename(columns={'nps_id': 'id'})
    
    df['responded_at_date_id'] = _get_date_id(df['responded_at'], dim_calendar)
    df['responded_at_time'] = _get_time(df['responded_at'])
    
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)

    cols = [
        'id', 'customer_id', 'channel_id', 'responded_at_date_id',
        'responded_at_time', 'score'
    ]
    return df[cols]

# --- Función Orquestadora (ACTUALIZADA) ---

def transform_all_data(data):
    """
    Orquesta todas las transformaciones y devuelve un diccionario
    con los DataFrames del DW (dim_ y fact_).
    """
    if data is None:
        print("No hay datos para transformar.")
        return None
        
    print("Iniciando proceso de transformación (T)...")
    
    dw_tables = {}
    
    # 1. Dimensiones
    dw_tables['dim_calendar'] = create_dim_calendar(data)
    
    # --- CAMBIOS AQUÍ ---
    dw_tables['dim_customer'] = create_dim_customer(data) # Sin 'S'
    dw_tables['dim_product'] = create_dim_product(data)   # Sin 'S'
    # ------------------
    
    dw_tables['dim_channel'] = create_dim_channel(data)
    dw_tables['dim_address'] = create_dim_address(data)
    dw_tables['dim_store'] = create_dim_store(data)
    
    # 2. Hechos
    dw_tables['fact_sales_order'] = create_fact_sales_order(
        data, dw_tables['dim_calendar']
    )
    dw_tables['fact_sales_order_item'] = create_fact_sales_order_item(
        data, dw_tables['dim_calendar']
    )
    dw_tables['fact_payment'] = create_fact_payment(
        data, dw_tables['dim_calendar']
    )
    dw_tables['fact_shipment'] = create_fact_shipment(
        data, dw_tables['dim_calendar']
    )
    dw_tables['fact_web_session'] = create_fact_web_session(
        data, dw_tables['dim_calendar']
    )
    dw_tables['fact_nps_response'] = create_fact_nps_response(
        data, dw_tables['dim_calendar']
    )
    
    print("Proceso de transformación completado.\n")
    return dw_tables

if __name__ == '__main__':
    print("Este módulo contiene las funciones de transformación.")
    print("Ejecútalo a través de main.py para un ETL completo.")