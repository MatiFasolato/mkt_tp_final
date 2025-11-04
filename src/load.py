import pandas as pd
import os

# Importamos el directorio DW definido en extract.py
from .extract import DW_DIR

def load_to_csv(df, filename):
    """
    Guarda un DataFrame en un archivo .csv dentro del directorio DW.
    FORZANDO el punto (.) como separador decimal.
    """
    try:
        # Asegurarse de que el directorio DW exista
        os.makedirs(DW_DIR, exist_ok=True)
        
        file_path = os.path.join(DW_DIR, filename)
        
        # --- ¡LA SOLUCIÓN! ---
        # Añadimos decimal='.' para asegurar que 1200.0 se guarde como '1200.0'
        # y no como '1200,0', que es lo que confunde a Power BI.
        df.to_csv(
            file_path, 
            index=False, 
            decimal='.',  # <--- ESTA ES LA LÍNEA QUE LO ARREGLA TODO
            encoding='utf-8' # (Buena práctica añadir encoding también)
        )
        # --- FIN DE LA SOLUCIÓN ---
        
        print(f"   -> Datos guardados exitosamente en: {file_path}")
        
    except Exception as e:
        print(f"Error al guardar el archivo {filename}: {e}")

if __name__ == '__main__':
    # Prueba rápida de la función de carga
    print("Iniciando prueba de carga...")
    # Prueba con un número decimal para ver el efecto
    test_df = pd.DataFrame({'col1': [1.5, 2.0], 'col2': ['A', 'B']})
    load_to_csv(test_df, 'test_table.csv')
    print("Prueba de carga finalizada.")
    print(f"Revisa {os.path.join(DW_DIR, 'test_table.csv')} y confirma que usa '.' (punto) decimal.")