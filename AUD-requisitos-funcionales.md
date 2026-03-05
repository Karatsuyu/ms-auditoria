# ms-auditoria [AUD] — Requisitos Funcionales

**Módulo:** Módulo 6 — Transversales  
**Stack:** FastAPI + Python + PostgreSQL  
**Propósito:** Servicio centralizado de auditoría y trazabilidad del sistema ERP universitario. Recibe registros de log de todos los microservicios de forma asíncrona, los almacena, permite reconstruir trazas completas de peticiones y genera estadísticas de uso del sistema.

---

## Tabla de Contenido

### Categoría 1: Requisitos Transversales

| ID | Nombre |
|---|---|
| AUD-RF-001 | Validación de sesión activa |
| AUD-RF-002 | Validación de permisos por funcionalidad |
| AUD-RF-003 | Generación y propagación de Request ID |
| AUD-RF-004 | Estructura de respuesta estándar |
| AUD-RF-005 | Auto-auditoría de operaciones internas |

### Categoría 2: Requisitos Funcionales por Entidad

#### Entidad: Eventos de Log

| ID | Nombre |
|---|---|
| AUD-RF-006 | Recibir registro de log individual (asíncrono) |
| AUD-RF-007 | Recibir registros de log en lote (batch) |
| AUD-RF-008 | Consultar traza completa por Request ID |
| AUD-RF-009 | Filtrar registros de log por criterios |

#### Entidad: Configuración de Retención

| ID | Nombre |
|---|---|
| AUD-RF-010 | Consultar configuración de retención |
| AUD-RF-011 | Actualizar configuración de retención |
| AUD-RF-012 | Ejecutar rotación manual de registros |
| AUD-RF-013 | Rotación automática programada de registros |

#### Entidad: Estadísticas por Servicio

| ID | Nombre |
|---|---|
| AUD-RF-014 | Calcular y almacenar estadísticas de uso |
| AUD-RF-015 | Consultar estadísticas generales del sistema |
| AUD-RF-016 | Consultar estadísticas detalladas de un servicio |

### Categoría 3: Requisitos Sugeridos

| ID | Nombre |
|---|---|
| AUD-RF-017 | Consultar estado de salud del servicio (health check) |
| AUD-RF-018 | Validar formato de log entrante |
| AUD-RF-019 | Consultar historial de rotaciones ejecutadas |

---

## Categoría 1: Requisitos Transversales

---

