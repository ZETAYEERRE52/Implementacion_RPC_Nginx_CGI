#!/usr/bin/env bash
#
# calc.cgi — Servicio RPC para operaciones matemáticas básicas con idempotencia.
# Dependencias: bash, bc

set -euo pipefail

# 1) Configuración de Idempotencia
# Extraer la cabecera HTTP_IDEMPOTENCY_KEY (CGI convierte Idempotency-Key a esta variable)
IDEM_KEY="${HTTP_IDEMPOTENCY_KEY:-}"
CACHE_DIR="/var/tmp"

if [ -n "$IDEM_KEY" ]; then
    # Sanitizar la clave para prevenir inyección de rutas (Path Traversal)
    SAFE_KEY=$(echo "$IDEM_KEY" | tr -dc 'a-zA-Z0-9')
    CACHE_FILE="${CACHE_DIR}/rpc_calc_${SAFE_KEY}.http"

    # Si la petición ya fue procesada, devolver la respuesta almacenada
    if [ -f "$CACHE_FILE" ]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# 2) Parseo de Parámetros (Marshalling Inverso)
OP=$(echo "${QUERY_STRING:-}" | sed -n 's/.*op=\([^&]*\).*/\1/p')
A=$(echo "${QUERY_STRING:-}" | sed -n 's/.*a=\([^&]*\).*/\1/p')
B=$(echo "${QUERY_STRING:-}" | sed -n 's/.*b=\([^&]*\).*/\1/p')

# 3) Validación de Entradas
# Expresión regular para validar enteros y decimales, incluyendo negativos
RE='^-?[0-9]+(\.[0-9]+)?$'
if ! [[ "$A" =~ $RE ]] || ! [[ "$B" =~ $RE ]]; then
    printf 'Status: 400 Bad Request\r\n'
    printf 'Content-Type: application/json\r\n\r\n'
    printf '{"error": "Los operandos a y b deben ser valores numericos validos"}\n'
    exit 0
fi

# 4) Lógica Matemática (bc)
RESULTADO=""
case "$OP" in
    sum|suma)
        RESULTADO=$(echo "$A + $B" | bc -l)
        ;;
    res|resta)
        RESULTADO=$(echo "$A - $B" | bc -l)
        ;;
    mul|multiplicacion)
        RESULTADO=$(echo "$A * $B" | bc -l)
        ;;
    div|division)
        # Validación estricta de división por cero
        if (( $(echo "$B == 0" | bc -l) )); then
            printf 'Status: 400 Bad Request\r\n'
            printf 'Content-Type: application/json\r\n\r\n'
            printf '{"error": "Division por cero detectada"}\n'
            exit 0
        fi
        # Escalar a 4 decimales para mayor precisión
        RESULTADO=$(echo "scale=4; $A / $B" | bc -l)
        ;;
    *)
        printf 'Status: 400 Bad Request\r\n'
        printf 'Content-Type: application/json\r\n\r\n'
        printf '{"error": "Operacion no soportada. Use: sum, res, mul, div"}\n'
        exit 0
        ;;
esac

# Formatear números para evitar salida de bc tipo ".5" (convertir a "0.5")
RESULTADO=$(printf "%.4f" "$RESULTADO" | sed 's/0*$//;s/\.$//')

# 5) Construcción de la Respuesta
# Se utiliza una variable para poder guardar la estructura completa en la caché
HTTP_RESPONSE="Content-Type: application/json; charset=UTF-8\r\n\r\n"
HTTP_RESPONSE+="{\"operacion\":\"$OP\", \"a\":$A, \"b\":$B, \"resultado\":$RESULTADO}\n"

# 6) Almacenamiento de Estado (Idempotencia)
if [ -n "$IDEM_KEY" ]; then
    echo -e "$HTTP_RESPONSE" > "$CACHE_FILE"
fi

# 7) Emisión al Cliente
echo -e "$HTTP_RESPONSE"
