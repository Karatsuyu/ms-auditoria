-- ============================================================
-- DATOS SEMILLA CORREGIDOS — ms-auditoria [AUD]
-- Base de datos: db_auditoria / ms_auditoria
-- CORRECCIONES APLICADAS:
--   1. Removido 'id' del INSERT (es SERIAL/autoincrement)
--   2. Token hashes son el SHA-256 real de cada token string
--   3. Tokens para los 18 microservicios del ERP
-- ============================================================

-- ------------------------------------------------------------
-- aud_configuracion_retencion
-- ------------------------------------------------------------
INSERT INTO aud_configuracion_retencion
    (dias_retencion, estado, ultima_rotacion, registros_eliminados_ultima, created_at, updated_at)
VALUES
    (30,  'activo',   '2026-02-01 03:00:00+00', 15842, NOW(), NOW()),
    (60,  'inactivo', '2026-01-01 03:00:00+00', 8210,  NOW(), NOW()),
    (7,   'inactivo', NULL,                      0,     NOW(), NOW()),
    (365, 'inactivo', NULL,                      0,     NOW(), NOW());


-- ------------------------------------------------------------
-- aud_eventos_log — Datos de prueba
-- ------------------------------------------------------------
INSERT INTO aud_eventos_log
    (request_id, fecha_hora, microservicio, funcionalidad,
     metodo, codigo_respuesta, duracion_ms, usuario_id, detalle,
     created_at, updated_at)
VALUES
    ('a1b2c3d4-0001-0001-0001-000000000001',
     '2026-02-15 08:05:12+00', 'ms-autenticacion', 'login',
     'POST', 200, 145, 'usr-0001-uuid-admin',
     'Inicio de sesión exitoso para usuario administrador.',
     NOW(), NOW()),

    ('a1b2c3d4-0001-0001-0001-000000000001',
     '2026-02-15 08:05:12+00', 'ms-roles', 'verificar_permisos',
     'GET', 200, 32, 'usr-0001-uuid-admin',
     'Permisos verificados para rol ADMIN.',
     NOW(), NOW()),

    ('b2c3d4e5-0002-0002-0002-000000000002',
     '2026-02-15 09:30:45+00', 'ms-reservas', 'crear_reserva',
     'POST', 201, 312, 'usr-0002-uuid-docente',
     'Reserva creada para espacio A-101, fecha 2026-02-20.',
     NOW(), NOW()),

    ('c3d4e5f6-0003-0003-0003-000000000003',
     '2026-02-15 10:15:00+00', 'ms-inventario', 'registrar_salida',
     'POST', 400, 78, 'usr-0001-uuid-admin',
     'Stock insuficiente para el item solicitado.',
     NOW(), NOW()),

    ('d4e5f6a7-0004-0004-0004-000000000004',
     '2026-02-15 11:00:00+00', 'ms-facturacion', 'generar_factura',
     'POST', 500, 2340, 'usr-0003-uuid-student',
     'Error al conectar con el proveedor de firma electronica.',
     NOW(), NOW()),

    ('e5f6a7b8-0005-0005-0005-000000000005',
     '2026-02-15 03:00:00+00', 'ms-reportes', 'generar_reporte_diario',
     'POST', 200, 8920, NULL,
     'Reporte diario generado automaticamente por scheduler.',
     NOW(), NOW()),

    ('f6a7b8c9-0006-0006-0006-000000000006',
     '2026-02-15 03:05:00+00', 'ms-auditoria', 'ejecutar_rotacion',
     'POST', 200, 4521, NULL,
     'Rotacion automatica ejecutada. 15842 registros eliminados.',
     NOW(), NOW()),

    ('b8c9d0e1-0008-0008-0008-000000000008',
     '2026-02-16 07:45:00+00', 'ms-matriculas', 'actualizar_estado_matricula',
     'PATCH', 200, 210, 'usr-0001-uuid-admin',
     'Matricula MAT-2026-0042 cambiada a estado activa.',
     NOW(), NOW()),

    ('c9d0e1f2-0009-0009-0009-000000000009',
     '2026-02-16 09:10:30+00', 'ms-calificaciones', 'editar_calificacion',
     'PUT', 403, 55, 'usr-0003-uuid-student',
     'Usuario no tiene permiso para editar calificaciones.',
     NOW(), NOW()),

    ('e1f2a3b4-0011-0011-0011-000000000011',
     '2026-02-16 11:30:00+00', 'ms-espacios', 'obtener_espacio',
     'GET', 404, 45, 'usr-0002-uuid-docente',
     'Espacio con ID ESP-9999 no encontrado.',
     NOW(), NOW());


-- ------------------------------------------------------------
-- aud_estadisticas_servicio
-- ------------------------------------------------------------
INSERT INTO aud_estadisticas_servicio
    (microservicio, periodo, fecha,
     total_peticiones, total_errores, tiempo_promedio_ms,
     funcionalidad_top, fecha_calculo, created_at, updated_at)
VALUES
    ('ms-autenticacion', 'diario', '2026-02-15',
     4820,  312, 98.50,  'login',                '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-reservas',      'diario', '2026-02-15',
     1345,  87,  285.30, 'crear_reserva',         '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-matriculas',    'diario', '2026-02-15',
     980,   45,  195.10, 'consultar_matriculas',  '2026-02-16 00:05:00+00', NOW(), NOW()),
    ('ms-autenticacion', 'semanal', '2026-02-09',
     31250, 2140, 102.30, 'login',               '2026-02-16 00:10:00+00', NOW(), NOW()),
    ('ms-autenticacion',  'mensual', '2026-02-01',
     125400, 8720, 99.80,  'login',              '2026-02-16 00:15:00+00', NOW(), NOW()),
    ('ms-auditoria',      'mensual', '2026-02-01',
     48200,  320,  112.40, 'consultar_logs',     '2026-02-16 00:15:00+00', NOW(), NOW());