| | | |
|---|---|---|
| **Código** | AUD-RF-001 | |
| **Nombre** | Validación de sesión activa | |
| **Descripción** | Verifica que el usuario que realiza la petición tenga una sesión activa y válida antes de ejecutar cualquier lógica de negocio. Aplica a todas las operaciones iniciadas por un usuario humano. | |
| **Actores** | Usuario autenticado, ms-autenticacion | |
| | | |
| **Precondición** | La petición contiene un token de sesión en los headers de autorización. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Extraer el token de sesión del header de autorización de la petición entrante. |
| | 2 | Invocar **ms-autenticacion** (endpoint de validación de sesión) enviando el token. Se espera como respuesta: estado de validez de la sesión e identificador del usuario. |
| | 3 | Si la sesión es válida, retornar el identificador de usuario al flujo invocante para continuar con la operación. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si el token no está presente: rechazar la petición con código 401 y mensaje "Sesión no proporcionada". |
| | E2 | Si ms-autenticacion indica que la sesión no es válida o está expirada: rechazar la petición con código 401 y mensaje "Sesión inválida o expirada". |
| | E3 | Si ms-autenticacion no responde (timeout o error): rechazar la petición con código 503 y mensaje "Servicio de autenticación no disponible". |
| | | |
| **Postcondición** | El identificador del usuario queda disponible para los pasos subsiguientes del flujo. | |
| | | |
| **Comentarios** | Este requisito es referenciado en la secuencia normal de todos los demás requisitos funcionales que requieren autenticación de usuario. No aplica a las recepciones de log enviadas por microservicios mediante token de aplicación. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-002 | |
| **Nombre** | Validación de permisos por funcionalidad | |
| **Descripción** | Verifica que el rol del usuario autenticado tiene autorización para ejecutar la funcionalidad solicitada. Se ejecuta inmediatamente después de validar la sesión. | |
| **Actores** | Usuario autenticado, ms-roles | |
| | | |
| **Precondición** | AUD-RF-001 se ejecutó correctamente y el identificador del usuario está disponible. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Invocar **ms-roles** (endpoint de verificación de permisos) enviando el identificador del usuario y el código de la funcionalidad solicitada. Se espera como respuesta: autorizado/no autorizado. |
| | 2 | Si el permiso es concedido, permitir la continuación del flujo. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si ms-roles indica que el usuario no tiene permiso: rechazar la petición con código 403 y mensaje "Permiso denegado para esta operación". |
| | E2 | Si ms-roles no responde (timeout o error): rechazar la petición con código 503 y mensaje "Servicio de roles no disponible". |
| | | |
| **Postcondición** | El flujo continúa hacia la lógica de negocio de la funcionalidad solicitada. | |
| | | |
| **Comentarios** | Este requisito es referenciado en la secuencia normal de todos los requisitos que implican acceso de usuario a consultas, configuración y ejecución de rotación manual. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-003 | |
| **Nombre** | Generación y propagación de Request ID | |
| **Descripción** | Asigna o reutiliza un identificador único de rastreo para cada petición entrante, garantizando la trazabilidad distribuida. El identificador se propaga en cabeceras y cuerpo de respuesta. | |
| **Actores** | Sistema (automático) | |
| | | |
| **Precondición** | Una petición HTTP ha ingresado al microservicio. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Inspeccionar los headers de la petición en busca de un Request ID existente (campo `X-Request-ID` o equivalente). |
| | 2 | Si existe un Request ID en los headers, reutilizarlo para toda la operación. |
| | 3 | Si no existe, generar un nuevo Request ID con el formato `AUD-{timestamp Unix}-{id corto aleatorio}`. |
| | 4 | Adjuntar el Request ID al contexto de la petición para que esté disponible en todos los pasos subsiguientes del flujo. |
| | 5 | Incluir el Request ID en el header de respuesta y en el cuerpo de la respuesta estándar (ver AUD-RF-004). |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si el Request ID recibido tiene un formato inválido: generar uno nuevo y registrar una advertencia en el log interno. |
| | | |
| **Postcondición** | Toda respuesta emitida por el servicio incluye el Request ID en header y cuerpo. | |
| | | |
| **Comentarios** | Este requisito se ejecuta automáticamente al inicio de cada petición, antes de AUD-RF-001. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-004 | |
| **Nombre** | Estructura de respuesta estándar | |
| **Descripción** | Define el formato uniforme que deben tener todas las respuestas emitidas por el microservicio, tanto en casos de éxito como de error. | |
| **Actores** | Sistema (automático) | |
| | | |
| **Precondición** | Una operación ha finalizado (con éxito o con error) y se va a emitir respuesta al solicitante. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Construir el objeto de respuesta con los siguientes campos obligatorios: `request_id` (Request ID de la petición), `success` (booleano indicador de éxito/error), `data` (datos resultantes de la operación, o `null` en caso de error), `message` (mensaje descriptivo del resultado), `timestamp` (fecha y hora de la respuesta en formato ISO 8601). |
| | 2 | Establecer el código HTTP correspondiente al resultado de la operación. |
| | 3 | Emitir la respuesta al solicitante. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | En ningún caso deben incluirse credenciales en texto plano en el campo `data` ni en `message`. |
| | | |
| **Postcondición** | El solicitante recibe una respuesta con estructura uniforme y predecible. | |
| | | |
| **Comentarios** | Aplica sin excepción a todas las respuestas del servicio, incluyendo errores de validación y errores técnicos. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-005 | |
| **Nombre** | Auto-auditoría de operaciones internas | |
| **Descripción** | Cada operación ejecutada dentro de ms-auditoria genera un registro de log que se almacena en su propia base de datos, garantizando que el servicio se audita a sí mismo. | |
| **Actores** | Sistema (automático) | |
| | | |
| **Precondición** | Una operación interna del servicio ha finalizado (con éxito o con error). | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Al finalizar cualquier operación, construir el registro de log con los campos del formato estándar: fecha/hora, Request ID, nombre del microservicio (`ms-auditoria`), funcionalidad ejecutada, método HTTP, código de respuesta, duración en ms, ID de usuario (o identificador del servicio si es llamada interna), y detalle descriptivo. |
| | 2 | Almacenar el registro directamente en la tabla de eventos de log de la base de datos propia. El procesamiento es en segundo plano para no bloquear la respuesta. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si falla el almacenamiento del log de auto-auditoría, registrar el error en el log de sistema (stderr/logger) pero no afectar el flujo principal ni la respuesta al solicitante. |
| | | |
| **Postcondición** | Existe un registro de log en la base de datos correspondiente a la operación ejecutada. | |
| | | |
| **Comentarios** | Este mecanismo garantiza la trazabilidad completa incluyendo las operaciones propias del servicio de auditoría. No debe generar bucles infinitos: el almacenamiento del log de auto-auditoría no genera otro log. | |

