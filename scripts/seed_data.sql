-- ============================================================
-- DATOS SEMILLA — ms-auditoria [AUD]
-- Base de datos: db_auditoria / ms_auditoria
-- Fuente: modelo-datos-ms-auditoria.md §7
-- ============================================================

-- ------------------------------------------------------------
-- aud_configuracion_retencion
-- Singleton operativo: un registro activo y tres inactivos
-- que representan configuraciones anteriores o alternativas.
-- ------------------------------------------------------------
INSERT INTO aud_configuracion_retencion
    (dias_retencion, estado, ultima_rotacion, registros_eliminados_ultima, created_at, updated_at)
VALUES
    -- 1. Configuración activa: valor por defecto del sistema (30 días)
    (30,  'activo',   '2026-02-01 03:00:00+00', 15842, NOW(), NOW()),
    -- 2. Configuración inactiva: usada anteriormente con retención extendida
    (60,  'inactivo', '2026-01-01 03:00:00+00', 8210,  NOW(), NOW()),
    -- 3. Configuración inactiva: retención corta para entorno de pruebas
    (7,   'inactivo', NULL,                      0,     NOW(), NOW()),
    -- 4. Configuración inactiva: retención extendida para cumplimiento normativo
    (365, 'inactivo', NULL,                      0,     NOW(), NOW());


-- ------------------------------------------------------------
-- aud_eventos_log
-- Cubre distintos microservicios, métodos, códigos de respuesta,
-- trazas multi-servicio (mismo request_id) y operaciones con y sin usuario.
--
-- IDs de usuario ficticios (REFERENCIAS EXTERNAS):
--   'usr-0001-uuid-admin'    → Usuario administrador    — ms-usuarios
--   'usr-0002-uuid-docente'  → Usuario docente          — ms-usuarios
--   'usr-0003-uuid-student'  → Usuario estudiante       — ms-usuarios
--   NULL                     → Operación de sistema (scheduler, rotación, etc.)
-- ------------------------------------------------------------
INSERT INTO aud_eventos_log
    (request_id, fecha_hora, microservicio, funcionalidad,
     metodo, codigo_respuesta, duracion_ms, usuario_id, detalle,
     created_at, updated_at)
VALUES
    -- 1. Login exitoso — ms-autenticacion
    ('a1b2c3d4-0001-0001-0001-000000000001',
     '2026-02-15 08:05:12+00', 'ms-autenticacion', 'login',
     'POST', 200, 145, 'usr-0001-uuid-admin',
     'Inicio de sesión exitoso para usuario administrador.',
     NOW(), NOW()),

    -- 2. Misma traza en ms-roles (mismo request_id → traza completa)
    ('a1b2c3d4-0001-0001-0001-000000000001',
     '2026-02-15 08:05:12+00', 'ms-roles', 'verificar_permisos',
     'GET', 200, 32, 'usr-0001-uuid-admin',
     'Permisos verificados para rol ADMIN.',
     NOW(), NOW()),

    -- 3. Creación de reserva exitosa — ms-reservas (201 Created)
    ('b2c3d4e5-0002-0002-0002-000000000002',
     '2026-02-15 09:30:45+00', 'ms-reservas', 'crear_reserva',
     'POST', 201, 312, 'usr-0002-uuid-docente',
     'Reserva creada para espacio A-101, fecha 2026-02-20.',
     NOW(), NOW()),

    -- 4. Error de validación — ms-inventario (400 Bad Request)
    ('c3d4e5f6-0003-0003-0003-000000000003',
     '2026-02-15 10:15:00+00', 'ms-inventario', 'registrar_salida',
     'POST', 400, 78, 'usr-0001-uuid-admin',
     'Stock insuficiente para el item solicitado.',
     NOW(), NOW()),

    -- 5. Error interno de servidor — ms-facturacion (500)
    ('d4e5f6a7-0004-0004-0004-000000000004',
     '2026-02-15 11:00:00+00', 'ms-facturacion', 'generar_factura',
     'POST', 500, 2340, 'usr-0003-uuid-student',
     'Error al conectar con el proveedor de firma electrónica.',
     NOW(), NOW()),

    -- 6. Operación de sistema sin usuario — ms-reportes (scheduler nocturno)
    ('e5f6a7b8-0005-0005-0005-000000000005',
     '2026-02-15 03:00:00+00', 'ms-reportes', 'generar_reporte_diario',
     'POST', 200, 8920, NULL,
     'Reporte diario generado automáticamente por scheduler.',
     NOW(), NOW()),

    -- 7. Auto-auditoría: ms-auditoria registra su propia rotación automática
    ('f6a7b8c9-0006-0006-0006-000000000006',
     '2026-02-15 03:05:00+00', 'ms-auditoria', 'ejecutar_rotacion',
     'POST', 200, 4521, NULL,
     'Rotación automática ejecutada. 15842 registros eliminados.',
     NOW(), NOW()),

    -- 8. Consulta de logs paginada — ms-auditoria (auto-auditoría de consulta)
    ('a7b8c9d0-0007-0007-0007-000000000007',
     '2026-02-15 14:22:10+00', 'ms-auditoria', 'consultar_logs',
     'GET', 200, 89, 'usr-0001-uuid-admin',
     'Consulta de logs filtrada por ms-reservas, página 1.',
     NOW(), NOW()),

    -- 9. Actualización parcial — ms-matriculas (PATCH exitoso)
    ('b8c9d0e1-0008-0008-0008-000000000008',
     '2026-02-16 07:45:00+00', 'ms-matriculas', 'actualizar_estado_matricula',
     'PATCH', 200, 210, 'usr-0001-uuid-admin',
     'Matrícula MAT-2026-0042 cambiada a estado activa.',
     NOW(), NOW()),

    -- 10. Acceso no autorizado — ms-calificaciones (403 Forbidden)
    ('c9d0e1f2-0009-0009-0009-000000000009',
     '2026-02-16 09:10:30+00', 'ms-calificaciones', 'editar_calificacion',
     'PUT', 403, 55, 'usr-0003-uuid-student',
     'Usuario no tiene permiso para editar calificaciones.',
     NOW(), NOW()),

    -- 11. Eliminación lógica — ms-usuarios (DELETE → 200)
    ('d0e1f2a3-0010-0010-0010-000000000010',
     '2026-02-16 10:00:00+00', 'ms-usuarios', 'eliminar_usuario',
     'DELETE', 200, 178, 'usr-0001-uuid-admin',
     'Usuario desactivado lógicamente (soft delete).',
     NOW(), NOW()),

    -- 12. Recurso no encontrado — ms-espacios (404 Not Found)
    ('e1f2a3b4-0011-0011-0011-000000000011',
     '2026-02-16 11:30:00+00', 'ms-espacios', 'obtener_espacio',
     'GET', 404, 45, 'usr-0002-uuid-docente',
     'Espacio con ID ESP-9999 no encontrado.',
     NOW(), NOW());


