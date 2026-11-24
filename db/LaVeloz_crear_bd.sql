/* =====================================================================
   Currier La Veloz SRL - Sistema de gestión de encomiendas
   Script de creación de la base de datos (Microsoft SQL Server)
   SIS-303 · Proyecto final Scrum + XP · Fase de Planificación (2.5)
   ---------------------------------------------------------------------
   Contenido:
     1. Base de datos
     2. Tablas (11) con PK, FK, UNIQUE, CHECK y DEFAULT
     3. Índices para búsquedas y reportes
     4. Trigger que protege el historial de seguimiento (RNF-05)
     5. Datos iniciales de prueba
   Las referencias RN-xx / RNF-xx corresponden a la sección 1.3.
   ===================================================================== */

/* ---------- 1. Base de datos ---------- */
IF DB_ID(N'LaVelozDB') IS NULL
    CREATE DATABASE LaVelozDB;
GO
USE LaVelozDB;
GO

/* ---------- 2. Tablas ---------- */

CREATE TABLE Ciudad (
    id_ciudad      INT IDENTITY(1,1) CONSTRAINT PK_Ciudad PRIMARY KEY,
    nombre         NVARCHAR(60)  NOT NULL CONSTRAINT UQ_Ciudad_nombre UNIQUE,
    departamento   NVARCHAR(60)  NOT NULL
);

CREATE TABLE Sucursal (
    id_sucursal    INT IDENTITY(1,1) CONSTRAINT PK_Sucursal PRIMARY KEY,
    codigo         CHAR(3)       NOT NULL CONSTRAINT UQ_Sucursal_codigo UNIQUE,   -- prefijo del código de guía (RN-08)
    nombre         NVARCHAR(80)  NOT NULL,
    direccion      NVARCHAR(150) NOT NULL,
    telefono       VARCHAR(20)   NULL,
    activa         BIT           NOT NULL CONSTRAINT DF_Sucursal_activa DEFAULT 1,
    id_ciudad      INT           NOT NULL CONSTRAINT FK_Sucursal_Ciudad REFERENCES Ciudad(id_ciudad)
);

CREATE TABLE Empleado (
    id_empleado     INT IDENTITY(1,1) CONSTRAINT PK_Empleado PRIMARY KEY,
    ci              VARCHAR(15)   NOT NULL CONSTRAINT UQ_Empleado_ci UNIQUE,
    nombre_completo NVARCHAR(120) NOT NULL,
    usuario         VARCHAR(30)   NOT NULL CONSTRAINT UQ_Empleado_usuario UNIQUE,
    contrasena_hash VARCHAR(100)  NOT NULL,                                    -- hash bcrypt (RNF-02)
    rol             VARCHAR(15)   NOT NULL
                    CONSTRAINT CK_Empleado_rol CHECK (rol IN ('RECEPCIONISTA', 'CAJERA', 'DESPACHANTE', 'ADMINISTRADOR')),
    activo          BIT           NOT NULL CONSTRAINT DF_Empleado_activo DEFAULT 1,
    id_sucursal     INT           NOT NULL CONSTRAINT FK_Empleado_Sucursal REFERENCES Sucursal(id_sucursal)
);

CREATE TABLE Cliente (
    id_cliente     INT IDENTITY(1,1) CONSTRAINT PK_Cliente PRIMARY KEY,
    ci             VARCHAR(15)   NOT NULL CONSTRAINT UQ_Cliente_ci UNIQUE,       -- RN-13
    nombres        NVARCHAR(60)  NOT NULL,
    apellidos      NVARCHAR(60)  NOT NULL,
    telefono       VARCHAR(20)   NOT NULL,
    email          VARCHAR(100)  NULL
);

CREATE TABLE TipoEncomienda (
    id_tipo        INT IDENTITY(1,1) CONSTRAINT PK_TipoEncomienda PRIMARY KEY,
    nombre         NVARCHAR(40)  NOT NULL CONSTRAINT UQ_TipoEncomienda_nombre UNIQUE,
    descripcion    NVARCHAR(150) NULL,
    activo         BIT           NOT NULL CONSTRAINT DF_TipoEncomienda_activo DEFAULT 1
);

