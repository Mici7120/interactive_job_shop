int: jobs;                     % número de trabajos
set of int: JOB = 1..jobs;

int: tasks;                    % número de tareas por trabajo
set of int: TASK = 1..tasks;

int: machines;                 % número de máquinas
set of int: MACH = 1..machines;

int: operators;                % número de operarios disponibles
set of int: OPER = 1..operators;

array [JOB,TASK] of int: d;    % duración de cada tarea
array [JOB,TASK] of int: m;    % máquina requerida para cada tarea

int: total = sum(i in JOB, j in TASK)(d[i,j]);

array [JOB,TASK] of var 0..total: s;     % tiempo de inicio
array [JOB,TASK] of var 0..total: f;     % tiempo de fin
array [JOB,TASK] of var OPER: o;         % operario asignado a cada tarea
var 0..total: end;                       % makespan

% Relación entre inicio, fin y duración
constraint forall(i in JOB, j in TASK) (
    f[i,j] = s[i,j] + d[i,j]
);

% Restricciones de precedencia dentro de cada trabajo
constraint forall(i in JOB, j in 1..tasks-1) (
    f[i,j] <= s[i,j+1]
);

% Restricciones de no solapamiento por máquina
predicate no_overlap(var int:s1, int:d1, var int:s2, int:d2) =
    s1 + d1 <= s2 \/ s2 + d2 <= s1;

constraint forall(j in TASK, i1,i2 in JOB where i1 < i2) (
    if m[i1,j] = m[i2,j] then
        no_overlap(s[i1,j], d[i1,j], s[i2,j], d[i2,j])
    endif
);

% Restricciones de operarios: no pueden hacer tareas simultáneas
constraint forall(o1 in OPER) (
    forall(i1,i2 in JOB, j1 in TASK, j2 in TASK where (i1,j1) < (i2,j2)) (
        (o[i1,j1] = o1 /\ o[i2,j2] = o1) ->
        no_overlap(s[i1,j1], d[i1,j1], s[i2,j2], d[i2,j2])
    )
);

% Cada tarea debe terminar antes del makespan
constraint forall(i in JOB, j in TASK) (f[i,j] <= end);

% Balancear la carga de trabajo de los operarios
array [OPER] of var 0..total: carga;
constraint forall(o1 in OPER)(
    carga[o1] = sum(i in JOB, j in TASK where o[i,j] = o1)(d[i,j])
);

var int: max_carga = max(o1 in OPER)(carga[o1]);
var int: min_carga = min(o1 in OPER)(carga[o1]);
var int: balance = max_carga - min_carga;

solve :: int_search(
    [s[i,j] | i in JOB, j in TASK] ++ [o[i,j] | i in JOB, j in TASK],
    first_fail,  %-----------Aqui se cambia a first_fail o smallest
    indomain_min,
    complete
) minimize end + balance;


% --- OUTPUT MODIFICADO PARA PARSEO ---
output [
  "---RESULTADOS---\n",
  "makespan=\(end);\n",
  "balance=\(balance);\n",
  "tareas_operarios=[\n"
] ++
[
  "(\(i),\(j),\(o[i,j]),\(s[i,j]),\(f[i,j]),\(m[i,j]))"
  | i in JOB, j in TASK
] ++ [
  "\n];\n",
  "---FIN---"
];
