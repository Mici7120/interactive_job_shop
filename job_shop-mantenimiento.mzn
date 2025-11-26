% ---------- PARÁMETROS ----------
int: n_jobs;            % Número de trabajos
int: n_machines;        % Número de máquinas

% Cada trabajo puede tener diferente número de operaciones
array [1..n_jobs] of int: n_ops_for;

% Número máximo de operaciones entre todos los trabajos (para definir dimensiones)
int: max_ops = max(n_ops_for);

% Duración de cada operación
% Si un trabajo tiene menos operaciones que max_ops, deja dur[j][t] = 0 para las que no existen
array [1..n_jobs, 1..max_ops] of int: dur;

% Máquina asignada a cada operación
array [1..n_jobs, 1..max_ops] of int: machine_for;

% Intervalos de mantenimiento (un intervalo por máquina)
array [1..n_machines] of int: maint_start;
array [1..n_machines] of int: maint_end;


% ---------- HORIZONTE DE TIEMPO ----------
int: horizon =
    sum(j in 1..n_jobs, t in 1..n_ops_for[j])(dur[j,t]) +
    max([maint_end[m] | m in 1..n_machines]);

% ---------- VARIABLES ----------
% Tiempos de inicio y fin para cada operación
array [1..n_jobs, 1..max_ops] of var 0..horizon: start;
array [1..n_jobs, 1..max_ops] of var 0..horizon: end_time;

% Makespan total (tiempo de finalización del último trabajo)
var 0..horizon: makespan;

% ---------- RELACIONES BÁSICAS ----------
% Relación entre inicio y fin
constraint forall(j in 1..n_jobs, t in 1..n_ops_for[j]) (
    end_time[j,t] = start[j,t] + dur[j,t]
);

% Definición del makespan (máximo fin entre todas las operaciones)
constraint makespan = max([ end_time[j,t] | j in 1..n_jobs, t in 1..n_ops_for[j] ]);

% ---------- RESTRICCIONES ----------
% Precedencia: las operaciones de un mismo trabajo deben ejecutarse en orden
constraint
  forall(j in 1..n_jobs, t in 1..(n_ops_for[j]-1)) (
    end_time[j,t] <= start[j,t+1]
  );

% No solapamiento en la misma máquina
constraint
  forall(j1 in 1..n_jobs, t1 in 1..n_ops_for[j1],
         j2 in 1..n_jobs, t2 in 1..n_ops_for[j2]
         where (j1,t1) < (j2,t2) /\ machine_for[j1,t1] = machine_for[j2,t2]) (
    (end_time[j1,t1] <= start[j2,t2]) \/ (end_time[j2,t2] <= start[j1,t1])
  );

% Mantenimiento: ninguna operación puede solaparse con los intervalos [maint_start, maint_end)
constraint
  forall(j in 1..n_jobs, t in 1..n_ops_for[j]) (
    let { int: m = machine_for[j,t] } in
      (end_time[j,t] <= maint_start[m]) \/ (start[j,t] >= maint_end[m])
  );

%  para cotar el dominio
constraint
  forall(j in 1..n_jobs, t in 1..n_ops_for[j]) (
    start[j,t] <= horizon - dur[j,t]
  );

% ---------- FUNCIÓN OBJETIVO ----------
solve :: int_search([ start[j,t] | j in 1..n_jobs, t in 1..n_ops_for[j] ],
                    smallest, indomain_min, complete) %aqui se puede porbar con first_fail o smallest
       minimize makespan;

% --- OUTPUT MODIFICADO PARA PARSEO ---
output [
  "---RESULTADOS---\n",
  "makespan=\(makespan);\n",
  "operaciones=[\n"
] ++
  [
    if dur[j,t] > 0 then
      "(\(j),\(t),\(start[j,t]),\(end_time[j,t]),\(machine_for[j,t]))"
    else ""
    endif
    | j in 1..n_jobs, t in 1..n_ops_for[j]
  ]
++ [
  "\n];\n",
  "mantenimiento=[\n"
] ++
[
  "(\(m),\(maint_start[m]),\(maint_end[m]))"
  | m in 1..n_machines
] ++ [
  "\n];\n",
  "---FIN---"
];
