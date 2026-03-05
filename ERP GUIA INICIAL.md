# ERP UNIVERSITARIO

## Sistema de Gestión Integral basado en Microservicios

### Propuesta de Arquitectura y Requisitos Funcionales

| Campo | Detalle |
|-------|---------|
| **Documento** | Propuesta de Arquitectura y Requisitos Funcionales |
| **Versión** | 1.0 |
| **Fecha** | Febrero 2026 |
| **Elaborado por** | Raul Londoño Murillo — Arquitecto de Software |
| **Asignatura** | Desarrollo de Software III (750027C) |
| **Institución** | Universidad del Valle — Sede Caicedonia |
| **Stack** | FastAPI + Python + PostgreSQL |
| **Microservicios** | 19 servicios independientes |

---

## Tabla de Contenido

1. [Introducción](#1-introducción)
2. [Objetivo del Sistema](#2-objetivo-del-sistema)
3. [Alcance](#3-alcance)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Arquitectura General](#5-arquitectura-general)
6. [Reglas Transversales del Sistema](#6-reglas-transversales-del-sistema)
7. [Especificación Funcional por Microservicio](#7-especificación-funcional-por-microservicio)
8. [Mapa de Dependencias entre Microservicios](#8-mapa-de-dependencias-entre-microservicios)
9. [Glosario](#9-glosario)

---

## 1. Introducción

La Universidad del Valle, Sede Caicedonia, requiere un sistema de gestión integral que centralice y automatice los procesos administrativos, académicos, financieros y logísticos de la institución. Este documento presenta la propuesta de arquitectura y los requisitos funcionales para el desarrollo de dicho sistema, basado en una arquitectura de microservicios.

El sistema ha sido diseñado como un conjunto de 19 microservicios independientes que se comunican entre sí mediante interfaces REST. Cada microservicio es responsable de un dominio funcional específico y opera de forma autónoma con su propia base de datos, siguiendo los principios de responsabilidad única, bajo acoplamiento y alta cohesión propios de la arquitectura de microservicios.

Este documento tiene como propósito servir de insumo para que el equipo de desarrollo realice el levantamiento detallado de requisitos, la elaboración de diagramas (casos de uso, clases, entidad-relación, secuencia) y la posterior implementación de cada componente del sistema.

---

## 2. Objetivo del Sistema

Desarrollar una plataforma de gestión integral tipo ERP (Enterprise Resource Planning) para la Universidad del Valle, Sede Caicedonia, que permita:

- Administrar de forma centralizada los procesos de seguridad, acceso y control de usuarios.
- Gestionar los recursos físicos de la institución: inventario de activos, espacios y reservas.
- Controlar los procesos financieros: presupuestos, gastos, novedades y facturación.
- Automatizar los procesos logísticos: pedidos, entregas y gestión de proveedores.
- Soportar los procesos académicos: programas, matrículas, horarios y calificaciones.
- Proveer servicios transversales de notificaciones, auditoría y generación de reportes.
- Garantizar la seguridad, trazabilidad y auditabilidad de todas las operaciones del sistema.

---

## 3. Alcance

### 3.1 Dentro del alcance

- Desarrollo de 19 microservicios independientes con comunicación REST.
- Sistema completo de autenticación, gestión de sesiones y tokens de aplicación.
- Sistema de roles y permisos granular con control de acceso por funcionalidad.
- Trazabilidad distribuida de todas las operaciones mediante identificadores únicos de petición.
- Auditoría centralizada de logs con rotación automática.
- Módulos funcionales: Seguridad, Recursos, Financiero, Logística, Académico y Transversales.

### 3.2 Fuera del alcance

- Interfaz gráfica de usuario (frontend web o móvil).
- Integración con sistemas externos de la universidad (sistemas legados).
- Implementación de pasarelas de pago reales.
- Envío real de correos electrónicos o mensajes SMS (se simulará el envío).
- Despliegue en infraestructura de producción en la nube.

---

## 4. Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje de programación | Python |
| Framework de desarrollo | FastAPI |
| Base de datos | PostgreSQL |
| Comunicación entre servicios | REST (HTTP/JSON) |
| Autenticación | JWT (JSON Web Tokens) |
| Cifrado de contraseñas | bcrypt (salt rounds ≥ 12) |
| Cifrado de tokens de aplicación | AES-256 |
| Documentación de API | Swagger UI (generado automáticamente por FastAPI) |

---

## 5. Arquitectura General

El sistema se organiza en 6 módulos funcionales que agrupan los 19 microservicios:

### Módulo 1 — Seguridad y Acceso

Responsable de la autenticación de usuarios, gestión de sesiones, control de tokens de aplicación para comunicación entre servicios, y administración de roles y permisos.

- ms-autenticacion
- ms-usuarios
- ms-roles

### Módulo 2 — Gestión de Recursos

Responsable del control de activos institucionales, espacios físicos y sistema de reservas.

- ms-inventario
- ms-espacios
- ms-reservas

### Módulo 3 — Financiero

Responsable de la gestión presupuestal, control de gastos y novedades, y facturación.

- ms-presupuesto
- ms-gastos
- ms-facturacion

### Módulo 4 — Logística y Proveedores

Responsable de pedidos internos, gestión de entregas y administración de proveedores.

- ms-pedidos
- ms-domicilios
- ms-proveedores

### Módulo 5 — Académico

Responsable de la estructura académica, matrículas, programación de horarios y calificaciones.

- ms-programas
- ms-matriculas
- ms-calificaciones
- ms-horarios

### Módulo 6 — Transversales

Servicios de soporte consumidos por los demás módulos: notificaciones, auditoría y reportes.

- ms-notificaciones
- ms-auditoria
- ms-reportes

---

## 6. Reglas Transversales del Sistema

Las siguientes reglas son de cumplimiento obligatorio para todos los microservicios del sistema. Representan requisitos no funcionales y de seguridad que garantizan la integridad, trazabilidad y protección del sistema.

### 6.1 Validación de Sesión Obligatoria

Toda operación realizada por un usuario a través de cualquier microservicio debe ser precedida por una validación de sesión activa. El microservicio que recibe la petición del usuario debe consultar al servicio de autenticación para confirmar que la sesión es válida antes de ejecutar cualquier lógica de negocio. Si la sesión no es válida, el sistema debe rechazar la petición inmediatamente sin procesarla.

### 6.2 Validación de Permisos por Funcionalidad

Cada funcionalidad del sistema tiene asociado un código de permiso único. Después de validar la sesión, el microservicio debe consultar al servicio de roles para verificar que el rol del usuario tiene autorización para ejecutar la funcionalidad solicitada. Si el usuario no tiene el permiso correspondiente, el sistema debe rechazar la petición.

### 6.3 Tokens de Aplicación para Comunicación entre Servicios

Cada microservicio posee un token de aplicación único que lo identifica ante los demás servicios. Este token es fijo (no expira ni se renueva automáticamente) y solo puede ser actualizado de forma manual por un administrador. Los tokens se almacenan cifrados con AES-256 y se transmiten cifrados en cada petición entre servicios. Cualquier microservicio puede comunicarse con cualquier otro siempre que posea un token activo y válido.

### 6.4 Cifrado de Credenciales

Las contraseñas de los usuarios nunca se almacenan en texto plano. Se guardan como hash generado con bcrypt con un factor de costo mínimo de 12. Además, las contraseñas se transmiten cifradas desde el cliente hacia el servidor utilizando AES-256 con codificación Base64. El servidor descifra la contraseña recibida antes de compararla con el hash almacenado. Los tokens de aplicación siguen la misma política: se almacenan cifrados y se transmiten cifrados. En ningún caso deben aparecer credenciales en texto plano en logs, respuestas del sistema ni archivos de configuración.

### 6.5 Trazabilidad Distribuida (Request ID)

Cada petición que ingresa al sistema recibe un identificador único de rastreo con el formato: código del servicio que la recibe, seguido de un timestamp Unix y un identificador corto aleatorio (ejemplo: `PED-1740000000-a3f8b2`). Este identificador se propaga a todos los microservicios que participan en el procesamiento de la petición. Si un servicio recibe una petición que ya trae un identificador de rastreo (porque proviene de otro servicio), debe reutilizarlo en lugar de generar uno nuevo. Toda respuesta del sistema, independientemente de si la operación fue exitosa o fallida, debe incluir este identificador tanto en las cabeceras como en el cuerpo de la respuesta.

### 6.6 Auditoría y Logs en Formato JSON

Cada operación realizada en cualquier microservicio debe generar un registro de log en formato JSON que contenga: la fecha y hora de la operación, el identificador de rastreo de la petición, el nombre del microservicio, la funcionalidad ejecutada, el método utilizado, el código de respuesta, la duración en milisegundos, el identificador del usuario que realizó la operación y un detalle descriptivo. Estos registros se envían de forma asíncrona al servicio de auditoría, de manera que el envío no bloquee ni retrase la respuesta al usuario. Si el envío al servicio de auditoría falla, el microservicio debe continuar operando normalmente.

### 6.7 Estructura de Respuesta Estándar

Todas las respuestas del sistema deben seguir una estructura uniforme que incluya: el identificador de rastreo de la petición, un indicador de éxito o error, los datos resultantes de la operación, un mensaje descriptivo y la fecha y hora de la respuesta.

---

## 7. Especificación Funcional por Microservicio

A continuación, se describe cada microservicio con su propósito, la información que debe gestionar, los requisitos funcionales que debe cumplir y sus responsabilidades adicionales.

---

### Módulo 1: Seguridad y Acceso

---

#### 7.1 ms-autenticacion [AUTH]

**Propósito:** Servicio central de seguridad del sistema. Es responsable de autenticar a los usuarios, gestionar sus sesiones activas, administrar los tokens de aplicación que permiten la comunicación entre microservicios y proveer la funcionalidad de validación de sesión que todos los demás servicios deben consumir antes de ejecutar cualquier operación.

##### Información que gestiona

**Sesiones de usuario:** El sistema debe registrar y mantener las sesiones activas de los usuarios. De cada sesión se requiere almacenar: el usuario al que pertenece, el token generado para la sesión, la dirección IP desde la cual se conectó, la información del navegador o cliente utilizado, la fecha y hora en que se creó la sesión, la fecha y hora de la última actividad registrada y el estado de la sesión (activa o cerrada). Se debe registrar también la fecha y hora de creación y de cualquier modificación al registro.

**Tokens de aplicación:** El sistema debe almacenar los tokens que identifican a cada microservicio. De cada token se requiere: el nombre del servicio al que pertenece, el valor del token almacenado de forma cifrada, una descripción del servicio, el estado del token (activo o inactivo), la fecha de creación, quién realizó la última actualización y la fecha de dicha actualización.

**Historial de accesos:** El sistema debe registrar un historial de todos los eventos de acceso. De cada evento se requiere: el usuario involucrado, el tipo de evento (inicio de sesión, cierre de sesión, intento fallido o bloqueo de cuenta), la dirección IP, la información del navegador o cliente, la fecha y hora del evento y el identificador de rastreo de la petición.

##### Requisitos funcionales

- El sistema debe permitir a un usuario iniciar sesión proporcionando sus credenciales cifradas. Al autenticarse correctamente, debe generar un token JWT que contenga el identificador del usuario, su rol y sus permisos, y crear un registro de sesión activa.
- El sistema debe permitir a un usuario cerrar su sesión, invalidando el token y marcando la sesión como cerrada.
- El sistema debe proveer una funcionalidad de validación de sesión que, dado un token de usuario, verifique que la sesión existe en la base de datos y que se encuentra activa. Este es el servicio más crítico del sistema, ya que todos los demás microservicios lo consumen antes de ejecutar cualquier operación.
- El sistema debe permitir crear, consultar, actualizar y desactivar tokens de aplicación. Los tokens se generan cifrados con AES-256 y no tienen fecha de expiración; solo se actualizan o desactivan de forma manual.
- El sistema debe permitir listar las sesiones activas del sistema, con posibilidad de filtrar por usuario, y permitir forzar el cierre de una sesión específica por parte de un administrador.
- El sistema debe permitir consultar el historial de accesos con filtros por usuario, tipo de evento y rango de fechas.
- El sistema debe implementar un mecanismo de bloqueo por intentos fallidos: después de 5 intentos consecutivos de inicio de sesión fallidos, la cuenta del usuario debe bloquearse. El contador de intentos se reinicia cuando el usuario inicia sesión exitosamente.
- Las sesiones no expiran por tiempo. Solo se invalidan mediante cierre de sesión explícito por parte del usuario o cierre forzado por un administrador.

##### Dependencias con otros servicios

- Debe consultar al servicio de usuarios para obtener los datos del usuario y verificar sus credenciales durante el inicio de sesión.
- Debe consultar al servicio de roles para obtener el rol y los permisos del usuario al momento de generar el token JWT.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.2 ms-usuarios [USR]

**Propósito:** Gestiona toda la información de los usuarios del sistema: sus credenciales de acceso, datos personales, información de contacto y estados. Es el servicio de referencia cuando cualquier otro componente del sistema necesita datos de un usuario.

##### Información que gestiona

**Usuarios:** Información de las credenciales y estado de cada usuario. Se requiere almacenar: un nombre de usuario único, una dirección de correo electrónico única, la contraseña almacenada como hash cifrado, el estado del usuario (activo, inactivo o suspendido), la fecha y hora de registro y la fecha y hora de la última actualización.

**Perfiles:** Información personal y de contacto extendida de cada usuario. Se requiere almacenar: el tipo de documento de identidad, el número de documento (único), primer nombre, segundo nombre, primer apellido, segundo apellido, fecha de nacimiento, género, dirección de residencia, ciudad, departamento, teléfono fijo, teléfono móvil, nombre del contacto de emergencia, teléfono del contacto de emergencia y una biografía o descripción personal. Se debe registrar la fecha de creación y la fecha de la última actualización del perfil.

**Historial de estados:** Cada vez que el estado de un usuario cambia, se debe registrar: el estado anterior, el nuevo estado, el motivo del cambio, la fecha y hora del cambio y el identificador del usuario que realizó el cambio.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y desactivar usuarios. La desactivación debe ser lógica (no se eliminan registros de la base de datos), cambiando el estado a inactivo y registrando el motivo.
- Al crear un usuario, el sistema debe recibir la contraseña cifrada, descifrarla y almacenarla como hash bcrypt. Debe validar que el nombre de usuario, el correo electrónico y el número de documento no estén duplicados.
- El sistema debe permitir consultar y actualizar el perfil extendido de cada usuario de forma independiente.
- El sistema debe permitir cambiar el estado de un usuario proporcionando un motivo, y debe registrar este cambio en el historial de estados.
- El sistema debe permitir consultar el historial de cambios de estado de un usuario.
- El sistema debe ofrecer una búsqueda avanzada que permita filtrar usuarios por combinaciones de nombre, número de documento, correo electrónico, estado y ciudad, con paginación de resultados que incluya el total de registros y el total de páginas.
- El sistema debe permitir buscar un usuario por su correo electrónico (utilizado internamente por el servicio de autenticación para validar credenciales).
- El sistema debe permitir buscar un usuario por su número de documento.

##### Dependencias con otros servicios

- Debe consultar al servicio de roles para verificar que el rol asignado a un nuevo usuario exista.
- Debe enviar notificaciones a través del servicio de notificaciones cuando una cuenta de usuario es creada, activada o suspendida.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.3 ms-roles [ROL]

**Propósito:** Administra los roles, los permisos (códigos únicos asociados a cada funcionalidad del sistema) y las asignaciones entre ellos. Es el servicio que todos los demás microservicios consultan para determinar si un usuario tiene autorización para ejecutar una funcionalidad específica. El responsable de este servicio debe coordinar con los responsables de los otros 18 microservicios para recopilar y registrar todos los códigos de permiso del sistema.

##### Información que gestiona

**Roles:** Definición de los roles del sistema. Se requiere almacenar: un nombre único para el rol, una descripción, el estado (activo o inactivo) y la fecha de creación. Los roles no tienen herencia; los permisos se asignan directamente a cada rol.

**Permisos:** Cada funcionalidad del sistema tiene un código de permiso único. Se requiere almacenar: el código del permiso (único en todo el sistema, por ejemplo: `PED_CREATE`), un nombre legible, una descripción, el módulo al que pertenece, el microservicio de origen, la funcionalidad asociada y el método de operación (consulta, creación, actualización, eliminación). Se debe registrar la fecha de creación y de actualización.

**Asignaciones rol-permiso:** Registro de qué permisos tiene asignado cada rol. Se requiere almacenar: el rol, el permiso asignado, la fecha de asignación y quién realizó la asignación.

**Asignaciones usuario-rol:** Registro de qué rol tiene asignado cada usuario. Se requiere almacenar: el usuario, el rol asignado, la fecha de asignación, quién realizó la asignación y el estado de la asignación.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y desactivar roles.
- El sistema debe permitir registrar, consultar, actualizar y eliminar permisos. Cada permiso debe tener un código único en todo el sistema.
- El sistema debe permitir asignar uno o varios permisos a un rol, y remover permisos de un rol.
- El sistema debe permitir asignar un rol a un usuario, listar los roles de un usuario y remover un rol de un usuario.
- El sistema debe proveer una funcionalidad de validación de permisos que, dado un rol y un código de permiso, retorne si el rol tiene autorización para esa funcionalidad. Este es el segundo servicio más crítico del sistema, ya que todos los microservicios lo consultan después de validar la sesión.
- El sistema debe permitir consultar los permisos organizados por módulo para facilitar la administración.
- El sistema debe detectar y prevenir la asignación de roles contradictorios a un mismo usuario.
- El sistema debe incluir una carga inicial de datos semilla con los roles básicos del sistema: Administrador, Docente, Estudiante y Operador, junto con sus permisos correspondientes.

##### Dependencias con otros servicios

- Tiene una relación de confianza mutua con el servicio de autenticación mediante tokens de aplicación preconfigurados (bootstrap de seguridad).
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

### Módulo 2: Gestión de Recursos

---

#### 7.4 ms-inventario [INV]

**Propósito:** Gestiona los activos físicos de la institución: equipos, insumos, mobiliario y cualquier bien inventariable. Controla el stock, los movimientos de entrada y salida, la depreciación de activos y genera alertas cuando el stock se encuentra por debajo del mínimo establecido.

##### Información que gestiona

**Activos:** Cada bien inventariable de la institución. Se requiere almacenar: un código interno único, nombre del activo, descripción, la categoría a la que pertenece, el proveedor de origen, el precio de adquisición, la fecha de adquisición, la vida útil estimada en meses, el valor de depreciación calculado actualmente, la ubicación física, el estado del activo (disponible, en uso, en mantenimiento o dado de baja), la cantidad actual en stock y la cantidad mínima de stock. Se debe registrar la fecha de creación y de cada actualización.

**Categorías:** Clasificación jerárquica de los activos. Se requiere almacenar: el nombre de la categoría, una descripción, la referencia a una categoría padre (para soportar subcategorías) y el estado. Se debe registrar la fecha de creación.

**Movimientos de stock:** Registro de cada entrada, salida, ajuste o transferencia de activos. Se requiere almacenar: el activo involucrado, el tipo de movimiento (entrada, salida, ajuste o transferencia), la cantidad, el motivo del movimiento, el usuario responsable, la fecha y hora del movimiento, una referencia al pedido relacionado (si aplica) y el identificador de rastreo de la petición.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y dar de baja activos. La baja debe ser lógica, cambiando el estado del activo.
- El sistema debe permitir crear, consultar y actualizar categorías organizadas de forma jerárquica (con categorías padre e hija).
- El sistema debe permitir registrar movimientos de stock (entradas, salidas, ajustes y transferencias). Cada movimiento debe actualizar automáticamente la cantidad en stock del activo. No se deben permitir salidas que resulten en stock negativo.
- El sistema debe permitir consultar el historial completo de movimientos de un activo específico.
- El sistema debe permitir listar todos los activos cuyo stock actual sea igual o inferior al stock mínimo configurado, y debe enviar alertas automáticas a través del servicio de notificaciones cuando esto ocurra.
- El sistema debe calcular la depreciación actual de un activo utilizando el método de línea recta: valor depreciado = (precio de adquisición / vida útil en meses) × meses transcurridos desde la adquisición.

##### Dependencias con otros servicios

- Debe consultar al servicio de proveedores para obtener datos del proveedor al registrar activos.
- Debe enviar alertas a través del servicio de notificaciones cuando el stock de un activo cae por debajo del mínimo.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.5 ms-espacios [ESP]

**Propósito:** Gestiona los espacios físicos de la institución: aulas, laboratorios, auditorios, oficinas y salas de reuniones. Controla su capacidad, el equipamiento asignado, los estados de disponibilidad, los mantenimientos programados y las estadísticas de ocupación.

##### Información que gestiona

**Espacios:** Cada espacio físico de la institución. Se requiere almacenar: un código único, nombre del espacio, tipo (aula, laboratorio, auditorio, oficina o sala de reuniones), edificio, piso, capacidad máxima de personas, estado (disponible, en mantenimiento, fuera de servicio o reservado), una descripción y la fecha de registro. Se debe registrar la fecha de creación y de cada actualización.

**Tipos de espacio:** Clasificación de los tipos de espacio. Se requiere almacenar: nombre del tipo, descripción, si requiere equipamiento especial y estado.

**Equipamiento de espacios:** Relación entre los espacios y los activos asignados a ellos (proyectores, computadores, tableros, etc.). Se requiere almacenar: el espacio, el activo asignado, la cantidad, la fecha de asignación y el estado de la asignación.

**Mantenimientos programados:** Registro de los mantenimientos planificados para cada espacio. Se requiere almacenar: el espacio, una descripción del mantenimiento, el responsable, el costo estimado, la fecha programada, la fecha de ejecución real, el estado (programado, en ejecución, completado o cancelado) y observaciones. Se debe registrar la fecha de creación y de actualización.

**Historial de ocupación:** Estadísticas de uso de cada espacio. Se requiere almacenar: el espacio, la fecha, las horas ocupadas, las horas disponibles, el porcentaje de uso y el periodo al que corresponde.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y desactivar espacios.
- El sistema debe permitir cambiar el estado de un espacio registrando quién realizó el cambio y el motivo.
- El sistema debe permitir crear y consultar tipos de espacio.
- El sistema debe permitir asignar y remover equipamiento (activos del inventario) a los espacios, validando que el activo exista y esté disponible en el inventario.
- El sistema debe permitir buscar espacios disponibles filtrando por tipo, capacidad mínima requerida, edificio y estado.
- El sistema debe permitir crear, consultar y actualizar mantenimientos programados. Al programar un mantenimiento, el estado del espacio debe cambiar automáticamente a "en mantenimiento". Al completar el mantenimiento, debe volver a "disponible".
- El sistema debe permitir consultar las estadísticas de ocupación de cada espacio, mostrando el porcentaje de uso por periodo.

##### Dependencias con otros servicios

- Debe consultar al servicio de inventario para validar la existencia y disponibilidad de activos al asignar equipamiento.
- Debe enviar alertas a través del servicio de notificaciones cuando un espacio pasa a estado de mantenimiento o fuera de servicio.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.6 ms-reservas [RES]

**Propósito:** Motor de reservas para los espacios y recursos de la institución. Gestiona la disponibilidad, detecta conflictos de horario, aplica políticas de cancelación y administra bloqueos de espacios. El sistema solo soporta reservas únicas (no recurrentes).

##### Información que gestiona

**Reservas:** Cada reserva de un espacio. Se requiere almacenar: el espacio reservado, el usuario que realizó la reserva, un título descriptivo, una descripción detallada, la fecha y hora de inicio, la fecha y hora de fin, el estado (pendiente, confirmada, cancelada o completada), la fecha de creación, quién canceló la reserva (si aplica) y el motivo de la cancelación. Se debe registrar la fecha de creación y de actualización.

**Políticas de reserva:** Reglas que rigen el comportamiento del sistema de reservas. Se requiere almacenar: nombre de la política, el tiempo mínimo de anticipación en horas para crear una reserva, el tiempo máximo de anticipación en días, la duración máxima permitida en horas, el tiempo límite en horas antes de la reserva para permitir cancelación, la cantidad máxima de reservas activas que un usuario puede tener simultáneamente y el estado de la política.

**Bloqueos de espacio:** Periodos en los que un espacio no puede ser reservado. Se requiere almacenar: el espacio bloqueado, la fecha y hora de inicio del bloqueo, la fecha y hora de fin, el motivo, quién creó el bloqueo y la fecha de creación.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar, cancelar y confirmar reservas.
- Al crear o actualizar una reserva, el sistema debe detectar y rechazar conflictos de horario: no se permite que dos reservas se solapen en el mismo espacio.
- Al cancelar una reserva, el sistema debe validar que se cumplan las políticas de cancelación (tiempo límite). Si la cancelación está fuera del límite permitido, debe rechazarla. Se debe registrar el motivo de la cancelación.
- El sistema debe validar que un usuario no exceda la cantidad máxima de reservas activas configurada en la política.
- El sistema debe permitir consultar la disponibilidad de un espacio en un rango de fechas.
- El sistema debe permitir crear, consultar y actualizar políticas de reserva.
- El sistema debe permitir crear, consultar y eliminar bloqueos de espacio. Un espacio bloqueado no puede ser reservado durante el periodo del bloqueo.

##### Dependencias con otros servicios

- Debe consultar al servicio de espacios para validar que el espacio existe, está disponible y tiene la capacidad requerida.
- Debe consultar al servicio de horarios para verificar que no haya conflicto con horarios académicos programados.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

### Módulo 3: Financiero

---

#### 7.7 ms-presupuesto [PRE]

**Propósito:** Gestiona los presupuestos institucionales, las partidas presupuestales y la asignación de fondos por área. Controla los topes de gasto, permite reasignaciones entre partidas con flujo de aprobación y genera alertas cuando el consumo se acerca al límite configurado.

##### Información que gestiona

**Presupuestos:** El presupuesto general de la institución por periodo. Se requiere almacenar: nombre del presupuesto, periodo académico al que corresponde, monto total, monto ejecutado, monto disponible, estado (borrador, aprobado, en ejecución o cerrado), la fecha de creación, quién lo aprobó y la fecha de aprobación. Se debe registrar la fecha de creación y de actualización.

**Partidas:** Subdivisiones del presupuesto asignadas a áreas específicas. Se requiere almacenar: el presupuesto al que pertenece, nombre de la partida, el área destino, el monto asignado, el monto ejecutado, el monto disponible, el porcentaje a partir del cual se genera una alerta (por defecto 80%) y el estado. Se debe registrar la fecha de creación y de actualización.

**Reasignaciones:** Transferencias de fondos entre partidas. Se requiere almacenar: la partida de origen, la partida de destino, el monto a transferir, el motivo, quién solicitó la reasignación, quién la aprobó, la fecha y el estado (pendiente, aprobada o rechazada).

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y aprobar presupuestos.
- El sistema debe permitir crear, consultar y actualizar partidas presupuestales asociadas a un presupuesto.
- El sistema debe permitir consultar el saldo disponible de una partida en cualquier momento.
- El sistema no debe permitir que una partida supere su monto asignado. Antes de aprobar cualquier gasto, se debe validar que exista saldo disponible.
- Cuando el monto ejecutado de una partida alcance el porcentaje de alerta configurado, el sistema debe enviar una notificación automática.
- El sistema debe permitir solicitar reasignaciones de fondos entre partidas. Las reasignaciones requieren un flujo de aprobación: se solicitan, se aprueban o rechazan. Al aprobarse, los montos se actualizan automáticamente en ambas partidas.
- El sistema debe calcular automáticamente el monto disponible como la diferencia entre el monto asignado y el monto ejecutado, actualizando en cascada al presupuesto padre.
- El sistema debe permitir consultar un resumen de ejecución presupuestal por presupuesto.

##### Dependencias con otros servicios

- Debe consultar al servicio de gastos para conocer los gastos aprobados y actualizar la ejecución presupuestal.
- Debe enviar alertas a través del servicio de notificaciones cuando una partida alcanza su porcentaje de alerta o cuando hay reasignaciones pendientes.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.8 ms-gastos [GAS]

**Propósito:** Registra y controla los gastos de la institución, las novedades asociadas y su flujo de aprobación. Clasifica los gastos por categoría, valida contra el presupuesto disponible y gestiona el ciclo completo desde la solicitud hasta el pago.

##### Información que gestiona

**Gastos:** Cada gasto registrado en el sistema. Se requiere almacenar: una descripción del gasto, el monto, la categoría del gasto, la partida presupuestal contra la que se carga, el proveedor asociado, el estado del gasto (solicitado, en revisión, aprobado, rechazado o pagado), quién lo solicitó, la fecha de solicitud, quién lo aprobó, la fecha de aprobación, la fecha de pago y observaciones. Se debe registrar la fecha de creación y de actualización.

**Categorías de gasto:** Clasificación de los tipos de gasto. Se requiere almacenar: nombre de la categoría, descripción, si requiere aprobación especial y estado.

**Novedades:** Eventos inesperados asociados a un gasto (sobrecostos, retrasos, cambios de alcance, imprevistos). Se requiere almacenar: el gasto al que se asocia, el tipo de novedad (sobrecosto, retraso, cambio de alcance o imprevisto), una descripción, el monto del impacto económico, quién reportó la novedad, la fecha del reporte y el estado (abierta, resuelta o escalada). Se debe registrar la fecha de creación y de actualización.

**Aprobaciones:** Registro de cada decisión de aprobación o rechazo de un gasto. Se requiere almacenar: el gasto evaluado, el aprobador, la decisión (aprobado o rechazado), un comentario y la fecha.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar y actualizar gastos. Un gasto solo puede ser modificado mientras se encuentre en estado "solicitado".
- El sistema debe implementar un flujo de aprobación obligatorio: solicitado → en revisión → aprobado o rechazado → pagado. No se permite saltar estados.
- Antes de aprobar un gasto, el sistema debe consultar al servicio de presupuesto para verificar que la partida presupuestal asociada tiene saldo disponible suficiente.
- El sistema debe permitir crear y consultar categorías de gasto.
- El sistema debe permitir registrar, consultar, actualizar y resolver novedades asociadas a un gasto. Si el monto de impacto de una novedad supera un umbral definido, la novedad debe escalarse.
- El sistema debe registrar cada decisión de aprobación o rechazo con el comentario del aprobador.

##### Dependencias con otros servicios

- Debe consultar al servicio de presupuesto para validar saldo disponible antes de aprobar un gasto.
- Debe consultar al servicio de proveedores para obtener los datos del proveedor asociado al gasto.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.9 ms-facturacion [FAC]

**Propósito:** Genera y gestiona las facturas de la institución, los conceptos de cobro y los estados de cuenta de los usuarios. Calcula totales con impuestos, controla los estados de pago, detecta facturas vencidas y permite la generación masiva de facturas para cobros recurrentes.

##### Información que gestiona

**Facturas:** Cada factura emitida por la institución. Se requiere almacenar: un número de factura único y secuencial generado automáticamente, el usuario al que se factura, la fecha de emisión, la fecha de vencimiento, el subtotal, el porcentaje de impuesto aplicado, el valor del impuesto calculado, el total, el estado (emitida, pagada, vencida o anulada), la fecha de pago (si aplica) y observaciones. Se debe registrar la fecha de creación y de actualización.

**Conceptos de cobro:** Definición de los diferentes conceptos que se pueden facturar. Se requiere almacenar: nombre del concepto, descripción, valor base, si es un cobro recurrente, la periodicidad (si aplica) y estado.

**Detalles de factura:** Cada línea de detalle dentro de una factura. Se requiere almacenar: la factura a la que pertenece, el concepto de cobro, una descripción, la cantidad, el valor unitario y el subtotal de la línea.

**Estados de cuenta:** Resumen financiero por usuario. Se requiere almacenar: el usuario, el total facturado histórico, el total pagado, el saldo pendiente, la cantidad de facturas vencidas y la fecha de la última actualización.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar, pagar y anular facturas. Una factura solo puede ser modificada mientras se encuentre en estado "emitida".
- El sistema debe generar automáticamente un número de factura único y secuencial al crear cada factura.
- El sistema debe calcular automáticamente: subtotal como la suma de cantidad por valor unitario de cada línea de detalle, el valor del impuesto como subtotal multiplicado por el porcentaje de impuesto, y el total como subtotal más impuesto.
- El sistema debe detectar automáticamente las facturas cuya fecha de vencimiento haya pasado y que no hayan sido pagadas, marcándolas como vencidas.
- El sistema debe mantener actualizado el estado de cuenta de cada usuario, reflejando totales facturados, pagados, saldo pendiente y cantidad de facturas vencidas.
- El sistema debe permitir crear, consultar y actualizar conceptos de cobro.
- El sistema debe permitir generar facturas de forma masiva para un concepto de cobro recurrente, creando una factura por cada usuario que corresponda.

##### Dependencias con otros servicios

- Debe consultar al servicio de matrículas para obtener los datos necesarios al generar facturas de inscripción.
- Debe enviar alertas a través del servicio de notificaciones para facturas próximas a vencer y facturas vencidas.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

### Módulo 4: Logística y Proveedores

---

#### 7.10 ms-pedidos [PED]

**Propósito:** Gestiona los pedidos internos y las órdenes de compra de la institución. Controla el flujo completo desde la creación del pedido en borrador hasta la recepción de los bienes, incluyendo la posibilidad de recepciones parciales.

##### Información que gestiona

**Pedidos:** Cada orden de compra o pedido interno. Se requiere almacenar: un número de pedido único, el solicitante, el proveedor asignado, el estado (borrador, enviado, aprobado, en proceso, recibido parcial, recibido o cancelado), la fecha de solicitud, la fecha de aprobación, la fecha de recepción, el monto total y observaciones. Se debe registrar la fecha de creación y de actualización.

**Ítems de pedido:** Cada línea de detalle dentro de un pedido. Se requiere almacenar: el pedido al que pertenece, el activo solicitado, una descripción, la cantidad solicitada, la cantidad recibida hasta el momento, el valor unitario, el subtotal de la línea y el estado del ítem (pendiente, recibido parcial o recibido).

**Historial de estados del pedido:** Registro de cada cambio de estado del pedido. Se requiere almacenar: el pedido, el estado anterior, el nuevo estado, quién realizó el cambio, la fecha y hora del cambio y un comentario.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar y actualizar pedidos. Un pedido solo puede ser modificado mientras se encuentre en estado "borrador".
- El sistema debe implementar un flujo de estados: borrador → enviado → aprobado → en proceso → recibido. Cada cambio de estado debe quedar registrado en el historial con la fecha, el usuario y un comentario.
- El sistema debe permitir cancelar un pedido en cualquier estado previo a "recibido", registrando el motivo de la cancelación.
- El sistema debe permitir registrar recepciones parciales: recibir una cantidad menor a la solicitada por cada ítem. El estado del ítem y del pedido debe actualizarse automáticamente según corresponda.
- El sistema debe permitir agregar, actualizar y remover ítems de un pedido mientras esté en estado borrador.
- El sistema debe calcular automáticamente el monto total del pedido como la suma de cantidad solicitada por valor unitario de cada ítem.
- El sistema debe permitir consultar el historial completo de cambios de estado de un pedido.

##### Dependencias con otros servicios

- Debe consultar al servicio de inventario para verificar que los activos solicitados existen y para registrar la entrada de stock al momento de la recepción.
- Debe consultar al servicio de proveedores para validar que el proveedor existe y tiene un contrato vigente.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.11 ms-domicilios [DOM]

**Propósito:** Gestiona las entregas a domicilio, la asignación de repartidores, el seguimiento en tiempo real de las rutas y la calificación del servicio de entrega.

##### Información que gestiona

**Entregas:** Cada entrega programada. Se requiere almacenar: el pedido que origina la entrega, el repartidor asignado, la dirección de origen, la dirección de destino, el estado (asignada, en camino, entregada, fallida o devuelta), la fecha de asignación, la fecha de recogida, la fecha de entrega, el costo del envío y observaciones. Se debe registrar la fecha de creación y de actualización.

**Repartidores:** Información de cada repartidor disponible. Se requiere almacenar: el usuario asociado, nombre, teléfono, tipo de vehículo, placa del vehículo, el estado (disponible, en ruta o inactivo), la zona de cobertura y la calificación promedio actual. Se debe registrar la fecha de registro y de actualización.

**Seguimiento:** Puntos de rastreo de cada entrega. Se requiere almacenar: la entrega, el estado en ese punto, la latitud, la longitud, la fecha y hora y una nota descriptiva.

**Calificaciones:** Evaluación del servicio de cada entrega. Se requiere almacenar: la entrega calificada, quién calificó, la puntuación (de 1 a 5), un comentario y la fecha.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar y actualizar entregas.
- El sistema debe permitir actualizar el estado de una entrega y debe generar automáticamente un punto de seguimiento con cada cambio de estado.
- El sistema debe permitir asignar un repartidor a una entrega, validando que el repartidor esté disponible y que su zona de cobertura corresponda con la dirección de destino.
- El sistema debe permitir crear, consultar y actualizar repartidores, así como listar los repartidores disponibles filtrados por zona de cobertura.
- El sistema debe permitir consultar el historial completo de seguimiento de una entrega.
- El sistema debe permitir registrar puntos de seguimiento con coordenadas geográficas durante el transcurso de una entrega.
- El sistema debe permitir calificar una entrega únicamente cuando se encuentre en estado "entregada". No se permite calificar entregas en curso o fallidas.
- El sistema debe calcular y mantener actualizada la calificación promedio de cada repartidor basándose en todas las calificaciones recibidas.
- El sistema debe calcular el costo de envío basándose en una tarifa fija configurable o en un cálculo simplificado por distancia.

##### Dependencias con otros servicios

- Debe consultar al servicio de pedidos para obtener los datos del pedido asociado a la entrega.
- Debe enviar notificaciones a través del servicio de notificaciones al solicitante cuando el estado de su entrega cambie.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.12 ms-proveedores [PRV]

**Propósito:** Gestiona la información de los proveedores de la institución, sus contratos, evaluaciones de desempeño, cotizaciones y documentos legales con control de vigencia.

##### Información que gestiona

**Proveedores:** Información de cada proveedor. Se requiere almacenar: el NIT (único), razón social, nombre del contacto, correo electrónico, teléfono, dirección, ciudad, estado (activo, inactivo o suspendido), la fecha de registro y el puntaje de evaluación actual. Se debe registrar la fecha de creación y de actualización.

**Contratos:** Contratos vigentes con los proveedores. Se requiere almacenar: el proveedor, un número de contrato único, el objeto del contrato, el monto total, la fecha de inicio, la fecha de fin, el estado (vigente, vencido, cancelado o en renovación), la URL del documento digitalizado y observaciones. Se debe registrar la fecha de creación y de actualización.

**Evaluaciones:** Evaluaciones periódicas del desempeño del proveedor. Se requiere almacenar: el proveedor, el contrato evaluado, el periodo de evaluación, calificaciones individuales (de 1 a 5) en calidad, cumplimiento de tiempos, precio competitivo y servicio postventa, el puntaje total calculado, quién realizó la evaluación y la fecha.

**Cotizaciones:** Propuestas de precio recibidas de los proveedores. Se requiere almacenar: el proveedor, la descripción del producto o servicio, el precio unitario, las condiciones comerciales, la vigencia de la cotización, la fecha y el estado.

**Documentos del proveedor:** Documentos legales requeridos. Se requiere almacenar: el proveedor, el tipo de documento (RUT, cámara de comercio, certificación o póliza), el nombre del documento, la URL del archivo, la fecha de emisión, la fecha de vencimiento y el estado (vigente, vencido o por vencer). Se debe registrar la fecha de carga del documento.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y desactivar proveedores. Debe validar que no se registren proveedores duplicados por NIT.
- El sistema debe permitir crear, consultar y actualizar contratos asociados a proveedores.
- El sistema debe permitir listar los contratos que vencen dentro de los próximos 30 días.
- El sistema debe permitir registrar evaluaciones de proveedores y calcular automáticamente el puntaje de evaluación actual del proveedor como el promedio de sus evaluaciones históricas.
- El sistema debe permitir registrar y consultar cotizaciones, así como comparar cotizaciones de diferentes proveedores para un mismo producto o servicio, mostrando precios y condiciones lado a lado.
- El sistema debe permitir registrar y consultar documentos legales de los proveedores, con control de vigencia. Debe listar los documentos próximos a vencer y enviar alertas automáticas.
- Cuando otro servicio consulte datos de un proveedor, el sistema debe informar si el contrato del proveedor se encuentra vigente.

##### Dependencias con otros servicios

- Debe enviar alertas a través del servicio de notificaciones para contratos y documentos próximos a vencer, y para proveedores con puntaje de evaluación bajo.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

### Módulo 5: Académico

---

#### 7.13 ms-programas [PRG]

**Propósito:** Gestiona la estructura académica de la institución: programas, asignaturas, prerrequisitos, malla curricular y versionamiento del pensum. Es la base de datos académica que alimenta los procesos de matrícula y programación de horarios.

##### Información que gestiona

**Programas académicos:** Cada carrera o programa ofrecido por la institución. Se requiere almacenar: un código único del programa, nombre, descripción, duración en semestres, total de créditos requeridos, estado (activo, inactivo o en revisión), el coordinador del programa y la fecha de creación. Se debe registrar la fecha de creación y de actualización.

**Asignaturas:** Cada materia que forma parte de un programa. Se requiere almacenar: un código único de la asignatura, nombre, descripción, cantidad de créditos, el semestre sugerido dentro del programa, el programa al que pertenece, las horas semanales, el tipo (teórica, práctica o teórico-práctica) y estado. Se debe registrar la fecha de creación y de actualización.

**Prerrequisitos:** Relación de dependencia entre asignaturas. Se requiere almacenar: la asignatura, la asignatura que es su prerrequisito y el tipo de prerrequisito (obligatorio o recomendado).

**Versiones de malla curricular:** Historial de cambios en la estructura del programa (pensum). Se requiere almacenar: el programa, el identificador de versión (ejemplo: `2026-v1`), la fecha desde la cual entra en vigencia, la fecha hasta la cual estuvo vigente (si ya fue reemplazada), el estado (vigente, histórica o borrador), una descripción de los cambios realizados y quién creó la versión. Se debe registrar la fecha de creación.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y desactivar programas académicos.
- El sistema debe permitir crear, consultar y actualizar asignaturas asociadas a un programa.
- El sistema debe permitir asignar y remover prerrequisitos entre asignaturas. Al asignar un prerrequisito, el sistema debe validar que no se generen ciclos (por ejemplo: A requiere B, B requiere C, C requiere A).
- El sistema debe permitir consultar la malla curricular completa de un programa, organizada por semestres y mostrando los prerrequisitos de cada asignatura.
- El sistema debe validar que los créditos totales de las asignaturas por semestre no excedan un máximo ni queden por debajo de un mínimo configurado.
- El sistema debe soportar versionamiento de la malla curricular: cuando el pensum cambia, se crea una nueva versión manteniendo el historial. Solo una versión puede estar vigente a la vez por programa.
- El sistema debe validar que el usuario asignado como coordinador del programa exista en el sistema.

##### Dependencias con otros servicios

- Debe consultar al servicio de usuarios para validar la existencia del coordinador del programa.
- Debe proveer información al servicio de horarios con las asignaturas disponibles para programación.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.14 ms-matriculas [MAT]

**Propósito:** Gestiona los periodos académicos, las matrículas de estudiantes y las inscripciones a asignaturas. Es el punto central del proceso de inscripción, encargado de validar prerrequisitos, cupos máximos y cruces de horario antes de permitir que un estudiante se inscriba en una asignatura.

##### Información que gestiona

**Periodos académicos:** Definición de cada periodo lectivo. Se requiere almacenar: un nombre identificador (ejemplo: `2026-1`), la fecha de inicio del periodo, la fecha de fin, la fecha de inicio del periodo de inscripciones, la fecha de fin del periodo de inscripciones y el estado (planificado, inscripciones abiertas, en curso o finalizado). Se debe registrar la fecha de creación y de actualización.

**Matrículas:** Registro de la matrícula de cada estudiante en un periodo. Se requiere almacenar: el estudiante, el periodo académico, el programa en el que se matricula, el estado (activa, cancelada o finalizada), la fecha de matrícula y el semestre que cursa actualmente. Se debe registrar la fecha de creación y de actualización.

**Inscripciones:** Cada asignatura en la que un estudiante se inscribe dentro de una matrícula. Se requiere almacenar: la matrícula a la que pertenece, la asignatura, la franja horaria asignada, el estado (inscrita, cancelada, aprobada o reprobada), la fecha de inscripción, quién canceló la inscripción (si aplica) y el motivo de la cancelación.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y cambiar el estado de los periodos académicos.
- El sistema debe permitir crear, consultar y actualizar matrículas de estudiantes.
- El sistema debe permitir inscribir a un estudiante en una asignatura y cancelar la inscripción.
- Antes de inscribir a un estudiante, el sistema debe validar que el periodo se encuentre en estado "inscripciones abiertas" y que la fecha actual esté dentro del rango de fechas de inscripción.
- Antes de inscribir, el sistema debe consultar al servicio de programas para verificar que el estudiante haya aprobado todos los prerrequisitos obligatorios de la asignatura.
- Antes de inscribir, el sistema debe consultar al servicio de horarios para verificar que no existan cruces de horario con las asignaturas ya inscritas por el estudiante.
- El sistema debe controlar que no se exceda el cupo máximo de estudiantes por asignatura y grupo.
- El sistema debe permitir consultar los estudiantes inscritos en una asignatura específica.
- El sistema debe ofrecer una funcionalidad de validación previa que permita verificar si un estudiante puede inscribir una asignatura sin realizar la inscripción efectiva.

##### Dependencias con otros servicios

- Debe consultar al servicio de programas para validar prerrequisitos y obtener datos de las asignaturas.
- Debe consultar al servicio de horarios para verificar disponibilidad y detectar cruces de horario.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.15 ms-calificaciones [CAL]

**Propósito:** Gestiona las notas de los estudiantes, los cortes evaluativos y los promedios académicos. Calcula notas definitivas ponderadas por cortes, mantiene el promedio acumulado del estudiante y genera alertas cuando el rendimiento cae por debajo del umbral aceptable.

##### Información que gestiona

**Cortes evaluativos:** Definición de los periodos de evaluación dentro de una asignatura. Se requiere almacenar: la asignatura, el periodo académico, el nombre del corte (ejemplo: Primer Corte, Segundo Corte), el porcentaje que representa del total, el número de corte, la fecha de inicio y la fecha de fin. Se debe registrar la fecha de creación.

**Notas:** Cada calificación registrada. Se requiere almacenar: la inscripción del estudiante en la asignatura, el corte evaluativo, el valor de la nota (entre 0.0 y 5.0), observaciones, quién registró la nota, la fecha de registro y la fecha de la última actualización.

**Promedios de estudiante:** Cálculo de promedios por periodo y acumulado. Se requiere almacenar: el estudiante, el periodo académico, el promedio del periodo, el promedio acumulado, los créditos aprobados, los créditos cursados y la fecha del cálculo.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar y actualizar cortes evaluativos para cada asignatura y periodo. Debe validar que la suma de los porcentajes de todos los cortes de una asignatura sea exactamente 100%.
- El sistema debe permitir registrar y actualizar notas. Solo se aceptan valores entre 0.0 y 5.0 con un decimal de precisión.
- El sistema debe permitir consultar las notas de un estudiante en una asignatura específica y todas las notas de un corte evaluativo.
- El sistema debe calcular la nota definitiva de un estudiante en una asignatura como la suma ponderada de la nota de cada corte multiplicada por su porcentaje.
- Si la nota definitiva es igual o superior a 3.0, la asignatura se considera aprobada. En caso contrario, se considera reprobada. El estado de la inscripción debe actualizarse correspondientemente.
- El sistema debe calcular el promedio del periodo como la suma de cada nota definitiva multiplicada por los créditos de la asignatura, dividida entre el total de créditos cursados en el periodo.
- El sistema debe mantener el promedio acumulado del estudiante considerando todos los periodos cursados.
- Cuando el promedio de un estudiante caiga por debajo de 3.0, el sistema debe enviar una alerta automática a través del servicio de notificaciones.
- El sistema debe permitir listar los estudiantes con rendimiento bajo un umbral configurable.

##### Dependencias con otros servicios

- Debe consultar al servicio de matrículas para obtener las inscripciones del estudiante y calcular notas y promedios.
- Debe enviar alertas a través del servicio de notificaciones para bajo rendimiento y publicación de notas.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.16 ms-horarios [HOR]

**Propósito:** Gestiona la programación de horarios académicos: franjas horarias, asignaciones de docentes a aulas y la organización de horarios por periodo. Detecta cruces de horario en el momento de la creación y rechaza la operación si existe conflicto.

##### Información que gestiona

**Franjas horarias:** Cada bloque de tiempo asignado a una asignatura. Se requiere almacenar: la asignatura, el docente asignado, el espacio (aula), el periodo académico, el día de la semana (lunes a sábado), la hora de inicio, la hora de fin, el grupo y el estado (activa, cancelada o suspendida). Se debe registrar la fecha de creación y de actualización.

**Asignaciones de docente:** Relación entre docentes y las asignaturas que imparten. Se requiere almacenar: el docente, la asignatura, el periodo académico, el grupo, las horas semanales y el estado. Se debe registrar la fecha de creación y de actualización.

##### Requisitos funcionales

- El sistema debe permitir crear, consultar, actualizar y cancelar franjas horarias.
- Al crear o actualizar una franja horaria, el sistema debe verificar que no existan cruces de horario. Se consideran tres tipos de cruce: que el docente ya tenga una franja asignada en el mismo día y hora, que el aula ya esté ocupada en el mismo día y hora, o que el mismo grupo de la misma asignatura ya tenga una franja en el mismo día y hora. Si se detecta cualquier cruce, la operación debe ser rechazada con un mensaje descriptivo del conflicto.
- El sistema debe permitir crear, consultar y actualizar asignaciones de docentes a asignaturas.
- El sistema debe permitir consultar el horario completo de un programa en un periodo determinado, consolidando todas las franjas horarias de sus asignaturas.
- El sistema debe permitir consultar el horario de un docente específico en un periodo.
- El sistema debe permitir consultar la ocupación de un espacio específico en un periodo, mostrando todas las franjas asignadas.
- El sistema debe permitir consultar las franjas libres de un docente, calculadas como la diferencia entre el horario total disponible y las franjas ya asignadas.

##### Dependencias con otros servicios

- Debe consultar al servicio de espacios para validar que el aula existe, está disponible y tiene capacidad suficiente.
- Debe consultar al servicio de programas para obtener las asignaturas del programa que se están programando.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

### Módulo 6: Transversales

---

#### 7.17 ms-notificaciones [NOT]

**Propósito:** Motor centralizado de notificaciones del sistema. Gestiona el envío de notificaciones a través de múltiples canales, utilizando plantillas dinámicas con variables reemplazables. Soporta prioridades, reintentos automáticos en caso de fallo y envío masivo. En el contexto de este proyecto, el envío de notificaciones se simula (se registra como enviado sin necesidad de un servidor de correo o SMS real).

##### Información que gestiona

**Notificaciones:** Cada notificación generada. Se requiere almacenar: el usuario destinatario, el canal de envío (correo electrónico, SMS, notificación push o interna), el asunto, el mensaje, la prioridad (urgente, normal o baja), el estado (pendiente, enviada, fallida o leída), el número de intentos realizados, el número máximo de intentos permitidos, la fecha de creación, la fecha de envío, la fecha de lectura y el identificador de rastreo de la petición que originó la notificación. Se debe registrar la fecha de creación y de actualización.

**Plantillas:** Plantillas reutilizables para la generación de notificaciones. Se requiere almacenar: un nombre único, el canal al que aplica, la plantilla del asunto (con variables), la plantilla del mensaje (con variables), las variables requeridas y el estado. Se debe registrar la fecha de creación y de actualización.

**Preferencias de usuario:** Configuración de preferencias de notificación por usuario. Se requiere almacenar: el usuario, el canal preferido, si las notificaciones están activas, la hora de inicio del horario de no molestar y la hora de fin del horario de no molestar.

**Historial de reintentos:** Registro de cada intento de envío. Se requiere almacenar: la notificación, el número de intento, la fecha y hora, el resultado (éxito o fallo) y el detalle del error si falló.

##### Requisitos funcionales

- El sistema debe permitir crear y enviar notificaciones directamente o utilizando una plantilla.
- Al utilizar una plantilla, el sistema debe reemplazar las variables dinámicas (ejemplo: `{{nombre}}`, `{{fecha}}`, `{{monto}}`) con los valores proporcionados.
- Si el envío de una notificación falla, el sistema debe reintentar automáticamente hasta alcanzar el número máximo de intentos, con un intervalo creciente entre intentos (backoff exponencial). Cada intento debe quedar registrado en el historial.
- Las notificaciones con prioridad urgente deben procesarse antes que las de prioridad normal o baja. Las notificaciones normales y bajas deben respetar el horario de no molestar configurado por el usuario.
- El sistema debe permitir enviar una misma notificación a múltiples usuarios de forma masiva.
- El sistema debe permitir marcar una notificación como leída y listar las notificaciones no leídas de un usuario.
- El sistema debe permitir crear, consultar, actualizar y desactivar plantillas de notificación.
- El sistema debe permitir consultar y actualizar las preferencias de notificación de cada usuario.

##### Dependencias con otros servicios

- Debe consultar al servicio de usuarios para obtener los datos de contacto y las preferencias del destinatario.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

#### 7.18 ms-auditoria [AUD]

**Propósito:** Servicio centralizado de auditoría y trazabilidad del sistema. Recibe los registros de log de todos los microservicios de forma asíncrona, los almacena en base de datos, permite la búsqueda por identificador de rastreo para reconstruir la traza completa de una petición a través de todos los servicios involucrados, y genera estadísticas de uso del sistema. Implementa rotación automática eliminando registros antiguos.

##### Información que gestiona

**Eventos de log:** Cada registro de operación enviado por cualquier microservicio. Se requiere almacenar: la fecha y hora, el identificador de rastreo de la petición, el nombre del microservicio origen, la funcionalidad ejecutada, el método utilizado, el código de respuesta, la duración en milisegundos, el identificador del usuario y un detalle descriptivo.

**Configuración de retención:** Parámetros de rotación de datos. Se requiere almacenar: la cantidad de días de retención (por defecto 30), el estado de la configuración, la fecha de la última rotación ejecutada y la cantidad de registros eliminados en la última rotación.

**Estadísticas por servicio:** Métricas calculadas del uso del sistema. Se requiere almacenar: el nombre del microservicio, el periodo de la estadística (diario, semanal o mensual), la fecha, el total de peticiones, el total de errores, el tiempo promedio de respuesta en milisegundos, la funcionalidad más utilizada y la fecha del cálculo.

##### Requisitos funcionales

- El sistema debe recibir registros de log en formato JSON de cualquier microservicio. La recepción debe ser asíncrona: el servicio debe confirmar la recepción inmediatamente y procesar el registro en segundo plano.
- El sistema debe permitir recibir múltiples registros de log en una sola petición para optimizar el rendimiento.
- El sistema debe permitir buscar registros por identificador de rastreo, retornando la traza completa de una petición a través de todos los microservicios que participaron en su procesamiento.
- El sistema debe permitir filtrar registros por microservicio de origen, por fecha y por combinación de criterios.
- El sistema debe implementar una rotación automática que elimine los registros con más antigüedad que la configurada en los días de retención (por defecto 30 días). Debe permitir también la ejecución manual de la rotación.
- El sistema debe calcular y almacenar estadísticas de uso por servicio y periodo: total de peticiones, total de errores, tiempo promedio de respuesta y funcionalidad más utilizada.
- El sistema debe permitir consultar las estadísticas generales del sistema y las estadísticas detalladas de un servicio específico.
- Dado el volumen de datos que maneja este servicio, todas las consultas deben soportar paginación obligatoria.

##### Dependencias con otros servicios

- Este servicio se audita a sí mismo: sus propias operaciones generan registros que se almacenan en su propia base de datos.

---

#### 7.19 ms-reportes [REP]

**Propósito:** Genera reportes consolidados consumiendo datos de múltiples microservicios del sistema. Soporta plantillas de reporte configurables, programación automática de generación y exportación en formatos CSV y JSON.

##### Información que gestiona

**Reportes:** Cada reporte generado. Se requiere almacenar: la plantilla utilizada, un nombre descriptivo, los parámetros con los que se generó (en formato JSON), el resultado almacenado en caché, el formato de salida (CSV o JSON), el estado (pendiente, generando, completado o error), quién lo solicitó, la fecha de solicitud, la fecha de generación y el tamaño del resultado en bytes. Se debe registrar la fecha de creación.

**Plantillas de reporte:** Definición de los tipos de reporte disponibles. Se requiere almacenar: un nombre único, una descripción, los microservicios de los cuales se obtienen datos, los parámetros requeridos para la generación, la configuración de las consultas a realizar (en formato JSON) y el estado. Se debe registrar la fecha de creación y de actualización.

**Programaciones:** Configuración para la generación automática de reportes. Se requiere almacenar: la plantilla del reporte, la periodicidad (diario, semanal o mensual), el día de ejecución, la hora de ejecución, los destinatarios que deben recibir el reporte, el estado (activa o pausada), la fecha de la última ejecución y la fecha de la próxima ejecución. Se debe registrar la fecha de creación y de actualización.

##### Requisitos funcionales

- El sistema debe permitir solicitar la generación de un reporte proporcionando una plantilla y los parámetros requeridos.
- El sistema debe consumir datos de los microservicios definidos en la plantilla, consolidarlos y generar el reporte.
- El sistema debe almacenar el resultado generado como caché para evitar recalcular el mismo reporte si se solicita nuevamente con los mismos parámetros.
- El sistema debe permitir descargar un reporte generado en formato CSV o JSON.
- El sistema debe permitir crear, consultar, actualizar y eliminar plantillas de reporte.
- El sistema debe permitir configurar la generación automática de reportes según una periodicidad definida (diaria, semanal o mensual). Los reportes programados deben ejecutarse automáticamente en la fecha y hora configuradas.
- El sistema debe permitir ejecutar manualmente los reportes programados que estén pendientes.
- El sistema debe permitir listar, crear, actualizar y desactivar programaciones de reportes.

##### Dependencias con otros servicios

- Debe consultar al servicio de calificaciones para generar reportes de rendimiento académico y promedios por programa.
- Debe consultar al servicio de inventario para generar reportes de estado de activos, depreciación y stock bajo.
- Debe consultar al servicio de presupuesto para generar reportes de ejecución presupuestal por área y periodo.
- Debe enviar registros de log al servicio de auditoría de forma asíncrona con cada operación realizada.

---

## 8. Mapa de Dependencias entre Microservicios

La siguiente tabla muestra, para cada microservicio, qué otros servicios consumen directamente (sin contar las dependencias transversales de autenticación, roles y auditoría que aplican a todos).

| Microservicio | Consume datos de |
|---|---|
| ms-autenticacion | ms-usuarios, ms-roles |
| ms-usuarios | ms-roles, ms-notificaciones |
| ms-roles | ms-autenticacion (confianza mutua) |
| ms-inventario | ms-proveedores, ms-notificaciones |
| ms-espacios | ms-inventario, ms-notificaciones |
| ms-reservas | ms-espacios, ms-horarios |
| ms-presupuesto | ms-gastos, ms-notificaciones |
| ms-gastos | ms-presupuesto, ms-proveedores |
| ms-facturacion | ms-matriculas, ms-notificaciones |
| ms-pedidos | ms-inventario, ms-proveedores |
| ms-domicilios | ms-pedidos, ms-notificaciones |
| ms-proveedores | ms-notificaciones |
| ms-programas | ms-usuarios, ms-horarios |
| ms-matriculas | ms-programas, ms-horarios |
| ms-calificaciones | ms-matriculas, ms-notificaciones |
| ms-horarios | ms-espacios, ms-programas |
| ms-notificaciones | ms-usuarios |
| ms-auditoria | (se audita a sí mismo) |
| ms-reportes | ms-calificaciones, ms-inventario, ms-presupuesto |

Adicionalmente, todos los microservicios (excepto ms-autenticacion y ms-roles entre sí) consumen:

- **ms-autenticacion** para validar sesiones activas.
- **ms-roles** para validar permisos por funcionalidad.
- **ms-auditoria** para enviar registros de log de forma asíncrona.

---

## 9. Glosario

| Término | Definición |
|---|---|
| **Microservicio** | Componente de software independiente que implementa un conjunto de funcionalidades de un dominio específico, opera con su propia base de datos y se comunica con otros componentes mediante interfaces REST |
| **REST** | Estilo de arquitectura para la comunicación entre sistemas basado en el protocolo HTTP, utilizando operaciones estándar (GET, POST, PUT, DELETE) y formato JSON para el intercambio de datos |
| **JWT** | JSON Web Token. Estándar para la creación de tokens de acceso que contienen información del usuario de forma cifrada y verificable |
| **AES-256** | Algoritmo de cifrado simétrico de 256 bits utilizado para proteger datos sensibles como tokens de aplicación |
| **bcrypt** | Algoritmo de hash diseñado específicamente para el almacenamiento seguro de contraseñas |
| **Request ID** | Identificador único de rastreo que se asigna a cada petición y se propaga por todos los servicios que intervienen en su procesamiento, permitiendo la trazabilidad distribuida |
| **Token de aplicación** | Credencial fija asignada a cada microservicio que lo identifica ante los demás servicios del sistema |
| **Soft delete** | Técnica de eliminación lógica en la que los registros no se borran físicamente de la base de datos, sino que se marcan con un estado inactivo |
| **Fire-and-forget** | Patrón de comunicación asíncrona en el que el emisor envía un mensaje y continúa su operación sin esperar confirmación del receptor |
| **Backoff exponencial** | Estrategia de reintentos en la que el intervalo entre intentos se incrementa exponencialmente (1s, 2s, 4s, 8s..) para evitar saturar el servicio destino |
| **ERP** | Enterprise Resource Planning. Sistema de gestión integral que centraliza y automatiza los procesos de una organización |
| **Swagger UI** | Interfaz web generada automáticamente por FastAPI que permite visualizar y probar la documentación de una API REST |