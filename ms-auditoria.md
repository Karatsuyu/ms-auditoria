# ms-auditoria [AUD] — Documento de Requisitos del Microservicio

---

## 1. Extracción Textual

### Fragmento 1 — Sección 5. Arquitectura General (Módulo 6 — Transversales)

> Servicios de soporte consumidos por los demás módulos: notificaciones, auditoría y reportes.
>
> - ms-notificaciones
> - ms-auditoria
> - ms-reportes

---

### Fragmento 2 — Sección 6.6 Reglas Transversales: Auditoría y Logs en Formato JSON

> Cada operación realizada en cualquier microservicio debe generar un registro de log en formato JSON que contenga: la fecha y hora de la operación, el identificador de rastreo de la petición, el nombre del microservicio, la funcionalidad ejecutada, el método utilizado, el código de respuesta, la duración en milisegundos, el identificador del usuario que realizó la operación y un detalle descriptivo. Estos registros se envían de forma asíncrona al servicio de auditoría, de manera que el envío no bloquee ni retrase la respuesta al usuario. Si el envío al servicio de auditoría falla, el microservicio debe continuar operando normalmente.

---

### Fragmento 3 — Sección 7.18 ms-auditoria [AUD] (sección completa)

> **Propósito:** Servicio centralizado de auditoría y trazabilidad del sistema. Recibe los registros de log de todos los microservicios de forma asíncrona, los almacena en base de datos, permite la búsqueda por identificador de rastreo para reconstruir la traza completa de una petición a través de todos los servicios involucrados, y genera estadísticas de uso del sistema. Implementa rotación automática eliminando registros antiguos.
>
> ##### Información que gestiona
>
> **Eventos de log:** Cada registro de operación enviado por cualquier microservicio. Se requiere almacenar: la fecha y hora, el identificador de rastreo de la petición, el nombre del microservicio origen, la funcionalidad ejecutada, el método utilizado, el código de respuesta, la duración en milisegundos, el identificador del usuario y un detalle descriptivo.
>
> **Configuración de retención:** Parámetros de rotación de datos. Se requiere almacenar: la cantidad de días de retención (por defecto 30), el estado de la configuración, la fecha de la última rotación ejecutada y la cantidad de registros eliminados en la última rotación.
>
> **Estadísticas por servicio:** Métricas calculadas del uso del sistema. Se requiere almacenar: el nombre del microservicio, el periodo de la estadística (diario, semanal o mensual), la fecha, el total de peticiones, el total de errores, el tiempo promedio de respuesta en milisegundos, la funcionalidad más utilizada y la fecha del cálculo.
>
> ##### Requisitos funcionales
>
> - El sistema debe recibir registros de log en formato JSON de cualquier microservicio. La recepción debe ser asíncrona: el servicio debe confirmar la recepción inmediatamente y procesar el registro en segundo plano.
> - El sistema debe permitir recibir múltiples registros de log en una sola petición para optimizar el rendimiento.
> - El sistema debe permitir buscar registros por identificador de rastreo, retornando la traza completa de una petición a través de todos los microservicios que participaron en su procesamiento.
> - El sistema debe permitir filtrar registros por microservicio de origen, por fecha y por combinación de criterios.
> - El sistema debe implementar una rotación automática que elimine los registros con más antigüedad que la configurada en los días de retención (por defecto 30 días). Debe permitir también la ejecución manual de la rotación.
> - El sistema debe calcular y almacenar estadísticas de uso por servicio y periodo: total de peticiones, total de errores, tiempo promedio de respuesta y funcionalidad más utilizada.
> - El sistema debe permitir consultar las estadísticas generales del sistema y las estadísticas detalladas de un servicio específico.
> - Dado el volumen de datos que maneja este servicio, todas las consultas deben soportar paginación obligatoria.
>
> ##### Dependencias con otros servicios
>
> - Este servicio se audita a sí mismo: sus propias operaciones generan registros que se almacenan en su propia base de datos.

---

### Fragmento 4 — Sección 8. Mapa de Dependencias (fila y nota general)

> | ms-auditoria | (se audita a sí mismo) |
>
> Adicionalmente, todos los microservicios (excepto ms-autenticacion y ms-roles entre sí) consumen:
>
> - **ms-auditoria** para enviar registros de log de forma asíncrona.

---

### Fragmento 5 — Menciones en dependencias de otros microservicios (selección)

Los siguientes fragmentos son copias textuales tomadas de las secciones de dependencias de otros microservicios que hacen referencia directa a ms-auditoria:

