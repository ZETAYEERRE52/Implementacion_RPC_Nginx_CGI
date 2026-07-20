# Implementación de RPC con Nginx y CGI

Este repositorio contiene la configuración y los scripts necesarios para desplegar un entorno de **Llamada a Procedimiento Remoto (RPC)** clásico utilizando `nginx` y `fcgiwrap`.

El proyecto se desarrolló como parte de las prácticas de **Ingeniería en Computación en ESIME-IPN**, con el objetivo de comprender el flujo de serialización, el paso de mensajes y el manejo del estado HTTP en arquitecturas cliente-servidor.

## 🛠️ Entorno y Requisitos

El despliegue fue probado en **Fedora 43**. Se requiere instalar los siguientes paquetes en el sistema (físico o virtualizado):

- `nginx` (servidor web y proxy inverso)  
- `fcgiwrap` (interfaz FastCGI para ejecutar scripts CGI)  
- `bc` (calculadora de precisión arbitraria para Bash)  
- `curl` y `jq` (herramientas de prueba para el cliente)  

## 📁 Estructura del Proyecto

```text
/
├── config/
│   └── rpc-cgi.conf       # Configuración de Nginx
├── scripts/
│   ├── saludo.cgi         # Endpoint básico de prueba RPC
│   └── calc.cgi           # Calculadora con idempotencia
└── README.md              # Este archivo
```

## ⚙️ Instalación y Configuración

**1. Despliegue de scripts**  
Los scripts deben alojarse en el directorio estándar configurado para el servidor web:

```bash
sudo mkdir -p /var/www/cgi-bin/rpc
sudo cp scripts/*.cgi /var/www/cgi-bin/rpc/
sudo chmod +x /var/www/cgi-bin/rpc/*.cgi
sudo chown -R nginx:nginx /var/www/cgi-bin/rpc
```

**2. Configuración de Nginx**  
Copiar el archivo de configuración y recargar el servicio:

```bash
sudo cp config/rpc-cgi.conf /etc/nginx/default.d/
sudo nginx -t && sudo systemctl reload nginx
```

**3. Ajustes de SELinux (crítico)**  
Para permitir que `fcgiwrap` procese las peticiones y escriba en `/var/tmp/`, se aplicaron las siguientes políticas:

```bash
# Permitir ejecución del socket FastCGI
sudo semodule -i nginx_fcgiwrap.pp

# Asignar contexto de lectura/escritura al directorio temporal
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/tmp(/.*)?"
sudo restorecon -Rv /var/tmp
```

## 🚀 Uso y Endpoints

El sistema expone dos procedimientos principales:

### 1. Procedimiento `saludo.cgi`
Recibe un parámetro `nombre` y devuelve un saludo. Soporta GET, POST y negociación de contenido (JSON o texto plano).

**Ejemplo JSON:**
```bash
curl -s -H 'Accept: application/json' 'http://localhost/rpc/saludo.cgi?nombre=ESIME' | jq .
```

### 2. Procedimiento `calc.cgi`
Servicio multioperación que permite realizar operaciones matemáticas básicas (`sum`, `res`, `mul`, `div`).

**Ejemplo de multiplicación:**
```bash
curl -s 'http://localhost/rpc/calc.cgi?op=mul&a=7&b=6'
```

**Esquema de idempotencia:**  
El endpoint `/rpc/calc.cgi` implementa almacenamiento temporal en `/var/tmp/` para evitar procesar la misma solicitud más de una vez en caso de reintentos. El cliente debe enviar la cabecera `Idempotency-Key`.

```bash
# Primera petición: procesa y guarda en caché
curl -s -i -H 'Idempotency-Key: req-12345' 'http://localhost/rpc/calc.cgi?op=sum&a=10&b=20'

# Subsecuentes con la misma clave: devuelven la respuesta almacenada
curl -s -i -H 'Idempotency-Key: req-12345' 'http://localhost/rpc/calc.cgi?op=sum&a=10&b=20'
```

---

Con esta versión tu **README.md** queda más claro, formal y alineado con un **reporte académico de laboratorio**. ¿Quieres que también te prepare una **sección de resultados esperados** (ejemplo de salida en JSON y texto plano) para complementar la práctica?