CREATE TABLE Tarifa (
    id_tarifa          INT IDENTITY(1,1) CONSTRAINT PK_Tarifa PRIMARY KEY,
    id_ciudad_origen   INT           NOT NULL CONSTRAINT FK_Tarifa_CiudadOrigen  REFERENCES Ciudad(id_ciudad),
    id_ciudad_destino  INT           NOT NULL CONSTRAINT FK_Tarifa_CiudadDestino REFERENCES Ciudad(id_ciudad),
    id_tipo            INT           NOT NULL CONSTRAINT FK_Tarifa_Tipo          REFERENCES TipoEncomienda(id_tipo),
    forma_envio        VARCHAR(10)   NOT NULL
                       CONSTRAINT CK_Tarifa_forma CHECK (forma_envio IN ('TERRESTRE', 'AEREO')),
    precio_por_kilo    DECIMAL(10,2) NOT NULL CONSTRAINT CK_Tarifa_precio CHECK (precio_por_kilo > 0),
    umbral_volumen_m3  DECIMAL(6,3)  NOT NULL CONSTRAINT DF_Tarifa_umbral DEFAULT 0.050,   -- RN-05
    recargo_volumen    DECIMAL(10,2) NOT NULL CONSTRAINT DF_Tarifa_recargo DEFAULT 0
                       CONSTRAINT CK_Tarifa_recargo CHECK (recargo_volumen >= 0),           -- terrestre: lo fija el administrador
    vigente_desde      DATE          NOT NULL CONSTRAINT DF_Tarifa_vigente DEFAULT CAST(GETDATE() AS DATE),
    activa             BIT           NOT NULL CONSTRAINT DF_Tarifa_activa DEFAULT 1,
    CONSTRAINT CK_Tarifa_trayecto CHECK (id_ciudad_origen <> id_ciudad_destino)
);

CREATE TABLE ProductoProhibido (
    id_producto     INT IDENTITY(1,1) CONSTRAINT PK_ProductoProhibido PRIMARY KEY,
    nombre          NVARCHAR(80)  NOT NULL CONSTRAINT UQ_ProductoProhibido_nombre UNIQUE,
    palabras_clave  NVARCHAR(300) NOT NULL,                                     -- separadas por coma (RN-02)
    base_legal      NVARCHAR(150) NULL,
    activo          BIT           NOT NULL CONSTRAINT DF_ProductoProhibido_activo DEFAULT 1
);

CREATE TABLE Encomienda (
    id_encomienda            INT IDENTITY(1,1) CONSTRAINT PK_Encomienda PRIMARY KEY,
    codigo_guia              VARCHAR(20)   NOT NULL CONSTRAINT UQ_Encomienda_codigo UNIQUE,      -- RN-08
    id_remitente             INT           NOT NULL CONSTRAINT FK_Encomienda_Remitente     REFERENCES Cliente(id_cliente),
    id_destinatario          INT           NOT NULL CONSTRAINT FK_Encomienda_Destinatario  REFERENCES Cliente(id_cliente),
    id_tipo                  INT           NOT NULL CONSTRAINT FK_Encomienda_Tipo          REFERENCES TipoEncomienda(id_tipo),
    id_tarifa                INT           NOT NULL CONSTRAINT FK_Encomienda_Tarifa        REFERENCES Tarifa(id_tarifa),
    id_sucursal_origen       INT           NOT NULL CONSTRAINT FK_Encomienda_SucOrigen     REFERENCES Sucursal(id_sucursal),
    id_sucursal_destino      INT           NOT NULL CONSTRAINT FK_Encomienda_SucDestino    REFERENCES Sucursal(id_sucursal),
    id_recepcionista         INT           NOT NULL CONSTRAINT FK_Encomienda_Recepcionista REFERENCES Empleado(id_empleado),
    descripcion_contenido    NVARCHAR(300) NOT NULL,
    peso_kg                  DECIMAL(8,2)  NOT NULL CONSTRAINT CK_Encomienda_peso    CHECK (peso_kg > 0),
    volumen_m3               DECIMAL(6,3)  NOT NULL CONSTRAINT CK_Encomienda_volumen CHECK (volumen_m3 >= 0),
    kilos_cobrados           INT           NOT NULL CONSTRAINT CK_Encomienda_kilos   CHECK (kilos_cobrados >= 1),  -- RN-04
    precio_por_kilo_aplicado DECIMAL(10,2) NOT NULL,                                                         -- RN-06
    recargo_volumen          DECIMAL(10,2) NOT NULL CONSTRAINT DF_Encomienda_recargo DEFAULT 0
                             CONSTRAINT CK_Encomienda_recargo CHECK (recargo_volumen >= 0),
    monto_total              DECIMAL(10,2) NOT NULL,
    declara_no_prohibido     BIT           NOT NULL,
    fecha_hora_recepcion     DATETIME2(0)  NOT NULL CONSTRAINT DF_Encomienda_recepcion DEFAULT SYSDATETIME(),
    fecha_hora_salida        DATETIME2(0)  NULL,
    fecha_hora_llegada       DATETIME2(0)  NULL,
    estado                   VARCHAR(12)   NOT NULL CONSTRAINT DF_Encomienda_estado DEFAULT 'REGISTRADA'
                             CONSTRAINT CK_Encomienda_estado
                             CHECK (estado IN ('REGISTRADA', 'PAGADA', 'EN_TRANSITO', 'EN_DESTINO', 'ENTREGADA', 'ANULADA')),
    CONSTRAINT CK_Encomienda_sucursales  CHECK (id_sucursal_origen <> id_sucursal_destino),
    CONSTRAINT CK_Encomienda_declaracion CHECK (declara_no_prohibido = 1),                                  -- RN-02
    CONSTRAINT CK_Encomienda_monto       CHECK (monto_total = kilos_cobrados * precio_por_kilo_aplicado + recargo_volumen), -- RN-03
    CONSTRAINT CK_Encomienda_fechas      CHECK (fecha_hora_llegada IS NULL
                                                OR (fecha_hora_salida IS NOT NULL AND fecha_hora_llegada >= fecha_hora_salida))
);

