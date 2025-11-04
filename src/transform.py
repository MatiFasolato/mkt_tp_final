# Módulo: etl.transform
# Descripción: Funciones para transformar datos crudos en un modelo
# dimensional (Dimensiones y Hechos) para el Data Warehouse.

import pandas as pd

# --- Funciones Auxiliares ---

def _get_date_id(date_series, dim_calendar):
    """
    Función auxiliar para buscar la Surrogate Key (SK) de dim_calendar
    basado en una serie de fechas.
    
    Devuelve NaN si la fecha no se encuentra.
    
    Args:
        date_series (pd.Series): La serie de timestamps o fechas.
        dim_calendar (pd.DataFrame): La dimensión de calendario ya creada.
        
    Returns:
        pd.Series: Una serie con las SK 'id' de dim_calendar.
    """
    # Normaliza la fecha de entrada (elimina la hora)
    dates = pd.to_datetime(date_series, errors='coerce').dt.normalize()
    dates_df = pd.DataFrame({'date_lookup': dates})
    
    # --- MERGE ---
    # Busca el 'id' (SK) en dim_calendar usando la fecha normalizada.
    merged = pd.merge(
        dates_df,
        dim_calendar[['date', 'id']],
        left_on='date_lookup',
        right_on='date',
        how='left'
    )
    return merged['id']

def _get_time(date_series):
    """
    Función auxiliar para extraer el time (HH:MM:SS) de una serie de fechas.
    Rellena con '00:00:00' si es Nulo.
    """
    times = pd.to_datetime(date_series, errors='coerce')
    return times.dt.strftime('%H:%M:%S').fillna('00:00:00')


# --- Funciones de Creación de Dimensiones ---

def create_dim_calendar(data):
    """
    Crea la Dimensión de Calendario (dim_calendar) DINÁMICAMENTE.
    """
    print("  -> Creando dim_calendar...")
    
    # 1. Recolectar todas las fechas de todas las tablas
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
        print("Advertencia: No se encontraron fechas válidas para dim_calendar.")
        return pd.DataFrame(columns=['id', 'date', 'day', 'month', 'year', 'day_name', 'month_name', 'quarter', 'week_number', 'year_month', 'is_weekend'])

    # 2. Determinar rango dinámico
    min_date = all_dates_normalized.min()
    max_date = all_dates_normalized.max()
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    df_calendar = pd.DataFrame(date_range, columns=['date'])
    
    # 3. Enriquecer con atributos de fecha
    df_calendar['day'] = df_calendar['date'].dt.day
    df_calendar['month'] = df_calendar['date'].dt.month
    df_calendar['year'] = df_calendar['date'].dt.year
    df_calendar['day_name'] = df_calendar['date'].dt.day_name()
    df_calendar['month_name'] = df_calendar['date'].dt.month_name()
    df_calendar['quarter'] = df_calendar['date'].dt.quarter
    df_calendar['week_number'] = df_calendar['date'].dt.isocalendar().week.astype(int)
    df_calendar['year_month'] = df_calendar['date'].dt.strftime('%Y-%m')
    df_calendar['is_weekend'] = df_calendar['day_name'].isin(['Saturday', 'Sunday'])
    
    # 4. Crear Surrogate Key (SK)
    df_calendar.reset_index(drop=True, inplace=True)
    df_calendar['id'] = df_calendar.index + 1
    
    # 5. Ordenar columnas
    cols = ['id'] + [col for col in df_calendar if col != 'id']
    df_calendar = df_calendar[cols]
    
    return df_calendar

