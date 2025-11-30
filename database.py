import os
import pandas as pd
import mysql.connector # For Local
import pymysql # For Cloud
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector, IPTypes

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    Returns a database connection object based on DB_ENV.
    """
    db_env = os.getenv("DB_ENV", "local")
    db_name = os.getenv("DB_NAME")

    if db_env == "cloud":
        print(f"-> Connecting to CLOUD ({os.getenv('DB_INSTANCE_CONNECTION_NAME')})...")
        
        instance_connection_name = os.getenv("DB_INSTANCE_CONNECTION_NAME")
        db_user = os.getenv("DB_USER_CLOUD")
        db_pass = os.getenv("DB_PASSWORD_CLOUD")
        
        # Initialize the connector (uses GOOGLE_APPLICATION_CREDENTIALS automatically)
        connector = Connector()
        
        conn = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PUBLIC 
        )
        return conn

    else:
        print("-> Connecting to LOCAL DB...")
        
        return mysql.connector.connect(
            host=os.getenv("DB_HOST_LOCAL"),
            user=os.getenv("DB_USER_LOCAL"),
            password=os.getenv("DB_PASSWORD_LOCAL"),
            database=db_name,
            port=3306
        )

def get_freelancer_data_from_db():
    """
    Se conecta a la base de datos de Busquidy y obtiene los perfiles de todos los freelancers activos.
    """
    print("Starting freelancer data load...")
    cnx = None
    try:
        cnx = get_db_connection()
        
        # Esta consulta une las tablas para obtener las habilidades y carrera de cada freelancer
        query = """
        SELECT 
            f.id_freelancer,
            es.carrera,
            GROUP_CONCAT(h.habilidad SEPARATOR ', ') AS habilidades
        FROM freelancer f
        JOIN usuario u ON f.id_usuario = u.id_usuario
        LEFT JOIN educacion_superior es ON f.id_freelancer = es.id_freelancer
        LEFT JOIN habilidades h ON f.id_freelancer = h.id_freelancer
        WHERE u.is_active = TRUE
        GROUP BY f.id_freelancer, es.carrera;
        """
        
        # Pandas works with both connection types
        df = pd.read_sql(query, cnx)
        
        # Data cleaning
        df['habilidades'] = df['habilidades'].fillna('')
        df['carrera'] = df['carrera'].fillna('')
        
        print(f"✅ Found {len(df)} freelancer profiles.")
        return df

    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        if cnx and hasattr(cnx, 'close'):
            cnx.close()