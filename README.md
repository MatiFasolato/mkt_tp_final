# TP Final: Ecosistema de Datos de Marketing (EcoBottle)

Proyecto final para la materia "Introducción al Marketing Online y los Negocios Digitales". El objetivo es diseñar e implementar un mini-ecosistema de datos comercial (online + offline) para la empresa ficticia **EcoBottle**.

El pipeline completo ingesta datos crudos (desde `raw/`), los transforma usando Python y Pandas (desde `src/`) para crear un Data Warehouse dimensional (en `DW/`). Finalmente, los datos están listos para presentar los KPIs clave en un dashboard.

**Dashboard Final (Looker Studio):** `[...]`

---

## Herramientas Utilizadas

- **Python 3.10+**
- **Pandas:** Para toda la lógica de extracción, transformación y carga (ETL).
- **Git / GitHub:** Para control de versiones y gestión del proyecto.
- **Looker Studio:** Para la visualización y el dashboard de KPIs.

---

## Diagrama Entidad Relación - OLTP (Fuente)

A continuación, se presenta el modelado de la base de datos transaccional (OLTP) original desde donde provienen los datos de la carpeta `raw/`.

_(Asumiendo que guardaste tu imagen `DER.jpg` en una carpeta `assets/` como en el ejemplo)_
`![Diagrama Entidad Relación](./assets/DER.jpg)`

---

## Arquitectura del Proyecto

El proyecto sigue una estructura ETL clásica, pero optimizada para este trabajo:

1.  **`raw/`**: Contiene los 13 archivos `.CSV` fuente que simulan la base de datos transaccional (OLTP) de EcoBottle.
2.  **`src/`**: Contiene toda la lógica de transformación del pipeline, separada en módulos:
    - **`src/extract.py`**: Función para leer los 13 CSVs desde la carpeta `raw/`.
    - **`src/transform.py`**: Contiene toda la lógica para limpiar, desnormalizar y construir cada una de las 6 tablas de Dimensión y 6 de Hechos, implementando Surrogate Keys (SKs) y manejando miembros desconocidos.
    - **`src/load.py`**: Función para guardar los 12 DataFrames transformados en el directorio `DW/`.
    - **`src/__init__.py`**: Permite que `src/` sea tratado como un paquete de Python.
3.  **`DW/`**: Es el Data Warehouse (Data Mart) de salida. Los 12 archivos `.CSV` en esta carpeta están limpios, modelados y listos para ser consumidos por Looker Studio.
4.  **`main.py`**: El script orquestador que llama a las funciones de `extract`, `transform` y `load` en el orden correcto para ejecutar el pipeline completo.
5.  **`requirements.txt`**: Define las dependencias de Python (ej. `pandas`) necesarias para correr el proyecto.

---

## Instrucciones de Ejecución Local

Sigue estos pasos para ejecutar el pipeline de transformación ETL en tu máquina:

1.  **Clonar el repositorio:**

    ```bash
    git clone [URL-DE-TU-REPOSITORIO-GIT]
    cd mkt_tp_final
    ```