- **ms-autenticacion:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-usuarios:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-roles:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-inventario:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-espacios:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-reservas:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-presupuesto:** *(aplica regla transversal 6.6)*
- **ms-gastos:** *(aplica regla transversal 6.6)*
- **ms-facturacion:** *(aplica regla transversal 6.6)*
- **ms-pedidos:** *(aplica regla transversal 6.6)*
- **ms-domicilios:** *(aplica regla transversal 6.6)*
- **ms-proveedores:** *(aplica regla transversal 6.6)*
- **ms-programas:** *(aplica regla transversal 6.6)*
- **ms-matriculas:** *(aplica regla transversal 6.6)*
- **ms-calificaciones:** *(aplica regla transversal 6.6)*
- **ms-horarios:** *(aplica regla transversal 6.6)*
- **ms-notificaciones:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."
- **ms-reportes:** "Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada."

---

## 2. Información General

| Campo | Detalle |
|---|---|
| **Nombre** | ms-auditoria |
| **Código** | AUD |
| **Módulo** | Módulo 6 — Transversales |
| **Stack** | FastAPI + Python + PostgreSQL |

**Propósito:** `ms-auditoria` es el servicio centralizado de auditoría y trazabilidad del sistema ERP universitario. Recibe los registros de log de todos los demás microservicios de forma asíncrona, los almacena y permite reconstruir la traza completa de cualquier petición a través de los servicios que participaron en su procesamiento. Adicionalmente, calcula estadísticas de uso del sistema e implementa rotación automática de registros antiguos.

**Rol dentro del sistema:** Es un servicio transversal de soporte consumido por la totalidad de los microservicios del sistema (18 de 19 servicios lo alimentan, más él mismo). Actúa como receptor pasivo de logs y como motor de trazabilidad y estadísticas. No bloquea las operaciones de los demás servicios: si falla, los microservicios deben continuar operando con normalidad.

---

## 3. Reglas de Negocio

### Reglas transversales del sistema que aplican a ms-auditoria

1. **Validación de sesión obligatoria:** Toda operación realizada por un usuario debe ser precedida por una validación de sesión activa consultando a `ms-autenticacion`. Si la sesión no es válida, la petición debe rechazarse inmediatamente.

2. **Validación de permisos por funcionalidad:** Tras validar la sesión, debe consultarse a `ms-roles` para verificar que el rol del usuario tiene autorización para ejecutar la funcionalidad solicitada.

3. **Tokens de aplicación para comunicación entre servicios:** El microservicio posee un token de aplicación único, fijo, cifrado con AES-256, que lo identifica ante los demás servicios. Solo puede actualizarse de forma manual por un administrador.

4. **Estructura de respuesta estándar:** Todas las respuestas deben incluir: identificador de rastreo, indicador de éxito/error, datos resultantes, mensaje descriptivo y fecha/hora de la respuesta.

5. **Trazabilidad distribuida (Request ID):** Cada petición que ingresa debe recibir o reutilizar un identificador único de rastreo con el formato `AUD-{timestamp Unix}-{id corto aleatorio}`. Si la petición proviene de otro servicio y ya trae un Request ID, debe reutilizarse. El identificador debe incluirse tanto en cabeceras como en el cuerpo de cada respuesta.

6. **Auto-auditoría:** Las propias operaciones de `ms-auditoria` generan registros de log que se almacenan en su propia base de datos. Este servicio se audita a sí mismo.

### Reglas específicas del microservicio

7. **Recepción asíncrona:** La recepción de registros de log debe ser asíncrona. El servicio debe confirmar la recepción de inmediato y procesar el registro en segundo plano, sin bloquear la respuesta al microservicio emisor.

8. **Recepción en lote:** El servicio debe soportar la recepción de múltiples registros de log en una sola petición (batch).

9. **Paginación obligatoria:** Dado el volumen de datos que maneja este servicio, todas las consultas deben soportar paginación obligatoria.

10. **Rotación automática de registros:** El sistema debe eliminar automáticamente los registros cuya antigüedad supere los días de retención configurados (por defecto 30 días). También debe permitir la ejecución manual de la rotación.

11. **No generación de credenciales en texto plano:** En ningún caso deben aparecer credenciales en texto plano en los logs, respuestas ni archivos de configuración.

### Reglas que provienen de su relación con otros microservicios

12. **Tolerancia a fallos en emisores:** Si cualquier microservicio emisor falla al enviar un log, ese microservicio debe continuar operando con normalidad. `ms-auditoria` no puede convertirse en un punto de fallo del sistema.