---

## Categoría 2: Requisitos Funcionales por Entidad

### Entidad: Eventos de Log

---

| | | |
|---|---|---|
| **Código** | AUD-RF-006 | |
| **Nombre** | Recibir registro de log individual (asíncrono) | |
| **Descripción** | Permite que cualquier microservicio del sistema envíe un único registro de log en formato JSON. El servicio confirma la recepción de forma inmediata y procesa el almacenamiento en segundo plano. | |
| **Actores** | Microservicio emisor (cualquiera de los 18 consumidores) | |
| | | |
| **Precondición** | El microservicio emisor posee un token de aplicación válido para identificarse ante ms-auditoria. | |
| | El registro de log cumple el formato JSON estándar definido en la regla 6.6. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003] para asignar o reutilizar el Request ID de la petición entrante. |
| | 2 | Validar el token de aplicación del microservicio emisor. |
| | 3 | Validar que el cuerpo de la petición contiene un objeto JSON con todos los campos requeridos: `timestamp`, `request_id`, `service_name`, `functionality`, `method`, `response_code`, `duration_ms`, `user_id`, `detail`. |
| | 4 | Responder inmediatamente al emisor con código 202 (Accepted) y estructura estándar [AUD-RF-004] indicando que el registro fue recibido y será procesado. |
| | 5 | En segundo plano (tarea asíncrona): persistir el registro en la tabla de eventos de log de la base de datos. |
| | 6 | Ejecutar [AUD-RF-005] para registrar la auto-auditoría de esta operación. |
| | | |
| **Secuencia alterna** | 5A | Si el almacenamiento en segundo plano falla: registrar el error en el log de sistema. No se notifica al emisor (ya recibió el 202). |
| | | |
| **Excepciones** | E1 | Si el token de aplicación es inválido o no está presente: rechazar con código 401. |
| | E2 | Si el cuerpo JSON está malformado o faltan campos requeridos: rechazar con código 422 y detalle de los campos faltantes. |
| | E3 | En ningún caso un fallo en ms-auditoria debe bloquear o demorar la respuesta al microservicio emisor. |
| | | |
| **Postcondición** | El registro de log queda almacenado en la base de datos (de forma eventual). | |
| | El microservicio emisor recibió confirmación inmediata independientemente del resultado del almacenamiento. | |
| | | |
| **Comentarios** | La comunicación entre microservicios usa tokens de aplicación (regla 3), no sesión de usuario. Por tanto, AUD-RF-001 y AUD-RF-002 no aplican a este endpoint. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-007 | |
| **Nombre** | Recibir registros de log en lote (batch) | |
| **Descripción** | Permite que cualquier microservicio envíe múltiples registros de log en una sola petición HTTP para optimizar el rendimiento de la comunicación. | |
| **Actores** | Microservicio emisor (cualquiera de los 18 consumidores) | |
| | | |
| **Precondición** | El microservicio emisor posee un token de aplicación válido. | |
| | La petición contiene un arreglo JSON con uno o más registros de log. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003] para asignar o reutilizar el Request ID. |
| | 2 | Validar el token de aplicación del microservicio emisor. |
| | 3 | Validar que el cuerpo es un arreglo JSON no vacío. |
| | 4 | Validar individualmente que cada registro del arreglo contiene todos los campos requeridos del formato estándar. |
| | 5 | Responder inmediatamente al emisor con código 202 (Accepted), indicando la cantidad de registros recibidos [AUD-RF-004]. |
| | 6 | En segundo plano: persistir todos los registros válidos del lote en la tabla de eventos de log mediante inserción masiva. |
| | 7 | Ejecutar [AUD-RF-005] para la auto-auditoría de esta operación. |
| | | |
| **Secuencia alterna** | 4A | Si algún registro individual del lote tiene campos inválidos o faltantes: marcarlo como rechazado. Los registros válidos del mismo lote se procesan con normalidad. |
| | 6A | Si falla el almacenamiento masivo: intentar reintento o registrar el error en el log de sistema. No se notifica al emisor. |
| | | |
| **Excepciones** | E1 | Si el token de aplicación es inválido: rechazar con código 401. |
| | E2 | Si el arreglo está vacío o el cuerpo no es un arreglo JSON válido: rechazar con código 422. |
| | E3 | Si todos los registros del lote son inválidos: responder 202 con indicación de que ningún registro fue aceptado. |
| | | |
| **Postcondición** | Los registros válidos del lote quedan almacenados en la base de datos de forma eventual. | |
| | El emisor recibió confirmación inmediata. | |
| | | |
| **Comentarios** | El tamaño máximo del lote aceptado por petición es [Por definir]. Se recomienda definir un límite para prevenir payloads excesivos. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-008 | |
| **Nombre** | Consultar traza completa por Request ID | |
| **Descripción** | Permite buscar todos los registros de log asociados a un identificador de rastreo específico, retornando la traza completa de una petición a través de todos los microservicios que participaron en su procesamiento. | |
| **Actores** | Usuario autenticado con permiso de consulta de auditoría | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos para consultar registros de auditoría. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001] para validar sesión. |
| | 3 | Ejecutar [AUD-RF-002] para validar permisos sobre esta funcionalidad. |
| | 4 | Recibir el parámetro `request_id` de la petición. |
| | 5 | Consultar en la base de datos todos los registros cuyo campo `request_id` coincida con el valor recibido. |
| | 6 | Ordenar los resultados por `timestamp` ascendente para reconstruir la secuencia cronológica de la traza. |
| | 7 | Aplicar paginación obligatoria sobre los resultados (parámetros `page` y `page_size` requeridos). |
| | 8 | Retornar los resultados paginados con estructura [AUD-RF-004]. |
| | 9 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 5A | Si no se encuentran registros para el `request_id` indicado: retornar lista vacía con código 200 y mensaje informativo. |
| | | |
| **Excepciones** | E1 | Si el parámetro `request_id` no es proporcionado: rechazar con código 400. |
| | E2 | Si los parámetros de paginación (`page`, `page_size`) no son proporcionados o son inválidos: rechazar con código 400. |
| | | |
| **Postcondición** | El usuario recibe la lista paginada de eventos de log asociados al Request ID consultado. | |
| | | |
| **Comentarios** | La paginación es obligatoria por regla de negocio (regla 9). Una traza puede involucrar docenas de registros si la petición original recorrió múltiples servicios. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-009 | |
| **Nombre** | Filtrar registros de log por criterios | |
| **Descripción** | Permite consultar registros de log aplicando filtros por microservicio de origen, por rango de fechas, o por combinación de ambos criterios. Todos los resultados son paginados. | |
| **Actores** | Usuario autenticado con permiso de consulta de auditoría | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos para consultar registros de auditoría. | |
| | Al menos un criterio de filtro debe ser proporcionado. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Recibir y validar los parámetros de filtro: `service_name` (opcional), `date_from` (opcional), `date_to` (opcional), `page`, `page_size` (obligatorios). |
| | 5 | Construir la consulta a la base de datos aplicando los filtros recibidos. Si se proporcionan `date_from` y `date_to`, filtrar registros cuyo `timestamp` esté dentro del rango. Si se proporciona `service_name`, filtrar por ese microservicio. |
| | 6 | Aplicar paginación obligatoria sobre los resultados. |
| | 7 | Retornar los resultados con estructura [AUD-RF-004]. |
| | 8 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 5A | Si no se encuentran registros que cumplan los criterios: retornar lista vacía con código 200. |
| | | |
| **Excepciones** | E1 | Si no se proporciona ningún criterio de filtro (todos opcionales están ausentes): rechazar con código 400 solicitando al menos un criterio. |
| | E2 | Si `date_from` es posterior a `date_to`: rechazar con código 400. |
| | E3 | Si los parámetros de paginación son inválidos o ausentes: rechazar con código 400. |
| | | |
| **Postcondición** | El usuario recibe la lista paginada de registros de log que cumplen los criterios de filtro. | |
| | | |
| **Comentarios** | La combinación de `service_name` + rango de fechas es el caso de uso más esperado para diagnóstico operacional. Los filtros son aditivos (AND). | |

