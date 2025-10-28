import time
from src.extract import extract_all_data
from src.transform import transform_all_data
from src.load import load_to_csv

def main():
    """
    Orquesta el proceso ETL completo:
    1. Extrae datos de /RAW
    2. Transforma los datos en un esquema estrella
    3. Carga los datos transformados en /DW
    """
    print("=============================================")
    print("==  Iniciando Proceso ETL para EcoBottle   ==")
    print("=============================================\n")
    
    start_time = time.time()
    
    try:
        # --- 1. FASE DE EXTRACCIÓN (E) ---
        print("[E] Iniciando Fase de Extracción...")
        raw_data = extract_all_data()
        
        if raw_data is None:
            print("Error en la extracción. Abortando proceso.")
            return
            
        print("[E] Extracción completada.\n")
        
        # --- 2. FASE DE TRANSFORMACIÓN (T) ---
        print("[T] Iniciando Fase de Transformación...")
        dw_tables = transform_all_data(raw_data)
        
        if dw_tables is None:
            print("Error en la transformación. Abortando proceso.")
            return
            
        print("[T] Transformación completada.\n")
        
        # --- 3. FASE DE CARGA (L) ---
        print("[L] Iniciando Fase de Carga en /DW...")
        
        for table_name, df in dw_tables.items():
            filename = f"{table_name}.csv"
            print(f"  -> Guardando tabla: {filename}...")
            load_to_csv(df, filename)
            
        print("[L] Carga de datos completada.\n")
        
        # --- Finalización ---
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=============================================")
        print(f"==  Proceso ETL completado exitosamente   ==")
        print(f"==  Tiempo total: {total_time:.2f} segundos      ==")
        print("=============================================")
        print(f"Se generaron {len(dw_tables)} tablas en la carpeta /DW.")

    except Exception as e:
        print(f"\n¡ERROR INESPERADO EN EL PROCESO PRINCIPAL!")
        print(f"Detalle: {e}")

if __name__ == "__main__":
    main()