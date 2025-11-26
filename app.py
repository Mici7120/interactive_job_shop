from flask import Flask, render_template, request, jsonify
from minizinc import Instance, Model, Solver
from datetime import timedelta
import re
import os

app = Flask(__name__)
gecode = Solver.lookup("gecode")

MODELS = {
    "operarios": "job_shop-operarios.mzn",
    "mantenimiento": "job_shop-mantenimiento.mzn"
}

# --- Funciones de Parseo ---

def parse_operarios_output(output):
    results = {}
    
    # Extraer makespan y balance
    makespan_match = re.search(r'makespan=(\d+);', output)
    balance_match = re.search(r'balance=(\d+);', output)
    
    if makespan_match:
        results['makespan'] = int(makespan_match.group(1))
    if balance_match:
        results['balance'] = int(balance_match.group(1))

    # Extraer las tareas
    task_data_raw = re.findall(r'\((.+?)\)', output)
    results['tasks'] = []
    
    # Formato: (job,task,operator,start,finish,machine)
    for task_raw in task_data_raw:
        parts = [int(p.strip()) for p in task_raw.split(',')]
        if len(parts) == 6:
            results['tasks'].append({
                'Job': parts[0],
                'Task': parts[1],
                'Operator': parts[2],
                'Start': parts[3],
                'Finish': parts[4],
                'Machine': parts[5]
            })
    return results

def parse_mantenimiento_output(output):
    """Parsea la salida del modelo de mantenimiento."""
    results = {'maint_intervals': []}
    
    # Extraer makespan
    makespan_match = re.search(r'makespan=(\d+);', output)
    if makespan_match:
        results['makespan'] = int(makespan_match.group(1))

    # Extraer las operaciones
    ops_data_raw = re.findall(r'operaciones=\[([\s\S]*?)\];', output)[0]
    ops_list_raw = re.findall(r'\((.+?)\)', ops_data_raw)
    results['tasks'] = []
    
    # Formato: (job,op,start,end,machine)
    for op_raw in ops_list_raw:
        parts = [int(p.strip()) for p in op_raw.split(',')]
        if len(parts) == 5:
            results['tasks'].append({
                'Job': parts[0],
                'Operation': parts[1],
                'Start': parts[2],
                'Finish': parts[3],
                'Machine': parts[4]
            })

    # Extraer el mantenimiento
    maint_data_raw = re.findall(r'mantenimiento=\[([\s\S]*?)\];', output)[0]
    maint_list_raw = re.findall(r'\((.+?)\)', maint_data_raw)
    
    # Formato: (machine,start,end)
    for maint_raw in maint_list_raw:
        parts = [int(p.strip()) for p in maint_raw.split(',')]
        if len(parts) == 3:
            results['maint_intervals'].append({
                'Machine': parts[0],
                'Start': parts[1],
                'Finish': parts[2]
            })

    return results

# Rutas Flask

@app.route('/')
def index():
    return render_template('index.html', models=MODELS.keys())

@app.route('/execute', methods=['POST'])
def execute_model():
    model_name = request.form.get('model_name')
    data_content = request.form.get('data_content')
    
    if model_name not in MODELS:
        return jsonify({'error': 'Modelo no válido'}), 400

    mzn_file = MODELS[model_name]
    
    try:
        model = Model(mzn_file)
        
        instance = Instance(gecode, model)
        
        # Crear un archivo .dzn temporal para cargar los datos
        temp_dzn_path = f"temp_data_{model_name}.dzn"
        with open(temp_dzn_path, 'w') as f:
            f.write(data_content)
            
        instance.add_file(temp_dzn_path)
        
        result = instance.solve(timeout=timedelta(seconds=30))
        raw_output = str(result)
        
        if model_name == "operarios":
            parsed_data = parse_operarios_output(raw_output)
        elif model_name == "mantenimiento":
            parsed_data = parse_mantenimiento_output(raw_output)
        else:
            parsed_data = {"message": "Modelo desconocido."}

        # Eliminar el archivo temporal
        os.remove(temp_dzn_path)

        return jsonify({'success': True, 'model': model_name, 'data': parsed_data})

    except Exception as e:
        # Intentar eliminar el archivo temporal si existe
        if 'temp_dzn_path' in locals() and os.path.exists(temp_dzn_path):
            os.remove(temp_dzn_path)
        return jsonify({'error': f"Error al ejecutar MiniZinc: {str(e)}", 'raw_output': raw_output if 'raw_output' in locals() else 'N/A'}), 500

if __name__ == '__main__':
    app.run(debug=True)