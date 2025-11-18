import os
import minizinc
import plotly.express as px
import pandas as pd
import json
import glob  # <-- CAMBIO: Necesario para buscar archivos
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# --- Configuración de Flask ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MODEL_FOLDER'] = 'models/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Ruta Principal (GET y POST) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # --- CAMBIO: Obtener la lista de modelos .mzn disponibles ---
    # Busca todos los archivos que terminen en .mzn en la carpeta de modelos
    model_files_path = os.path.join(app.config['MODEL_FOLDER'], '*.mzn')
    model_files = glob.glob(model_files_path)
    # Extraemos solo el nombre del archivo (ej. 'jssp.mzn')
    model_list = [os.path.basename(f) for f in model_files]
    # --- Fin del cambio ---

    if request.method == 'POST':
        # 1. Manejar la carga del archivo .dzn
        if 'dzn_file' not in request.files:
            return redirect(request.url)
        
        file = request.files['dzn_file']
        if file.filename == '':
            return redirect(request.url)
        
        # --- CAMBIO: Obtener el modelo seleccionado del formulario ---
        selected_model_name = request.form.get('model_file')
        if not selected_model_name or selected_model_name not in model_list:
            # Si el modelo no es válido, recargar con error
            return render_template('index.html', 
                                   error="Modelo .mzn seleccionado no es válido.", 
                                   model_list=model_list)
        # --- Fin del cambio ---

        if file and file.filename.endswith('.dzn'):
            filename = secure_filename(file.filename)
            dzn_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(dzn_path)
            
            # --- CAMBIO: Usar el modelo seleccionado dinámicamente ---
            model_path = os.path.join(app.config['MODEL_FOLDER'], selected_model_name)
            # --- Fin del cambio ---
            
            try:
                # Configurar la instancia de MiniZinc
                gecode = minizinc.Solver.lookup("gecode")
                # El modelo se carga desde el model_path dinámico
                instance = minizinc.Instance(gecode, minizinc.Model(model_path))
                instance.add_file(dzn_path)
                
                # Resolver el problema
                result = instance.solve(timeout=timedelta(seconds=30))
                
                if result.solution:
                    # 3. Procesar la salida (Parser)
                    gantt_data = parse_solution_for_gantt(result)
                    
                    # 4. Generar visualización (Diagrama de Gantt)
                    graph_json = create_gantt_chart(gantt_data)
                    
                    # Renderizar la plantilla con los resultados
                    return render_template('index.html', 
                                           graph_json=graph_json, 
                                           makespan=result.solution.makespan,
                                           filename=filename,
                                           model_list=model_list, # <-- CAMBIO: Pasar lista
                                           selected_model=selected_model_name # <-- CAMBIO: Pasar selección
                                          )
                else:
                    error_msg = "No se encontró solución."
                    # <-- CAMBIO: Pasar model_list al renderizar error
                    return render_template('index.html', error=error_msg, model_list=model_list)
            
            except Exception as e:
                # <-- CAMBIO: Pasar model_list al renderizar error
                return render_template('index.html', error=str(e), model_list=model_list)

    # Método GET: Simplemente mostrar la página
    # <-- CAMBIO: Pasar la lista de modelos a la plantilla
    return render_template('index.html', model_list=model_list)

# --- (El resto de las funciones parse_solution_for_gantt y create_gantt_chart) ---
# --- (No necesitan cambios) ---

def parse_solution_for_gantt(result):
    """ Convierte la salida de MiniZinc en un formato listo para Plotly. """
    data = []
    
    # Extraer los datos de la solución
    starts = result.solution.start
    durations = result.solution.duration
    machines = result.solution.machines
    n_jobs, n_ops = len(starts), len(starts[0])

    # Usamos una fecha base arbitraria para el Gantt
    base_time = datetime(2025, 1, 1) 

    for j in range(n_jobs):
        for o in range(n_ops):
            start_time = starts[j][o]
            duration = durations[j][o]
            machine = machines[j][o]
            
            data.append(dict(
                Task=f"Máquina {machine}", 
                Start=base_time + timedelta(seconds=int(start_time)),
                Finish=base_time + timedelta(seconds=int(start_time + duration)),
                Resource=f"Trabajo {j + 1}"
            ))
    return data

def create_gantt_chart(data):
    """ Genera el JSON del diagrama de Gantt usando Plotly Express. """
    df = pd.DataFrame(data)
    
    fig = px.timeline(df, 
                      x_start="Start", 
                      x_end="Finish", 
                      y="Task", 
                      color="Resource",
                      title="Diagrama de Gantt (Job Shop Scheduling)")
    
    fig.update_yaxes(autorange="reversed") 
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


if __name__ == '__main__':
    app.run(debug=True)