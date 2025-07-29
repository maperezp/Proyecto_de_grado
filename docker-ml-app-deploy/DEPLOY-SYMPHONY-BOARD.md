# Despliegue en Symphony Board - Guía de Instalación

Esta guía describe el proceso completo para desplegar la aplicación de monitoreo PCH-Cloud en una Symphony Board usando Docker.

## 📋 Prerrequisitos

### Hardware Requerido
- Symphony Board (ARM64)
- Cable USB para conexión serial
- Cable Ethernet
- PC host para desarrollo

### Software Requerido
- Docker instalado en PC host
- Terminal serial (picocom)
- SSH client
- SCP para transferencia de archivos

## 🔧 Preparación Inicial

### 1. Conexión Serial
```bash
# Verificar dispositivos conectados
dmesg

# Conectar por puerto serial
picocom -b 115200 /dev/ttyUSB0
```

### 2. Preparación del Proyecto
```bash
# Navegar al directorio del proyecto
cd docker-ml-app-deploy
```

## 🚀 Proceso de Despliegue

### Paso 1: Construcción de la Imagen Docker

```bash
# Construir imagen para arquitectura ARM64
docker build -t ml-app:arm64 .

# Verificar que la imagen se creó correctamente
docker images
```

### Paso 2: Exportar Imagen para Transferencia

```bash
# Comprimir imagen en archivo tar
docker save -o proton-ml-app.tar ml-app:arm64
```

### Paso 3: Configuración de Red

#### En el PC Host:
```bash
# Habilitar interfaz de red
sudo ip link set enp2s0 up

# Asignar IP estática en subred /24 (máscara 255.255.255.0)
sudo ip addr add 192.168.7.1/24 dev enp2s0
```

#### En la Symphony Board:
```bash
# Habilitar interfaz Ethernet
ip link set eth0 up

# Asignar IP en la misma subred
ip addr add 192.168.7.2/24 dev eth0
```

### Paso 4: Establecer Conexión SSH

```bash
# Probar conectividad desde el PC
ping -c2 192.168.7.2

# Conectarse por SSH (si responde)
ssh root@192.168.7.2
```

### Paso 5: Transferir Imagen Docker

```bash
# Copiar imagen a la Symphony Board
scp proton-ml-app.tar root@192.168.7.2:/tmp/
```

### Paso 6: Cargar Imagen en la Board

```bash
# En la Symphony Board, cargar la imagen Docker
cd /tmp
docker load -i proton-ml-app.tar

# Verificar que se cargó correctamente
docker images
```

## 🏃‍♂️ Ejecución de la Aplicación

### Modo de Desarrollo (Interactivo)
```bash
# Ejecutar con acceso completo a la red del host
docker run --network=host --privileged -it ml-app:arm64
```

### Modo de Desarrollo con Volúmenes
```bash
# Ejecutar con directorio de código montado
docker run --network=host --privileged --name test-container \
  -v $(pwd)/src:/app \
  -p 8080:8080 \
  -it ml-app:arm64
```

### Modo de Producción
```bash
# Ejecutar en segundo plano con nombre específico
docker run -d \
  --name pch-monitoring \
  --network=host \
  --privileged \
  --restart=unless-stopped \
  ml-app:arm64
```

### Modo de Producción con Permisos Específicos (Recomendado)
```bash
# Ejecutar con capabilities específicas para WiFi
docker run -d \
  --name pch-monitoring \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --device=/dev/rfkill \
  -p 8080:8080 \
  --restart=unless-stopped \
  ml-app:arm64
```

## ✅ Verificación de la Instalación

### Verificar Estado del Contenedor
```bash
# Listar contenedores en ejecución
docker ps

# Ver logs de la aplicación
docker logs pch-monitoring

# Ver logs en tiempo real
docker logs -f pch-monitoring
```

### Probar Funcionalidades

#### Estado de la Aplicación
```bash
curl http://localhost:8080/api/status
```

#### Funcionalidad WiFi
```bash
# Verificar estado WiFi
curl http://localhost:8080/api/wifi/status

# Escanear redes disponibles
curl http://localhost:8080/api/wifi/scan
```

#### Dashboard Web
- Abrir navegador en: `http://192.168.7.2:8080`
- Verificar que se carga el dashboard principal
- Probar la página de configuración WiFi: `http://192.168.7.2:8080/wifi`

## 🔧 Gestión del Contenedor

### Comandos Básicos de Gestión

#### Detener la Aplicación
```bash
docker stop pch-monitoring
```

#### Reiniciar la Aplicación
```bash
docker restart pch-monitoring
```

#### Acceder al Contenedor
```bash
# Abrir shell interactiva en el contenedor
docker exec -it pch-monitoring bash

# Ejecutar comando específico
docker exec -it pch-monitoring ls -la /app
```

#### Eliminar Contenedor
```bash
# Detener y eliminar contenedor
docker stop pch-monitoring
docker rm pch-monitoring
```

#### Eliminar Imagen
```bash
# Eliminar imagen del sistema
docker rmi ml-app:arm64
```

### Monitoreo y Mantenimiento

#### Ver Recursos Utilizados
```bash
# Estadísticas en tiempo real
docker stats pch-monitoring

# Información detallada del contenedor
docker inspect pch-monitoring
```

#### Backup de Datos
```bash
# Backup de base de datos
docker cp pch-monitoring:/app/db/predictions.db ./backup_$(date +%Y%m%d).db

# Backup de logs
docker logs pch-monitoring > app_logs_$(date +%Y%m%d).log
```

## 🐛 Troubleshooting

### Problemas Comunes

#### Error de Conexión de Red
```bash
# Verificar configuración de red
ip addr show eth0

# Reiniciar interfaz de red
ip link set eth0 down
ip link set eth0 up
ip addr add 192.168.7.2/24 dev eth0
```

#### Error de Permisos WiFi
```bash
# Verificar que el contenedor tiene privilegios
docker inspect pch-monitoring | grep -i privileged

# Reiniciar con privilegios completos
docker stop pch-monitoring
docker rm pch-monitoring
docker run -d --name pch-monitoring --network=host --privileged ml-app:arm64
```

#### Error de Carga de Modelos
```bash
# Verificar que los modelos están presentes
docker exec -it pch-monitoring ls -la /app/models/

# Verificar logs de carga
docker logs pch-monitoring | grep -i model
```

#### Problemas de Performance
```bash
# Verificar uso de memoria y CPU
docker stats pch-monitoring

# Verificar espacio en disco
docker exec -it pch-monitoring df -h
```

## 📋 Checklist de Despliegue

- [ ] Symphony Board conectada y accesible
- [ ] Red configurada correctamente (192.168.7.x/24)
- [ ] Imagen Docker construida y transferida
- [ ] Contenedor ejecutándose correctamente
- [ ] API respondiendo en puerto 8080
- [ ] Dashboard web accesible
- [ ] Funcionalidad WiFi operativa
- [ ] Base de datos inicializada
- [ ] Modelos ML cargados correctamente

## 📞 Soporte

### Información de Contacto
- **Equipo**: Proctek Team
- **Documentación**: README.md principal
- **Logs**: `docker logs pch-monitoring`

### Comandos de Diagnóstico
```bash
# Estado general del sistema
docker ps -a
docker images
docker system df

# Información de red
ip addr show
ip route show

# Estado de la aplicación
curl -I http://localhost:8080/api/status
```

---

**Versión**: 1.0.0  
**Fecha**: Julio 2025  
**Target**: Symphony Board ARM64  
**Estado**: Documentación de Producción