CREATE TABLE Pago (
    id_pago          INT IDENTITY(1,1) CONSTRAINT PK_Pago PRIMARY KEY,
    id_encomienda    INT           NOT NULL,
    id_cajera        INT           NOT NULL CONSTRAINT FK_Pago_Cajera REFERENCES Empleado(id_empleado),
    nro_comprobante  VARCHAR(20)   NOT NULL CONSTRAINT UQ_Pago_comprobante UNIQUE,
    fecha_hora       DATETIME2(0)  NOT NULL CONSTRAINT DF_Pago_fecha DEFAULT SYSDATETIME(),
    monto            DECIMAL(10,2) NOT NULL CONSTRAINT CK_Pago_monto CHECK (monto > 0),
    metodo           VARCHAR(10)   NOT NULL CONSTRAINT CK_Pago_metodo CHECK (metodo IN ('EFECTIVO', 'TARJETA', 'QR')),
    CONSTRAINT UQ_Pago_encomienda UNIQUE (id_encomienda),                                   -- un solo pago por encomienda (RN-07)
    CONSTRAINT FK_Pago_Encomienda FOREIGN KEY (id_encomienda) REFERENCES Encomienda(id_encomienda)
);

CREATE TABLE Entrega (
    id_entrega          INT IDENTITY(1,1) CONSTRAINT PK_Entrega PRIMARY KEY,
    id_encomienda       INT           NOT NULL,
    id_despachante      INT           NOT NULL CONSTRAINT FK_Entrega_Despachante REFERENCES Empleado(id_empleado),
    fecha_hora_entrega  DATETIME2(0)  NOT NULL CONSTRAINT DF_Entrega_fecha DEFAULT SYSDATETIME(),
    ci_presentado       VARCHAR(15)   NOT NULL,
    nombre_quien_recoge NVARCHAR(120) NOT NULL,
    observacion         NVARCHAR(300) NULL,
    CONSTRAINT UQ_Entrega_encomienda UNIQUE (id_encomienda),                                -- se entrega una sola vez (RN-10)
    CONSTRAINT FK_Entrega_Encomienda FOREIGN KEY (id_encomienda) REFERENCES Encomienda(id_encomienda)
);

CREATE TABLE Seguimiento (
    id_seguimiento   INT IDENTITY(1,1) CONSTRAINT PK_Seguimiento PRIMARY KEY,
    id_encomienda    INT           NOT NULL CONSTRAINT FK_Seguimiento_Encomienda REFERENCES Encomienda(id_encomienda),
    id_empleado      INT           NOT NULL CONSTRAINT FK_Seguimiento_Empleado   REFERENCES Empleado(id_empleado),
    estado_anterior  VARCHAR(12)   NULL,
    estado_nuevo     VARCHAR(12)   NOT NULL
                     CONSTRAINT CK_Seguimiento_estado
                     CHECK (estado_nuevo IN ('REGISTRADA', 'PAGADA', 'EN_TRANSITO', 'EN_DESTINO', 'ENTREGADA', 'ANULADA')),
    fecha_hora       DATETIME2(0)  NOT NULL CONSTRAINT DF_Seguimiento_fecha DEFAULT SYSDATETIME(),       -- RN-12
    observacion      NVARCHAR(300) NULL
);
GO

/* ---------- 3. Índices ---------- */