---

### Entidad: Configuración de Retención

---

| | | |
|---|---|---|
| **Código** | AUD-RF-010 | |
| **Nombre** | Consultar configuración de retención | |
| **Descripción** | Permite a un usuario autorizado consultar la configuración actual de retención de datos: días configurados, estado, fecha de última rotación y cantidad de registros eliminados en la última ejecución. | |
| **Actores** | Usuario administrador autenticado | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos de administración del servicio de auditoría. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Consultar en la base de datos el registro de configuración de retención activo. |
| | 5 | Retornar los datos con estructura [AUD-RF-004]: `retention_days`, `status`, `last_rotation_date`, `last_rotation_deleted_count`. |
| | 6 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 4A | Si no existe configuración registrada (primer uso): retornar la configuración por defecto (30 días) sin persistir. |
| | | |
| **Excepciones** | E1 | Error de acceso a base de datos: responder con código 500. |
| | | |
| **Postcondición** | El usuario recibe la configuración de retención vigente. | |
| | | |
| **Comentarios** | El valor por defecto de `retention_days` es 30, según las reglas de negocio. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-011 | |
| **Nombre** | Actualizar configuración de retención | |
| **Descripción** | Permite a un usuario administrador modificar la cantidad de días de retención de registros de log. | |
| **Actores** | Usuario administrador autenticado | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos de administración del servicio de auditoría. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Recibir y validar el parámetro `retention_days`: debe ser un entero positivo mayor a cero. |
| | 5 | Actualizar el registro de configuración en la base de datos con el nuevo valor y marcar el estado como activo. |
| | 6 | Retornar la configuración actualizada con estructura [AUD-RF-004]. |
| | 7 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si `retention_days` es cero, negativo o no es un entero: rechazar con código 422. |
| | E2 | Error de escritura en base de datos: responder con código 500. |
| | | |
| **Postcondición** | La configuración de retención queda actualizada en la base de datos. | |
| | Las siguientes rotaciones automáticas usarán el nuevo valor configurado. | |
| | | |
| **Comentarios** | [Por definir] si se debe validar un rango mínimo/máximo de días permitidos (ej: mínimo 7, máximo 365). | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-012 | |
| **Nombre** | Ejecutar rotación manual de registros | |
| **Descripción** | Permite a un usuario administrador disparar de forma manual la eliminación de registros de log cuya antigüedad supera los días de retención configurados. | |
| **Actores** | Usuario administrador autenticado | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos de administración del servicio de auditoría. | |
| | Existe una configuración de retención activa. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Consultar la configuración de retención vigente para obtener el valor de `retention_days`. |
| | 5 | Calcular la fecha de corte: `fecha_actual - retention_days`. |
| | 6 | Eliminar de la base de datos todos los registros de la tabla de eventos de log cuyo `timestamp` sea anterior a la fecha de corte. |
| | 7 | Contar la cantidad de registros eliminados. |
| | 8 | Actualizar el registro de configuración de retención con: `last_rotation_date = fecha_actual`, `last_rotation_deleted_count = cantidad eliminada`. |
| | 9 | Retornar el resultado con estructura [AUD-RF-004]: fecha de ejecución y cantidad de registros eliminados. |
| | 10 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 6A | Si no existen registros anteriores a la fecha de corte: retornar código 200 indicando que no hubo registros para eliminar. |
| | | |
| **Excepciones** | E1 | Error durante la eliminación en base de datos: responder con código 500 y no actualizar la fecha de última rotación. |
| | | |
| **Postcondición** | Los registros con antigüedad superior a los días configurados han sido eliminados de la base de datos. | |
| | La configuración de retención refleja la fecha y cantidad de registros de la última rotación ejecutada. | |
| | | |
| **Comentarios** | Esta operación puede ser costosa en tiempo si el volumen de registros es alto. Se recomienda evaluar ejecución asíncrona para lotes grandes [Por definir]. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-013 | |
| **Nombre** | Rotación automática programada de registros | |
| **Descripción** | El sistema ejecuta automáticamente la rotación de registros según un calendario programado, eliminando los registros cuya antigüedad supera los días de retención configurados, sin intervención de un usuario. | |
| **Actores** | Sistema (scheduler/cron interno) | |
| | | |
| **Precondición** | Existe una configuración de retención activa con `retention_days` definido. | |
| | El scheduler del sistema está operativo. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | El scheduler interno dispara la tarea de rotación según la frecuencia configurada (por defecto: diaria). |
| | 2 | Consultar la configuración de retención vigente. |
| | 3 | Calcular la fecha de corte: `fecha_actual - retention_days`. |
| | 4 | Eliminar de la base de datos todos los registros de eventos de log cuyo `timestamp` sea anterior a la fecha de corte. |
| | 5 | Contar la cantidad de registros eliminados. |
| | 6 | Actualizar el registro de configuración con `last_rotation_date` y `last_rotation_deleted_count`. |
| | 7 | Ejecutar [AUD-RF-005] para registrar la ejecución de la rotación automática. |
| | | |
| **Secuencia alterna** | 4A | Si no hay registros a eliminar: actualizar la fecha de última rotación con cantidad = 0 y finalizar normalmente. |
| | | |
| **Excepciones** | E1 | Si falla la rotación automática: registrar el error en el log de sistema. No afectar la disponibilidad del servicio. |
| | | |
| **Postcondición** | Los registros con antigüedad superior a los días configurados han sido eliminados. | |
| | La configuración de retención refleja la última ejecución automática. | |
| | | |
| **Comentarios** | La frecuencia de ejecución del scheduler es [Por definir] (se recomienda diaria en horario de baja carga). No aplican AUD-RF-001 ni AUD-RF-002 al ser una operación interna del sistema. | |