2.  **Crear y activar un entorno virtual**:
    _(Usamos `venv` como definimos en nuestro proyecto)_

    ```bash
    # En Windows (cmd/powershell)
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar el pipeline de transformación:**
    El script `main.py` en la raíz del proyecto orquesta todo el proceso.

    ```bash
    python main.py
    ```

5.  **Verificar la salida:**
    Tras la ejecución, la carpeta `DW/` (Data Warehouse) deberá contener los 12 archivos `.CSV` transformados, listos para subir a Looker Studio.

---

## Modelo de Datos (Diccionario de Datos)

El Data Warehouse (`DW/`) se compone de un Esquema de Constelación con 6 Dimensiones y 6 Tablas de Hechos.

### Dimensiones (`DW/`)

Las dimensiones responden al **quién, qué, dónde y cuándo** del análisis.

#### `Dim_Fecha`

_(Generada en Python) Contiene todos los atributos de fecha para el análisis. La `fecha_key = 0` representa fechas desconocidas._

| Nombre de Columna | Descripción                                             | Tipo de Dato         |
| :---------------- | :------------------------------------------------------ | :------------------- |
| **fecha_key**     | **Clave Primaria (PK)** inteligente (Formato YYYYMMDD). | `INT`                |
| fecha_completa    | La fecha completa.                                      | `DATE` / `TIMESTAMP` |
| año               | Año (ej. 2024).                                         | `INT`                |
| mes               | Número de mes (1-12).                                   | `INT`                |
| mes_nombre        | Nombre del mes (ej. January).                           | `VARCHAR`            |
| dia               | Número de día (1-31).                                   | `INT`                |
| dia_semana        | Día de la semana (0=Lunes, 6=Domingo).                  | `INT`                |
| trimestre         | Trimestre del año (1-4).                                | `INT`                |

#### `Dim_Cliente`

_Describe a los clientes. La `cliente_sk = -1` representa clientes desconocidos o anónimos._

| Nombre de Columna | Descripción                              | Tipo de Dato   |
| :---------------- | :--------------------------------------- | :------------- |
| **cliente_sk**    | **Clave Primaria (PK)** sustituta.       | `INT`          |
| customer_id       | Clave Natural (NK) del sistema original. | `INT`          |
| email             | Email del cliente.                       | `VARCHAR(120)` |
| first_name        | Nombre del cliente.                      | `VARCHAR(80)`  |
| last_name         | Apellido del cliente.                    | `VARCHAR(80)`  |
| status            | Estado del cliente (ej. 'A' por Activo). | `CHAR(1)`      |

#### `Dim_Canal`

_Describe los canales de venta. La `canal_sk = -1` representa canales desconocidos._

| Nombre de Columna | Descripción                                 | Tipo de Dato  |
| :---------------- | :------------------------------------------ | :------------ |
| **canal_sk**      | **Clave Primaria (PK)** sustituta.          | `INT`         |
| channel_id        | Clave Natural (NK) del sistema original.    | `INT`         |
| code              | Código del canal (ej. 'ONLINE', 'OFFLINE'). | `VARCHAR(20)` |
| canal_nombre      | Nombre descriptivo del canal.               | `VARCHAR(50)` |

#### `Dim_Geografia`

_Describe las ubicaciones (direcciones), desnormalizando `address` y `province`. La `geografia_sk = -1` representa ubicaciones desconocidas._

| Nombre de Columna | Descripción                         | Tipo de Dato   |
| :---------------- | :---------------------------------- | :------------- |
| **geografia_sk**  | **Clave Primaria (PK)** sustituta.  | `INT`          |
| address_id        | Clave Natural (NK) de la dirección. | `INT`          |
| line1             | Línea 1 de la dirección.            | `VARCHAR(120)` |
| city              | Ciudad.                             | `VARCHAR(80)`  |
| postal_code       | Código Postal.                      | `VARCHAR(20)`  |
| provincia_nombre  | Nombre de la provincia.             | `VARCHAR(50)`  |
| provincia_code    | Código de la provincia.             | `VARCHAR(10)`  |

#### `Dim_Producto`

_Describe los productos, desnormalizando `product` y `product_category`. El `producto_sk = -1` representa productos desconocidos._

| Nombre de Columna | Descripción                               | Tipo de Dato    |
| :---------------- | :---------------------------------------- | :-------------- |
| **producto_sk**   | **Clave Primaria (PK)** sustituta.        | `INT`           |
| product_id        | Clave Natural (NK) del producto.          | `INT`           |
| sku               | Código SKU del producto.                  | `VARCHAR(40)`   |
| producto_nombre   | Nombre del producto.                      | `VARCHAR(120)`  |
| list_price        | Precio de lista del producto.             | `DECIMAL(12,2)` |
| producto_status   | Estado del producto (ej. 'A' por Activo). | `CHAR(1)`       |
| categoria_nombre  | Nombre de la categoría del producto.      | `VARCHAR(80)`   |

#### `Dim_Tienda`

_Describe las tiendas físicas. La `tienda_sk = -1` representa "Sin Tienda" (ej. pedidos ONLINE)._

| Nombre de Columna | Descripción                         | Tipo de Dato  |
| :---------------- | :---------------------------------- | :------------ |
| **tienda_sk**     | **Clave Primaria (PK)** sustituta.  | `INT`         |
| store_id          | Clave Natural (NK) de la tienda.    | `INT`         |
| tienda_nombre     | Nombre de la tienda.                | `VARCHAR(80)` |
| provincia_nombre  | Provincia donde se ubica la tienda. | `VARCHAR(50)` |
| city              | Ciudad donde se ubica la tienda.    | `VARCHAR(80)` |

---

### Tablas de Hechos (`DW/`)

Las tablas de hechos contienen las **métricas** y las claves foráneas (FKs) que las conectan a las dimensiones.

#### `Fact_Pedidos`

- [cite_start]**Grano:** Una fila por cabecera de pedido (órdenes con status 'PAID' o 'FULFILLED' [cite: 169-170]).
- [cite_start]**Propósito:** Base para KPIs de Ventas Totales ($M), Ticket Promedio ($K) y Ventas por Provincia [cite: 169-170, 173, 175].

| Nombre de Columna | Descripción                                   | Tipo de Dato    |
| :---------------- | :-------------------------------------------- | :-------------- |
| **pedido_sk**     | **Clave Primaria (PK)** sustituta.            | `INT`           |
| fecha_key         | Clave Foránea (FK) a `Dim_Fecha`.             | `INT`           |
| cliente_sk        | Clave Foránea (FK) a `Dim_Cliente`.           | `INT`           |
| canal_sk          | Clave Foránea (FK) a `Dim_Canal`.             | `INT`           |
| geografia_sk      | Clave Foránea (FK) a `Dim_Geografia` (envío). | `INT`           |
| tienda_sk         | Clave Foránea (FK) a `Dim_Tienda`.            | `INT`           |
| order_id          | Dimensión Degenerada (NK del pedido).         | `BIGINT`        |
| subtotal          | Métrica: Monto antes de impuestos/envío.      | `DECIMAL(12,2)` |
| tax_amount        | Métrica: Monto de impuestos.                  | `DECIMAL(12,2)` |
| shipping_fee      | Métrica: Costo de envío.                      | `DECIMAL(12,2)` |
| total_amount      | Métrica: Monto total pagado.                  | `DECIMAL(12,2)` |

#### `Fact_Ventas_Items`

- **Grano:** Una fila por ítem (producto) dentro de un pedido válido.
- **Propósito:** Base para el KPI de Ranking mensual por Producto.

| Nombre de Columna  | Descripción                                         | Tipo de Dato    |
| :----------------- | :-------------------------------------------------- | :-------------- |
| **ventas_item_sk** | **Clave Primaria (PK)** sustituta.                  | `INT`           |
| fecha_key          | Clave Foránea (FK) a `Dim_Fecha`.                   | `INT`           |
| producto_sk        | Clave Foránea (FK) a `Dim_Producto`.                | `INT`           |
| order_item_id      | Dimensión Degenerada (NK del ítem).                 | `BIGINT`        |
| order_id           | Dimensión Degenerada (NK del pedido).               | `BIGINT`        |
| quantity           | Métrica: Cantidad de unidades vendidas.             | `INT`           |
| unit_price         | Métrica: Precio por unidad.                         | `DECIMAL(12,2)` |
| discount_amount    | Métrica: Descuento aplicado al ítem.                | `DECIMAL(12,2)` |
| line_total         | Métrica: Total de la línea (cant \* precio - desc). | `DECIMAL(12,2)` |

#### `Fact_Pagos`

- **Grano:** Una fila por transacción de pago.
- **Propósito:** Análisis financiero y de cobranza.

| Nombre de Columna | Descripción                                       | Tipo de Dato    |
| :---------------- | :------------------------------------------------ | :-------------- |
| **pago_sk**       | **Clave Primaria (PK)** sustituta.                | `INT`           |
| fecha_key         | Clave Foránea (FK) a `Dim_Fecha` (fecha de pago). | `INT`           |
| payment_id        | Dimensión Degenerada (NK del pago).               | `BIGINT`        |
| order_id          | Dimensión Degenerada (NK del pedido).             | `BIGINT`        |
| amount            | Métrica: Monto del pago.                          | `DECIMAL(12,2)` |
| method            | Atributo/Dimensión Degenerada (método).           | `VARCHAR(20)`   |
| status            | Atributo/Dimensión Degenerada (estado).           | `VARCHAR(20)`   |

#### `Fact_Envios`

- **Grano:** Una fila por envío.
- **Propósito:** Análisis de logística y tiempos de entrega.

| Nombre de Columna   | Descripción                                         | Tipo de Dato  |
| :------------------ | :-------------------------------------------------- | :------------ |
| **envio_sk**        | **Clave Primaria (PK)** sustituta.                  | `INT`         |
| fecha_key_shipped   | FK a `Dim_Fecha` (Rol: Fecha de Despacho).          | `INT`         |
| fecha_key_delivered | FK a `Dim_Fecha` (Rol: Fecha de Entrega).           | `INT`         |
| shipment_id         | Dimensión Degenerada (NK del envío).                | `BIGINT`      |
| order_id            | Dimensión Degenerada (NK del pedido).               | `BIGINT`      |
| dias_de_entrega     | Métrica: Días entre despacho y entrega (Calculada). | `INT`         |
| carrier             | Atributo/Dimensión Degenerada (transportista).      | `VARCHAR(40)` |
| status              | Atributo/Dimensión Degenerada (estado).             | `VARCHAR(20)` |

#### `Fact_Sesiones`

- **Grano:** Una fila por sesión web.
- [cite_start]**Propósito:** Base para el KPI de Usuarios Activos (nK) [cite: 171-172].

| Nombre de Columna | Descripción                                          | Tipo de Dato  |
| :---------------- | :--------------------------------------------------- | :------------ |
| **session_sk**    | **Clave Primaria (PK)** sustituta.                   | `INT`         |
| fecha_key         | Clave Foránea (FK) a `Dim_Fecha` (inicio de sesión). | `INT`         |
| cliente_sk        | Clave Foránea (FK) a `Dim_Cliente`.                  | `INT`         |
| session_id        | Dimensión Degenerada (NK de la sesión).              | `BIGINT`      |
| source            | Atributo/Dimensión Degenerada (fuente de tráfico).   | `VARCHAR(50)` |
| device            | Atributo/Dimensión Degenerada (dispositivo).         | `VARCHAR(30)` |

#### `Fact_NPS`

- **Grano:** Una fila por respuesta de encuesta NPS.
- **Propósito:** Base para el KPI de NPS (Net Promoter Score).

| Nombre de Columna | Descripción                                            | Tipo de Dato |
| :---------------- | :----------------------------------------------------- | :----------- |
| **nps_sk**        | **Clave Primaria (PK)** sustituta.                     | `INT`        |
| fecha_key         | Clave Foránea (FK) a `Dim_Fecha` (fecha de respuesta). | `INT`        |
| cliente_sk        | Clave Foránea (FK) a `Dim_Cliente`.                    | `INT`        |
| canal_sk          | Clave Foránea (FK) a `Dim_Canal`.                      | `INT`        |
| nps_id            | Dimensión Degenerada (NK de la respuesta).             | `BIGINT`     |
| score             | Métrica: Puntaje (0-10) dado por el cliente.           | `SMALLINT`   |