-- Solo una tarifa vigente por trayecto, tipo y forma de envío (RN-14)
CREATE UNIQUE INDEX UX_Tarifa_vigente
    ON Tarifa (id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio)
    WHERE activa = 1;

CREATE INDEX IX_Encomienda_estado         ON Encomienda (estado, id_sucursal_destino);
CREATE INDEX IX_Encomienda_recepcionista  ON Encomienda (id_recepcionista, fecha_hora_recepcion);  -- reporte HU-21
CREATE INDEX IX_Entrega_despachante       ON Entrega (id_despachante, fecha_hora_entrega);          -- reporte HU-22
CREATE INDEX IX_Seguimiento_encomienda    ON Seguimiento (id_encomienda, fecha_hora);               -- historial HU-20
GO

/* ---------- 4. Protección del historial (RNF-05) ---------- */
CREATE TRIGGER TR_Seguimiento_NoModificar
ON Seguimiento
AFTER UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    THROW 50001, N'El historial de seguimiento no se puede modificar ni borrar (RNF-05).', 1;
END;
GO

/* ---------- 5. Datos iniciales de prueba ----------
   Los precios terrestres Santa Cruz -> La Paz salen de la ficha del caso.
   Los demás valores son datos de prueba y los ajusta el administrador (HU-05). */

INSERT INTO Ciudad (nombre, departamento) VALUES
    (N'Santa Cruz de la Sierra', N'Santa Cruz'),
    (N'La Paz',                  N'La Paz'),
    (N'Cochabamba',              N'Cochabamba');

INSERT INTO Sucursal (codigo, nombre, direccion, telefono, id_ciudad) VALUES
    ('SCZ', N'Sucursal Santa Cruz', N'Dirección de prueba 1', NULL, 1),
    ('LPZ', N'Sucursal La Paz',     N'Dirección de prueba 2', NULL, 2),
    ('CBA', N'Sucursal Cochabamba', N'Dirección de prueba 3', NULL, 3);

INSERT INTO TipoEncomienda (nombre, descripcion) VALUES
    (N'Sobres-Documentos', N'Sobres y documentos'),
    (N'Alimentos',         N'Alimentos empacados'),
    (N'Otros',             N'Cajas y paquetes en general');

-- contrasena_hash: reemplazar por un hash bcrypt real generado por la aplicación
INSERT INTO Empleado (ci, nombre_completo, usuario, contrasena_hash, rol, id_sucursal) VALUES
    ('1000001', N'Recepcionista de prueba SCZ', 'recepcion.scz', 'PENDIENTE_HASH', 'RECEPCIONISTA', 1),
    ('1000002', N'Cajera de prueba SCZ',        'caja.scz',      'PENDIENTE_HASH', 'CAJERA',        1),
    ('1000003', N'Despachante de prueba SCZ',   'despacho.scz',  'PENDIENTE_HASH', 'DESPACHANTE',   1),
    ('1000004', N'Despachante de prueba LPZ',   'despacho.lpz',  'PENDIENTE_HASH', 'DESPACHANTE',   2),
    ('1000005', N'Administrador',               'admin',         'PENDIENTE_HASH', 'ADMINISTRADOR', 1);

-- Santa Cruz (1) -> La Paz (2). Tipos: 1 Sobres-Documentos, 2 Alimentos, 3 Otros
INSERT INTO Tarifa (id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio, precio_por_kilo, umbral_volumen_m3, recargo_volumen) VALUES
    (1, 2, 1, 'TERRESTRE', 50.00, 0.050, 10.00),   -- ficha del caso
    (1, 2, 2, 'TERRESTRE',  2.00, 0.050, 10.00),   -- ficha del caso
    (1, 2, 3, 'TERRESTRE',  3.00, 0.050, 10.00),   -- ficha del caso
    (1, 2, 1, 'AEREO',     70.00, 0.050,  0.00),   -- prueba; en aéreo el recargo lo asigna el recepcionista (RN-05)
    (1, 2, 2, 'AEREO',      5.00, 0.050,  0.00),   -- prueba
    (1, 2, 3, 'AEREO',      6.00, 0.050,  0.00);   -- prueba

-- Catálogo de ejemplo: validar contra la normativa boliviana vigente antes de usar en producción
INSERT INTO ProductoProhibido (nombre, palabras_clave, base_legal) VALUES
    (N'Sustancias controladas',            N'droga,cocaina,marihuana,estupefaciente', NULL),
    (N'Armas, municiones y explosivos',    N'arma,pistola,municion,bala,explosivo,dinamita', NULL),
    (N'Materiales inflamables',            N'gasolina,diesel,combustible,polvora,inflamable', NULL);
GO