---

### Entidad: Estadísticas por Servicio

---

| | | |
|---|---|---|
| **Código** | AUD-RF-014 | |
| **Nombre** | Calcular y almacenar estadísticas de uso | |
| **Descripción** | El sistema calcula y persiste métricas de uso por microservicio y periodo (diario, semanal, mensual): total de peticiones, total de errores, tiempo promedio de respuesta y funcionalidad más utilizada. | |
| **Actores** | Sistema (scheduler/proceso interno) | |
| | | |
| **Precondición** | Existen registros de eventos de log almacenados en la base de datos para el periodo a calcular. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | El proceso interno se dispara según la frecuencia configurada (o bajo demanda desde otro requisito). |
| | 2 | Para cada microservicio con registros en el periodo a calcular, agrupar los eventos de log por `service_name` y `period`. |
| | 3 | Calcular: `total_requests` (conteo total), `total_errors` (conteo de registros con `response_code` >= 400), `avg_response_time_ms` (promedio de `duration_ms`), `most_used_functionality` (funcionalidad con mayor frecuencia de aparición). |
| | 4 | Persistir o actualizar el registro de estadísticas en la tabla correspondiente con los campos calculados y la `calculation_date` actual. |
| | 5 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 2A | Si un microservicio no tiene registros en el periodo: omitirlo sin generar error. |
| | | |
| **Excepciones** | E1 | Si falla el cálculo o la persistencia: registrar el error en el log de sistema sin afectar la disponibilidad del servicio. |
| | | |
| **Postcondición** | Las estadísticas calculadas quedan persistidas en la base de datos para el periodo procesado. | |
| | | |
| **Comentarios** | La frecuencia de cálculo automático y la lógica de actualización vs. inserción de registros existentes son [Por definir]. Los errores se identifican por `response_code >= 400`. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-015 | |
| **Nombre** | Consultar estadísticas generales del sistema | |
| **Descripción** | Permite a un usuario autorizado consultar las estadísticas de uso agregadas de todos los microservicios del sistema para un periodo determinado. | |
| **Actores** | Usuario autenticado con permiso de consulta de estadísticas | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos para consultar estadísticas. | |
| | Existen estadísticas calculadas y almacenadas en la base de datos. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Recibir y validar los parámetros de consulta: `period` (diario/semanal/mensual, obligatorio), `date` (opcional, por defecto el periodo más reciente), `page`, `page_size` (obligatorios). |
| | 5 | Consultar en la base de datos todos los registros de estadísticas que coincidan con el periodo indicado. |
| | 6 | Aplicar paginación obligatoria. |
| | 7 | Retornar los resultados con estructura [AUD-RF-004]. |
| | 8 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 5A | Si no existen estadísticas para el periodo indicado: retornar lista vacía con código 200 y mensaje informativo. |
| | | |
| **Excepciones** | E1 | Si `period` tiene un valor distinto a `daily`, `weekly` o `monthly`: rechazar con código 422. |
| | E2 | Si los parámetros de paginación son inválidos o ausentes: rechazar con código 400. |
| | | |
| **Postcondición** | El usuario recibe las estadísticas generales paginadas del periodo solicitado. | |
| | | |
| **Comentarios** | Esta vista general es útil para monitoreo de salud del sistema completo por parte de administradores. | |