def create_dim_customer(data):
    """
    Crea la Dimensión de Cliente (dim_customer).
    
    Consume:
        data['customer']
        
    Crea:
        - id (SK): Surrogate Key
        - customer_key (NK): Natural Key (de 'customer_id')
    """
    print("  -> Creando dim_customer...")
    df = data['customer'].copy()
    
    # 1. Renombrar Natural Key (NK)
    df = df.rename(columns={'customer_id': 'customer_key'})
    
    # 2. Seleccionar columnas relevantes
    df = df[['customer_key', 'email', 'first_name', 'last_name', 'phone', 'status', 'created_at']]
    
    # 3. Crear Surrogate Key (SK)
    df = df.sort_values(by='customer_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    # 4. Ordenar columnas
    cols = ['id', 'customer_key'] + [col for col in df if col not in ['id', 'customer_key']]
    df = df[cols]
    
    return df

def create_dim_channel(data):
    """
    Crea la Dimensión de Canal (dim_channel).
    
    Consume:
        data['channel']
        
    Crea:
        - id (SK): Surrogate Key
        - channel_key (NK): Natural Key (de 'channel_id')
    """
    print("  -> Creando dim_channel...")
    df = data['channel'].copy()
    
    # 1. Renombrar Natural Key (NK)
    df = df.rename(columns={'channel_id': 'channel_key'})
    
    # 2. Crear Surrogate Key (SK)
    df = df.sort_values(by='channel_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    # 3. Ordenar y seleccionar columnas
    cols = ['id', 'channel_key', 'code', 'name']
    df = df[cols]
    
    return df

def create_dim_address(data):
    """
    Crea la Dimensión de Dirección (dim_address).
    Denormaliza la información de provincia.
    
    Consume:
        data['address']
        data['province']
        
    Crea:
        - id (SK): Surrogate Key
        - address_key (NK): Natural Key (de 'address_id')
    """
    print("  -> Creando dim_address...")
    address = data['address'].copy()
    province = data['province'].copy()
    
    # --- MERGE ---
    # Enriquece la dirección con el nombre de la provincia.
    # Join: (address) LEFT JOIN (province)
    # Key: (province_id)
    df = pd.merge(address, province, on='province_id', how='left')
    
    # 1. Renombrar claves y columnas ambiguas
    df = df.rename(columns={
        'address_id': 'address_key',
        'name': 'province_name',
        'code': 'province_code'
    })
    
    # 2. Seleccionar columnas
    df = df[['address_key', 'line1', 'line2', 'city', 'province_name', 
             'province_code', 'postal_code', 'country_code', 'created_at']]

    # 3. Crear Surrogate Key (SK)
    df = df.sort_values(by='address_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    # 4. Ordenar columnas
    cols = ['id', 'address_key'] + [col for col in df if col not in ['id', 'address_key']]
    df = df[cols]
    
    return df

def create_dim_product(data):
    """
    Crea la Dimensión de Producto (dim_product).
    Denormaliza la información de categoría y categoría padre.
    
    Consume:
        data['product']
        data['product_category']
        
    Crea:
        - id (SK): Surrogate Key
        - product_key (NK): Natural Key (de 'product_id')
    """
    print("  -> Creando dim_product...")
    product = data['product'].copy()
    category = data['product_category'].copy()

    # 1. Forzar tipos de datos para las claves de join
    product['category_id'] = product['category_id'].astype(str)
    category['category_id'] = category['category_id'].astype(str)
    category['parent_id'] = category['parent_id'].astype(str)
    
    # 2. Preparar categorías padre (para el self-join)
    parent_cats = category[['category_id', 'name']].rename(
        columns={'category_id': 'parent_id', 'name': 'parent_category_name'}
    )
    
    # --- MERGE 1 (Self-Join) ---
    # Busca el nombre de la categoría padre uniendo la tabla de categorías consigo misma.
    # Join: (category) LEFT JOIN (parent_cats)
    # Key: (parent_id)
    categories_enriched = pd.merge(
        category,
        parent_cats,
        on='parent_id',
        how='left',
        suffixes=('_cat', '_parent')
    )

    # --- MERGE 2 ---
    # Une los productos con sus categorías ya enriquecidas.
    # Join: (product) LEFT JOIN (categories_enriched)
    # Key: (category_id)
    df = pd.merge(
        product,
        categories_enriched,
        on='category_id',
        how='left',
        suffixes=('_prod', '') 
    )
    
    # 3. Renombrar claves y columnas ambiguas
    df = df.rename(columns={
        'product_id': 'product_key',
        'name_prod': 'name',      # Nombre del producto
        'name': 'category_name'   # Nombre de la categoría
    })
    
    # 4. Seleccionar y limpiar columnas
    df = df[['product_key', 'sku', 'name', 'list_price', 'status', 
             'created_at', 'category_name', 'parent_category_name']]
    
    df['category_name'] = df['category_name'].fillna('Sin Categoría')
    df['parent_category_name'] = df['parent_category_name'].fillna('Sin Categoría')

    # 5. Crear la Surrogate Key (SK)
    df = df.sort_values(by='product_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1

    # 6. Reordenar columnas
    cols = ['id', 'product_key'] + [col for col in df if col not in ['id', 'product_key']]
    df = df[cols]

    return df

def create_dim_store(data):
    """
    Crea la Dimensión de Tienda (dim_store).
    Denormaliza la información de dirección y provincia.
    
    Consume:
        data['store']
        data['address']
        data['province']
        
    Crea:
        - id (SK): Surrogate Key
        - store_key (NK): Natural Key (de 'store_id')
    """
    print("  -> Creando dim_store...")
    store = data['store'].copy()
    address = data['address'].copy()
    province = data['province'].copy()
    
    # --- MERGE 1 ---
    # Une la tienda con su dirección.
    # Join: (store) LEFT JOIN (address)
    # Key: (address_id)
    store_addr = pd.merge(store, address, on='address_id', how='left')
    
    # --- MERGE 2 ---
    # Une la tienda+dirección con la provincia.
    # Join: (store_addr) LEFT JOIN (province)
    # Key: (province_id)
    df = pd.merge(store_addr, province, on='province_id', how='left')
    
    # 1. Renombrar claves y columnas ambiguas
    df = df.rename(columns={
        'store_id': 'store_key',
        'name_x': 'name',         # Nombre de la tienda
        'line1': 'line',          # Renombrar 'line1' a 'line'
        'name_y': 'province_name',
        'code': 'province_code'
    })
    
    # 2. Seleccionar columnas (excluyendo 'line2')
    df = df[['store_key', 'name', 'line', 'city', 'province_name', 
             'province_code', 'postal_code', 'country_code', 'created_at']]

    # 3. Crear Surrogate Key (SK)
    df = df.sort_values(by='store_key')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index + 1
    
    # 4. Ordenar columnas
    cols = ['id', 'store_key'] + [col for col in df if col not in ['id', 'store_key']]
    df = df[cols]
    
    return df

# --- Funciones de Creación de Hechos ---
# (Estas funciones no cambian, pero se benefician
# de la corrección en _get_date_id)

def create_fact_sales_order(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Órdenes de Venta (fact_sales_order).
    Contiene la cabecera de la orden.
    
    Consume:
        data['sales_order']
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'order_id')
        - order_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): 
          customer_id, channel_id, store_id, 
          billing_address_id, shipping_address_id
    """
    print("  -> Creando fact_sales_order...")
    df = data['sales_order'].copy()
        
    # 1. Renombrar NK y columnas
    df = df.rename(columns={'order_id': 'id', 'status': 'status_order'})
    
    # 2. Buscar Foreign Keys (FKs) de dim_calendar
    df['order_date_id'] = _get_date_id(df['order_date'], dim_calendar)
    df['order_time'] = _get_time(df['order_date'])
    
    # 3. Limpiar claves naturales (usadas para joins en el BI)
    # Se rellenan con -1 (Clave para "Desconocido" o "N/A")
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['billing_address_id'] = df['billing_address_id'].fillna(-1).astype(int)
    df['shipping_address_id'] = df['shipping_address_id'].fillna(-1).astype(int)

    # 4. Seleccionar y ordenar columnas
    cols = [
        'id', 'customer_id', 'channel_id', 'store_id', 'order_date_id', 'order_time',
        'billing_address_id', 'shipping_address_id', 'status_order', 'currency_code',
        'subtotal', 'tax_amount', 'shipping_fee', 'total_amount'
    ]
    return df[cols]

def create_fact_sales_order_item(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Items de Venta (fact_sales_order_item).
    Tabla de granularidad de "línea de producto" (transaccional).
    
    Consume:
        data['sales_order_item']
        data['sales_order'] (para denormalizar claves)
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'order_item_id')
        - order_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): 
          order_id, customer_id, channel_id, store_id, product_id
    """
    print("  -> Creando fact_sales_order_item...")
    items = data['sales_order_item'].copy()
    orders = data['sales_order'][['order_id', 'customer_id', 'channel_id', 'store_id', 'order_date']]
    
    # --- MERGE ---
    # Denormaliza la tabla de items con claves de la cabecera (customer, channel, store, date).
    # Join: (items) LEFT JOIN (orders)
    # Key: (order_id)
    df = pd.merge(items, orders, on='order_id', how='left')
    
    # 1. Renombrar NK
    df = df.rename(columns={'order_item_id': 'id'})
    
    # 2. Buscar Foreign Key (FK) de dim_calendar
    df['order_date_id'] = _get_date_id(df['order_date'], dim_calendar)
    
    # 3. Limpiar claves naturales (usadas para joins en el BI)
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['product_id'] = df['product_id'].fillna(-1).astype(int)

    # 4. Seleccionar y ordenar columnas
    cols = [
        'id', 'order_id', 'customer_id', 'channel_id', 'store_id', 'product_id', 'order_date_id',
        'quantity', 'unit_price', 'discount_amount', 'line_total'
    ]
    return df[cols]

def create_fact_payment(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Pagos (fact_payment).
    
    Consume:
        data['payment']
        data['sales_order'] (para denormalizar claves)
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'payment_id')
        - paid_at_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): 
          customer_id, billing_address_id, channel_id, store_id
    """
    print("  -> Creando fact_payment...")
    payments = data['payment'].copy()
    orders = data['sales_order'][['order_id', 'customer_id', 'billing_address_id', 'channel_id', 'store_id']]
    
    # --- MERGE ---
    # Denormaliza la tabla de pagos con claves de la cabecera de la orden.
    # Join: (payments) LEFT JOIN (orders)
    # Key: (order_id)
    df = pd.merge(payments, orders, on='order_id', how='left')
    
    # 1. Renombrar NK y columnas
    df = df.rename(columns={'payment_id': 'id', 'status': 'status_payment'})
    
    # 2. Buscar Foreign Keys (FKs) de dim_calendar
    df['paid_at_date_id'] = _get_date_id(df['paid_at'], dim_calendar)
    df['paid_at_time'] = _get_time(df['paid_at'])
    
    # 3. Limpiar claves naturales
    df['store_id'] = df['store_id'].fillna(-1).astype(int)
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['billing_address_id'] = df['billing_address_id'].fillna(-1).astype(int)

    # 4. Seleccionar y ordenar columnas
    cols = [
        'id', 'customer_id', 'billing_address_id', 'channel_id', 'store_id',
        'method', 'status_payment', 'amount', 'paid_at_date_id', 'paid_at_time',
        'transaction_ref'
    ]
    return df[cols]

def create_fact_shipment(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Envíos (fact_shipment).
    Calcula la métrica 'dias_de_entrega'.
    
    Consume:
        data['shipment']
        data['sales_order'] (para denormalizar claves)
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'shipment_id')
        - shipped_at_date_id (FK): Foreign Key a dim_calendar
        - delivered_at_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): 
          customer_id, shipping_address_id, channel_id
    """
    print("  -> Creando fact_shipment...")
    shipments = data['shipment'].copy()
    orders = data['sales_order'][['order_id', 'customer_id', 'shipping_address_id', 'channel_id']]
    
    # --- MERGE ---
    # Denormaliza la tabla de envíos con claves de la cabecera de la orden.
    # Join: (shipments) LEFT JOIN (orders)
    # Key: (order_id)
    df = pd.merge(shipments, orders, on='order_id', how='left')
    
    # 1. Renombrar NK
    df = df.rename(columns={'shipment_id': 'id'})
    
    # 2. Convertir a datetime ANTES de calcular métricas o buscar FKs
    df['shipped_at'] = pd.to_datetime(df['shipped_at'], errors='coerce')
    df['delivered_at'] = pd.to_datetime(df['delivered_at'], errors='coerce')

    # 3. Buscar Foreign Keys (FKs) de dim_calendar
    df['shipped_at_date_id'] = _get_date_id(df['shipped_at'], dim_calendar)
    df['delivered_at_date_id'] = _get_date_id(df['delivered_at'], dim_calendar)
    
    # 4. Extraer tiempos
    df['shipped_at_time'] = _get_time(df['shipped_at'])
    df['delivered_at_time'] = _get_time(df['delivered_at'])

    # 5. Calcular métricas
    df['dias_de_entrega'] = (df['delivered_at'] - df['shipped_at']).dt.days

    # 6. Limpiar claves naturales
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)
    df['shipping_address_id'] = df['shipping_address_id'].fillna(-1).astype(int)

    # 7. Seleccionar y ordenar columnas
    cols = [
        'id', 'customer_id', 'shipping_address_id', 'channel_id', 'carrier',
        'shipped_at_date_id', 'shipped_at_time',
        'delivered_at_date_id', 'delivered_at_time', 'tracking_number', 
        'dias_de_entrega'
    ]
    return df[cols]

def create_fact_web_session(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Sesiones Web (fact_web_session).
    
    Consume:
        data['web_session']
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'session_id')
        - started_at_date_id (FK): Foreign Key a dim_calendar
        - ended_at_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): customer_id
    """
    print("  -> Creando fact_web_session...")
    df = data['web_session'].copy()
    
    # 1. Renombrar NK
    df = df.rename(columns={'session_id': 'id'})
    
    # 2. Buscar Foreign Keys (FKs) de dim_calendar
    df['started_at_date_id'] = _get_date_id(df['started_at'], dim_calendar)
    df['ended_at_date_id'] = _get_date_id(df['ended_at'], dim_calendar)
    
    # 3. Extraer tiempos
    df['started_at_time'] = _get_time(df['started_at'])
    df['ended_at_time'] = _get_time(df['ended_at'])
    
    # 4. Limpiar claves naturales
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)

    # 5. Seleccionar y ordenar columnas
    cols = [
        'id', 'customer_id', 'started_at_date_id', 'started_at_time',
        'ended_at_date_id', 'ended_at_time', 'source', 'device'
    ]
    return df[cols]

def create_fact_nps_response(data, dim_calendar):
    """
    Crea la Tabla de Hechos de Respuestas NPS (fact_nps_response).
    
    Consume:
        data['nps_response']
        dim_calendar (para buscar SK de fechas)
        
    Crea:
        - id (NK): Natural Key (de 'nps_id')
        - responded_at_date_id (FK): Foreign Key a dim_calendar
        - Claves Naturales (para joins en el BI): customer_id, channel_id
    """
    print("  -> Creando fact_nps_response...")
    df = data['nps_response'].copy()
    
    # 1. Renombrar NK
    df = df.rename(columns={'nps_id': 'id'})
    
    # 2. Buscar Foreign Keys (FKs) de dim_calendar
    df['responded_at_date_id'] = _get_date_id(df['responded_at'], dim_calendar)
    df['responded_at_time'] = _get_time(df['responded_at'])
    
    # 3. Limpiar claves naturales
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int)
    df['channel_id'] = df['channel_id'].fillna(-1).astype(int)

    # 4. Seleccionar y ordenar columnas
    cols = [
        'id', 'customer_id', 'channel_id', 'responded_at_date_id',
        'responded_at_time', 'score'
    ]
    return df[cols]

# --- Función Orquestadora (ACTUALIZADA) ---

def transform_all_data(data):
    """
    Orquesta todas las transformaciones y devuelve un diccionario
    con los DataFrames del Data Warehouse (dim_ y fact_).
    
    Args:
        data (dict): Un diccionario donde cada clave es el nombre
                     de una tabla cruda (ej: 'customer') y el valor
                     es un DataFrame de pandas con esos datos.
                     
    Returns:
        dict: Un diccionario donde cada clave es el nombre de la
              tabla del DW (ej: 'dim_customer') y el valor es el
              DataFrame transformado.
    """
    if data is None:
        print("Error: No hay datos (data es None) para transformar.")
        return None
        
    print("Iniciando proceso de transformación (T)...")
    
    dw_tables = {}
    
    # --- Paso 1: Crear Dimensiones ---
    print("Procesando Dimensiones...")
    
    # CAMBIO: dim_calendar ahora usa el rango estático por defecto.
    # Ya no necesita el diccionario 'data'.
    dw_tables['dim_calendar'] = create_dim_calendar(
        data=data
    )
    
    # El resto de dimensiones sí consumen 'data'
    dw_tables['dim_customer'] = create_dim_customer(data)
    dw_tables['dim_product'] = create_dim_product(data)
    dw_tables['dim_channel'] = create_dim_channel(data)
    dw_tables['dim_address'] = create_dim_address(data)
    dw_tables['dim_store'] = create_dim_store(data)
    
    # --- Paso 2: Crear Hechos ---
    print("Procesando Hechos...")
    # Pasamos la dim_calendar recién creada a todas las funciones de hechos
    dim_calendar = dw_tables['dim_calendar'] 
    
    dw_tables['fact_sales_order'] = create_fact_sales_order(data, dim_calendar)
    dw_tables['fact_sales_order_item'] = create_fact_sales_order_item(data, dim_calendar)
    dw_tables['fact_payment'] = create_fact_payment(data, dim_calendar)
    dw_tables['fact_shipment'] = create_fact_shipment(data, dim_calendar)
    dw_tables['fact_web_session'] = create_fact_web_session(data, dim_calendar)
    dw_tables['fact_nps_response'] = create_fact_nps_response(data, dim_calendar)
    
    print("Proceso de transformación completado.\n")
    return dw_tables

if __name__ == '__main__':
    print("Este módulo (transform.py) contiene las funciones de transformación.")
    print("No está diseñado para ejecutarse directamente.")
    print("Impórtalo y llama a 'transform_all_data(data)' desde tu script principal (ej: main.py).")