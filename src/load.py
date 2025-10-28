import pandas as pd
import os

# Importamos el directorio DW definido en extract.py
from .extract import DW_DIR

def load_to_csv(df, filename):
    """
    Guarda un DataFrame en un archivo .csv dentro del directorio DW.
    """
    try:
        # Asegurarse de que el directorio DW exista
        os.makedirs(DW_DIR, exist_ok=True)
        
        file_path = os.path.join(DW_DIR, filename)
        
        # Guardar el archivo sin el índice de pandas
        df.to_csv(file_path, index=False)
        print(f"  -> Datos guardados exitosamente en: {file_path}")
        
    except Exception as e:
        print(f"Error al guardar el archivo {filename}: {e}")

if __name__ == '__main__':
    # Prueba rápida de la función de carga
    print("Iniciando prueba de carga...")
    test_df = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']})
    load_to_csv(test_df, 'test_table.csv')
    print("Prueba de carga finalizada.")