---

| | | |
|---|---|---|
| **Código** | AUD-RF-016 | |
| **Nombre** | Consultar estadísticas detalladas de un servicio | |
| **Descripción** | Permite a un usuario autorizado consultar las estadísticas de uso de un microservicio específico, con detalle de métricas por periodo. | |
| **Actores** | Usuario autenticado con permiso de consulta de estadísticas | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos para consultar estadísticas. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Recibir y validar los parámetros: `service_name` (obligatorio), `period` (obligatorio: diario/semanal/mensual), `date` (opcional), `page`, `page_size` (obligatorios). |
| | 5 | Consultar en la base de datos los registros de estadísticas que coincidan con `service_name` y `period`. |
| | 6 | Aplicar paginación obligatoria. |
| | 7 | Retornar los resultados con estructura [AUD-RF-004], incluyendo todos los campos: `service_name`, `period`, `date`, `total_requests`, `total_errors`, `avg_response_time_ms`, `most_used_functionality`, `calculation_date`. |
| | 8 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 5A | Si no existen estadísticas para el servicio y periodo indicados: retornar lista vacía con código 200 y mensaje informativo. |
| | | |
| **Excepciones** | E1 | Si `service_name` está vacío o no es proporcionado: rechazar con código 400. |
| | E2 | Si `period` tiene un valor inválido: rechazar con código 422. |
| | E3 | Si los parámetros de paginación son inválidos o ausentes: rechazar con código 400. |
| | | |
| **Postcondición** | El usuario recibe las estadísticas del microservicio solicitado para el periodo indicado. | |
| | | |
| **Comentarios** | Permite identificar servicios con alta tasa de error o degradación de tiempo de respuesta en el tiempo. | |

