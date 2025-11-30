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

# Import the function from your new file
from database import get_freelancer_data_from_db

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
    print("SIMILITUDES AQUI WON",similarities)
    
    top_indices = np.argsort(similarities)[-5:][::-1]
    
    # Mapear los índices a los IDs de freelancers reales de la BD
    recommended_ids = df_freelancers_live.iloc[top_indices]['id_freelancer'].tolist()
    # print(f"Recomendaciones generadas para el proyecto: {recommended_ids}")

    return {"recommended_ids": recommended_ids}

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Recomendación de Busquidy"}