-- ------------------------------------------------------------
-- aud_estadisticas_servicio
-- Cubre los tres periodos (diario, semanal, mensual)
-- y varios microservicios con distintos volúmenes de tráfico.
-- ------------------------------------------------------------
INSERT INTO aud_estadisticas_servicio
    (microservicio, periodo, fecha,
     total_peticiones, total_errores, tiempo_promedio_ms,
     funcionalidad_top, fecha_calculo, created_at, updated_at)
VALUES
    -- Estadísticas diarias (2026-02-15)
    ('ms-autenticacion', 'diario', '2026-02-15',
     4820,  312, 98.50,  'login',                '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-reservas',      'diario', '2026-02-15',
     1345,  87,  285.30, 'crear_reserva',         '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-matriculas',    'diario', '2026-02-15',
     980,   45,  195.10, 'consultar_matriculas',  '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-facturacion',   'diario', '2026-02-15',
     620,   58,  540.70, 'generar_factura',       '2026-02-16 00:05:00+00', NOW(), NOW()),

    -- Estadísticas semanales (semana del 2026-02-09)
    ('ms-autenticacion', 'semanal', '2026-02-09',
     31250, 2140, 102.30, 'login',               '2026-02-16 00:10:00+00', NOW(), NOW()),
    ('ms-reservas',      'semanal', '2026-02-09',
     8970,  610,  278.50, 'crear_reserva',        '2026-02-16 00:10:00+00', NOW(), NOW()),

    -- Estadísticas mensuales (febrero 2026)
    ('ms-autenticacion',  'mensual', '2026-02-01',
     125400, 8720, 99.80,  'login',              '2026-02-16 00:15:00+00', NOW(), NOW()),
    ('ms-auditoria',      'mensual', '2026-02-01',
     48200,  320,  112.40, 'consultar_logs',     '2026-02-16 00:15:00+00', NOW(), NOW()),
    ('ms-inventario',     'mensual', '2026-02-01',
     19800,  1240, 225.60, 'consultar_stock',    '2026-02-16 00:15:00+00', NOW(), NOW()),
    ('ms-calificaciones', 'mensual', '2026-02-01',
     15600,  480,  188.90, 'registrar_nota',     '2026-02-16 00:15:00+00', NOW(), NOW());


-- ------------------------------------------------------------
-- microservice_tokens
-- Tokens de ejemplo para desarrollo local.
-- En producción los tokens se gestionan vía secrets manager.
-- Hash: SHA-256 del texto plano del token.
-- ------------------------------------------------------------
INSERT INTO microservice_tokens
    (id, nombre_microservicio, token_hash, activo, created_at, updated_at)
VALUES
    -- Token: "dev-token-ms-reservas"
    (gen_random_uuid(), 'ms-reservas',
     '7b3e2d8f9a4b1c6e5d0f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d',
     true, NOW(), NOW()),
    -- Token: "dev-token-ms-matriculas"
    (gen_random_uuid(), 'ms-matriculas',
     '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
     true, NOW(), NOW()),
    -- Token: "dev-token-ms-autenticacion"
    (gen_random_uuid(), 'ms-autenticacion',
     '9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e',
     true, NOW(), NOW())
ON CONFLICT (nombre_microservicio) DO NOTHING;