---

## Categoría 3: Requisitos Sugeridos

---

> **Justificación AUD-RF-017:** ms-auditoria es un servicio de infraestructura crítica consumido por todos los microservicios del sistema. Un endpoint de health check es indispensable para que los orquestadores de contenedores (Kubernetes, Docker Compose), los API gateways y los pipelines de CI/CD puedan verificar la disponibilidad del servicio sin requerir autenticación, siguiendo la práctica estándar de microservicios. Su ausencia impide la supervisión automatizada del servicio más transversal del sistema.

| | | |
|---|---|---|
| **Código** | AUD-RF-017 | |
| **Nombre** | Consultar estado de salud del servicio (health check) | |
| **Descripción** | Provee un endpoint público sin autenticación que retorna el estado operativo del servicio y de su conexión con la base de datos, para uso de orquestadores, monitores y pipelines de despliegue. | |
| **Actores** | Sistema orquestador, herramienta de monitoreo, pipeline CI/CD | |
| | | |
| **Precondición** | El servicio está en ejecución. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Recibir la petición GET al endpoint `/health` (sin requerir autenticación ni token). |
| | 2 | Verificar la conectividad con la base de datos PostgreSQL realizando una consulta mínima (ej: `SELECT 1`). |
| | 3 | Retornar código 200 con un objeto JSON indicando: `status: "healthy"`, estado de la conexión a base de datos, versión del servicio y timestamp. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si la base de datos no responde: retornar código 503 con `status: "unhealthy"` y detalle del componente fallido. |
| | | |
| **Postcondición** | El solicitante conoce el estado operativo actual del servicio. | |
| | | |
| **Comentarios** | Este endpoint no debe generar registros de auto-auditoría (AUD-RF-005) para evitar ruido en los logs por los sondeos frecuentes de los orquestadores. | |

---

> **Justificación AUD-RF-018:** La regla de negocio 13 establece un formato de log estandarizado, pero AUD-RF-006 y AUD-RF-007 solo mencionan validación de campos presentes. Es necesario un requisito explícito que defina la validación de tipos de dato, formatos y rangos válidos para cada campo del log (ej: `response_code` debe ser un entero HTTP válido, `duration_ms` debe ser no negativo, `timestamp` debe ser una fecha ISO 8601 válida). Sin este requisito, datos malformados pero estructuralmente presentes pueden comprometer la integridad de las estadísticas calculadas en AUD-RF-014.