-- ============================================================
-- microservice_tokens — CORREGIDO
--
-- CAMBIOS RESPECTO AL ORIGINAL:
--   1. Columna 'id' REMOVIDA del INSERT (es SERIAL autoincrement,
--      PostgreSQL la genera solo — insertar gen_random_uuid() en
--      una columna Integer causa error de tipo).
--   2. Los token_hash son el SHA-256 REAL de cada token string.
--      Antes tenían hashes inventados que no coincidían con nada.
--
-- Tokens en texto plano para desarrollo (compartir con cada equipo):
--   ms-autenticacion  → dev-token-ms-autenticacion
--   ms-usuarios       → dev-token-ms-usuarios
--   ms-roles          → dev-token-ms-roles
--   ms-inventario     → dev-token-ms-inventario
--   ms-espacios       → dev-token-ms-espacios
--   ms-reservas       → dev-token-ms-reservas
--   ms-presupuesto    → dev-token-ms-presupuesto
--   ms-gastos         → dev-token-ms-gastos
--   ms-facturacion    → dev-token-ms-facturacion
--   ms-pedidos        → dev-token-ms-pedidos
--   ms-domicilios     → dev-token-ms-domicilios
--   ms-proveedores    → dev-token-ms-proveedores
--   ms-programas      → dev-token-ms-programas
--   ms-matriculas     → dev-token-ms-matriculas
--   ms-calificaciones → dev-token-ms-calificaciones
--   ms-horarios       → dev-token-ms-horarios
--   ms-notificaciones → dev-token-ms-notificaciones
--   ms-reportes       → dev-token-ms-reportes
-- ============================================================
INSERT INTO microservice_tokens
    (nombre_microservicio, token_hash, activo, created_at, updated_at)
VALUES
    ('ms-autenticacion',
     'f3d552ffd64b698f9b4178ee773e3fcf51bb6c86443052125c7afaa4878eaf46',
     true, NOW(), NOW()),

    ('ms-usuarios',
     'b3caf41a4b5460d7dbb4fd2e186a015eeb08a102591bd39d5af82b96d7f68967',
     true, NOW(), NOW()),

    ('ms-roles',
     'ca5de10efd88abb0c985ee68679f6e8fa54751059678adefa49a8332c26210be',
     true, NOW(), NOW()),

    ('ms-inventario',
     '8514ee20785d16130e52f93b3dcada7c9bc57c630a91d5f3153dbdfadbb83225',
     true, NOW(), NOW()),

    ('ms-espacios',
     '56e234d9badbe36a3cacc0980846bd149deb094874639bd915122e6b6fed11c4',
     true, NOW(), NOW()),

    ('ms-reservas',
     '407958831ee977a249a028d4a4cbf70fbebf14934feb97bdafe68d1e4e103b9c',
     true, NOW(), NOW()),

    ('ms-presupuesto',
     '0d08a989bb5e2e775356fbfe28ae401d219142e1687de8f180a630c55ee96c76',
     true, NOW(), NOW()),

    ('ms-gastos',
     'ad54327561e8237ea82a930136d8e87c5e722bd1090de14b668fbfd9e0dfa0b1',
     true, NOW(), NOW()),

    ('ms-facturacion',
     '26a237a91d0a93ee56e9d4547f0bf66c6eb1aa02d1442fe5add9aed5f9597bba',
     true, NOW(), NOW()),

    ('ms-pedidos',
     'fbf30b332256613ccb129c62e3f8861e1e7dd9328cf63353c97f2b096fba95a3',
     true, NOW(), NOW()),

    ('ms-domicilios',
     'a2f2cc258c520c90c00607caecc48d1b999e268efb58e7951fae1860002aa437',
     true, NOW(), NOW()),

    ('ms-proveedores',
     'a1748e9b71c8e3f0e1355916edab000288a84a34b3b57be3ad1155d2f6099855',
     true, NOW(), NOW()),

    ('ms-programas',
     '4777787fb5adbd291e29959ffa73884c6111b3a81069846ab0368ead9d8dac9a',
     true, NOW(), NOW()),

    ('ms-matriculas',
     'ad36242191f369bf615185f9c87fb99ab96e0821372c85de8c59b23efbf9f5aa',
     true, NOW(), NOW()),

    ('ms-calificaciones',
     'e9de5b0754422a80d699afde95c4cf78f88e2f33fd92535dc26130840b6c4c8e',
     true, NOW(), NOW()),

    ('ms-horarios',
     '3eeaf893518cd7d21f9def6dc7b637527fb674268c86c14fd8030dc7520aa787',
     true, NOW(), NOW()),

    ('ms-notificaciones',
     '372248eca9dbc8686c14e590c843cab482e98335a715e3936e920f67691fc64a',
     true, NOW(), NOW()),

    ('ms-reportes',
     '71f13cdc6ccfcee86141a9f2c6841f822227ad4ca278b1feb0b6dd582bcbcf8d',
     true, NOW(), NOW())

ON CONFLICT (nombre_microservicio) DO NOTHING;