13. **Formato de log estandarizado:** Todos los registros recibidos deben cumplir el formato JSON con los campos definidos en la regla transversal 6.6: fecha/hora, Request ID, nombre del microservicio, funcionalidad, método, código de respuesta, duración en ms, ID de usuario y detalle descriptivo.

---

## 4. Entidades y Datos

### Entidad 1: Eventos de log

**Descripción:** Cada registro de operación enviado por cualquier microservicio.

**Atributos requeridos (texto original):**

> Se requiere almacenar: la fecha y hora, el identificador de rastreo de la petición, el nombre del microservicio origen, la funcionalidad ejecutada, el método utilizado, el código de respuesta, la duración en milisegundos, el identificador del usuario y un detalle descriptivo.

---

### Entidad 2: Configuración de retención

**Descripción:** Parámetros que controlan la rotación automática de datos.

**Atributos requeridos (texto original):**

> Se requiere almacenar: la cantidad de días de retención (por defecto 30), el estado de la configuración, la fecha de la última rotación ejecutada y la cantidad de registros eliminados en la última rotación.

---

### Entidad 3: Estadísticas por servicio

**Descripción:** Métricas calculadas del uso del sistema, agrupadas por microservicio y periodo.

**Atributos requeridos (texto original):**

> Se requiere almacenar: el nombre del microservicio, el periodo de la estadística (diario, semanal o mensual), la fecha, el total de peticiones, el total de errores, el tiempo promedio de respuesta en milisegundos, la funcionalidad más utilizada y la fecha del cálculo.

---

## 5. Funcionalidades Requeridas

*(Texto copiado sin modificar del documento original, sección 7.18)*

- El sistema debe recibir registros de log en formato JSON de cualquier microservicio. La recepción debe ser asíncrona: el servicio debe confirmar la recepción inmediatamente y procesar el registro en segundo plano.
- El sistema debe permitir recibir múltiples registros de log en una sola petición para optimizar el rendimiento.
- El sistema debe permitir buscar registros por identificador de rastreo, retornando la traza completa de una petición a través de todos los microservicios que participaron en su procesamiento.
- El sistema debe permitir filtrar registros por microservicio de origen, por fecha y por combinación de criterios.
- El sistema debe implementar una rotación automática que elimine los registros con más antigüedad que la configurada en los días de retención (por defecto 30 días). Debe permitir también la ejecución manual de la rotación.
- El sistema debe calcular y almacenar estadísticas de uso por servicio y periodo: total de peticiones, total de errores, tiempo promedio de respuesta y funcionalidad más utilizada.
- El sistema debe permitir consultar las estadísticas generales del sistema y las estadísticas detalladas de un servicio específico.
- Dado el volumen de datos que maneja este servicio, todas las consultas deben soportar paginación obligatoria.

---

## 6. Dependencias (de quién dependo)

| Microservicio | Información/funcionalidad consumida | Momento/contexto |
|---|---|---|
| **ms-autenticacion** | Validación de sesión activa | Antes de ejecutar cualquier lógica de negocio, en toda operación iniciada por un usuario |
| **ms-roles** | Validación de permisos por funcionalidad | Después de validar la sesión, para autorizar la ejecución de cada funcionalidad |
| **ms-auditoria** *(sí mismo)* | Sus propias operaciones generan registros de log que se almacenan en su propia base de datos | Con cada operación interna del servicio |

> **Nota:** `ms-auditoria` es el servicio con menor cantidad de dependencias externas del sistema. Solo consume `ms-autenticacion` y `ms-roles` (dependencias transversales obligatorias) y se auto-audita.

---

## 7. Consumidores (quién depende de mí)

Conforme a la regla transversal 6.6 y al mapa de dependencias (sección 8), **todos los microservicios del sistema** (excepto `ms-autenticacion` y `ms-roles` en su comunicación mutua de bootstrap) envían registros de log a `ms-auditoria`.

| Microservicio consumidor | Qué consume | Momento/contexto |
|---|---|---|
| ms-autenticacion | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-usuarios | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-roles | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-inventario | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-espacios | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-reservas | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-presupuesto | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-gastos | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-facturacion | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-pedidos | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-domicilios | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-proveedores | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-programas | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-matriculas | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-calificaciones | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-horarios | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-notificaciones | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |
| ms-reportes | Envío de registros de log en formato JSON | De forma asíncrona con cada operación realizada |

> **Total de consumidores:** 18 microservicios (la totalidad del sistema) más el propio `ms-auditoria` que se auto-audita.

---

*Documento generado a partir del archivo: Propuesta de Arquitectura y Requisitos Funcionales — ERP Universitario v1.0, Febrero 2026.*