| | | |
|---|---|---|
| **Código** | AUD-RF-018 | |
| **Nombre** | Validar formato y tipos de datos de registro de log entrante | |
| **Descripción** | Define las reglas de validación detalladas de tipo, formato y rango que debe cumplir cada campo de un registro de log antes de ser aceptado para almacenamiento, complementando la validación de presencia de campos. | |
| **Actores** | Sistema (componente de validación interno, invocado desde AUD-RF-006 y AUD-RF-007) | |
| | | |
| **Precondición** | Un registro de log en formato JSON ha sido recibido y se ha confirmado que contiene todos los campos requeridos. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Validar que `timestamp` es una fecha/hora válida en formato ISO 8601. |
| | 2 | Validar que `request_id` es una cadena no vacía. |
| | 3 | Validar que `service_name` corresponde a un nombre de microservicio conocido del sistema, o es una cadena no vacía si se admiten servicios no registrados [Por definir]. |
| | 4 | Validar que `functionality` es una cadena no vacía. |
| | 5 | Validar que `method` es uno de los métodos HTTP válidos: GET, POST, PUT, PATCH, DELETE. |
| | 6 | Validar que `response_code` es un entero en el rango 100–599. |
| | 7 | Validar que `duration_ms` es un entero no negativo. |
| | 8 | Validar que `user_id` es una cadena no vacía o un identificador válido [Por definir si puede ser nulo para operaciones de sistema]. |
| | 9 | Validar que `detail` es una cadena (puede estar vacía pero no ser nula). |
| | 10 | Si todas las validaciones pasan, retornar el registro como válido. |
| | | |
| **Secuencia alterna** | — | No aplica. |
| | | |
| **Excepciones** | E1 | Si alguna validación falla: retornar el registro como inválido con indicación del campo y la regla violada. |
| | | |
| **Postcondición** | El registro queda clasificado como válido o inválido con detalle de los errores encontrados. | |
| | | |
| **Comentarios** | Este requisito es invocado internamente por AUD-RF-006 (paso 3) y AUD-RF-007 (paso 4). No tiene endpoint propio. La validación de `user_id` como nulo/vacío para operaciones de sistema es [Por definir]. | |

---

> **Justificación AUD-RF-019:** AUD-RF-010 solo expone el estado de la última rotación ejecutada. Sin embargo, para fines de auditoría y diagnóstico, los administradores necesitan acceder al historial de todas las rotaciones realizadas (automáticas y manuales), incluyendo fechas y cantidades eliminadas. Este requisito es deducible del hecho de que ms-auditoria se auto-audita (AUD-RF-005 registra cada ejecución de rotación) y de que el sistema gestiona retención de datos como una entidad explícita, lo que implica que el historial de cambios en esa entidad es información valiosa.

| | | |
|---|---|---|
| **Código** | AUD-RF-019 | |
| **Nombre** | Consultar historial de rotaciones ejecutadas | |
| **Descripción** | Permite a un usuario administrador consultar el historial de todas las rotaciones de registros ejecutadas (automáticas y manuales), con fecha de ejecución, tipo de disparador y cantidad de registros eliminados en cada una. | |
| **Actores** | Usuario administrador autenticado | |
| | | |
| **Precondición** | El usuario ha iniciado sesión y tiene permisos de administración del servicio de auditoría. | |
| | | |
| | **Paso** | **Descripción** |
| **Secuencia normal** | 1 | Ejecutar [AUD-RF-003]. |
| | 2 | Ejecutar [AUD-RF-001]. |
| | 3 | Ejecutar [AUD-RF-002]. |
| | 4 | Recibir los parámetros de paginación obligatorios (`page`, `page_size`) y opcionalmente un rango de fechas para filtrar el historial. |
| | 5 | Consultar los registros de auto-auditoría (eventos de log propios de ms-auditoria) filtrando por `functionality` igual a la operación de rotación. |
| | 6 | Ordenar los resultados por `timestamp` descendente. |
| | 7 | Aplicar paginación y retornar resultados con estructura [AUD-RF-004]. |
| | 8 | Ejecutar [AUD-RF-005]. |
| | | |
| **Secuencia alterna** | 5A | Si no existe historial de rotaciones: retornar lista vacía con código 200. |
| | | |
| **Excepciones** | E1 | Si los parámetros de paginación son inválidos o ausentes: rechazar con código 400. |
| | | |
| **Postcondición** | El usuario recibe el historial paginado de rotaciones ejecutadas. | |
| | | |
| **Comentarios** | Este historial se reconstruye a partir de los registros de auto-auditoría generados por AUD-RF-005 durante las ejecuciones de AUD-RF-012 y AUD-RF-013. Puede requerir una tabla dedicada de historial de rotaciones si la granularidad de los campos de auto-auditoría no es suficiente [Por definir]. | |

---

*Documento generado a partir de: ms-auditoria.md — ERP Universitario v1.0, Febrero 2026.*  
*Fecha de generación: Marzo 2026.*
