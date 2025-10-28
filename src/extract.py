import pandas as pd
import os
# Definimos la ruta base de los datos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'RAW')
DW_DIR = os.path.join(BASE_DIR, 'DW')

# Lista de todas las tablas que necesitamos leer
TABLE_NAMES = [
    'address',
    'channel',
    'customer',
    'nps_response',
    'payment',
    'product',
    'product_category',
    'province',
    'sales_order',
    'sales_order_item',
    'shipment',
    'store',
    'web_session'
]

def extract_all_data(data_dir=DATA_DIR):
    """
    Carga todas las tablas .csv desde el directorio RAW a un diccionario
    de DataFrames de pandas.
    """
    data = {}
    print(f"Iniciando extracción de datos desde: {data_dir}")
    
    try:
        for table in TABLE_NAMES:
            file_path = os.path.join(data_dir, f"{table}.csv")
            data[table] = pd.read_csv(file_path)
            print(f"  -> Tabla '{table}' cargada exitosamente.")
            
        print("Extracción de datos completada.\n")
        return data
    
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo. {e}")
        return None
    except Exception as e:
        print(f"Error durante la extracción: {e}")
        return None

if __name__ == '__main__':
    # Esto es para probar que la función corre
    raw_data = extract_all_data()
    if raw_data:
        print("\nPrueba de extracción exitosa.")
        print(f"Tablas cargadas: {list(raw_data.keys())}")
        print(f"\nPrimeras 5 filas de 'customer':")
        print(raw_data['customer'].head())