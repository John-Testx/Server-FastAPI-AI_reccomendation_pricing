import pickle
import json
import pandas as pd
import numpy as np
import mysql.connector
import os # Para leer variables de entorno (más seguro)
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
load_dotenv()

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def get_freelancer_data_from_db():
    """
    Se conecta a la base de datos de Busquidy y obtiene los perfiles de todos los freelancers activos.
    """
    print("Conectando a la base de datos para obtener perfiles de freelancers...")
    try:
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)
        
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
        
        df = pd.read_sql(query, cnx)
        cnx.close()
        
        # Limpieza de datos
        df['habilidades'] = df['habilidades'].fillna('') # Rellenar nulos
        df['carrera'] = df['carrera'].fillna('')
        
        print(f"Se encontraron {len(df)} perfiles de freelancers en la base de datos.")
        return df

    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")
        return None

# --- API Y CARGA DE MODELOS (MODIFICADO) ---
app = FastAPI(title="API de Recomendación Busquidy")

vectorizer = None
profiles_matrix = None
df_freelancers_live = None

@app.on_event("startup")
def load_model_and_data():
    global vectorizer, profiles_matrix, df_freelancers_live
    try:
        print("Cargando artefactos del modelo (.pkl)...")
        vectorizer = pickle.load(open('tfidf_vectorizer.pkl', 'rb'))
        profiles_matrix = pickle.load(open('freelancer_profiles_matrix.pkl', 'rb'))
        
        # Obtenemos los freelancers desde la BD en lugar de un CSV
        df_freelancers_live = get_freelancer_data_from_db()

        if df_freelancers_live is None:
            raise ValueError("No se pudieron cargar los datos de freelancers desde la BD.")

        print("¡Modelos y datos de BD cargados correctamente!")

    except FileNotFoundError as e:
        print(f"Error al cargar archivos .pkl: {e}")
    except Exception as e:
        print(f"Ocurrió un error durante el inicio: {e}")


# El resto del archivo es casi igual...

class ProjectRequest(BaseModel):
    categoria_proyecto: str
    habilidades_requeridas: List[str] # Changed to a list of strings

@app.post("/recommend/")
async def get_recommendations(project: ProjectRequest):
    if vectorizer is None or profiles_matrix is None or df_freelancers_live is None:
        return {"error": "El sistema de recomendación no está listo. Revisa los logs."}

    # Crear el perfil de texto para el freelancer actual de la BD
    def crear_perfil_texto(row):
        habilidades_texto = row['habilidades'].replace(',', '') # Limpiar comas
        carrera_texto = row['carrera']
        return (habilidades_texto + ' ') * 3 + carrera_texto

    # Se recalcula el perfil de texto con los datos frescos de la BD
    live_profiles_text = df_freelancers_live.apply(crear_perfil_texto, axis=1)
    
    # ❗️ Importante: Usamos el vectorizador YA ENTRENADO para transformar los nuevos perfiles
    live_profiles_matrix = vectorizer.transform(live_profiles_text)

    # Crear el perfil del proyecto
    habilidades_texto = ' '.join(project.habilidades_requeridas)
    perfil_proyecto = (habilidades_texto + ' ') * 3 + project.categoria_proyecto
    proyecto_vector = vectorizer.transform([perfil_proyecto])
    
    # Calcular similitud contra los perfiles VIVOS de la BD
    similarities = cosine_similarity(proyecto_vector, live_profiles_matrix).flatten()
    
    top_indices = np.argsort(similarities)[-5:][::-1]
    
    # Mapear los índices a los IDs de freelancers reales de la BD
    recommended_ids = df_freelancers_live.iloc[top_indices]['id_freelancer'].tolist()

    return {"recommended_ids": recommended_ids}

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Recomendación de Busquidy"}