# pgAdmin

pgAdmin es opcional y sirve para inspeccionar la base de datos durante el desarrollo. No es necesario para utilizar la aplicación.

## Iniciar pgAdmin con Docker Compose

Desde la raíz del proyecto:

```bash
docker compose --profile tools up -d pgadmin
```

Abre `http://localhost:5050` y usa las variables `PGADMIN_EMAIL` y `PGADMIN_PASSWORD` definidas en `.env`.

## Registrar PostgreSQL

Dentro de pgAdmin crea un servidor con estos valores:

| Campo | Valor |
|---|---|
| Name | `FashionVision` |
| Host name/address | `db` |
| Port | `5432` |
| Maintenance database | Valor de `POSTGRES_DB` |
| Username | Valor de `POSTGRES_USER` |
| Password | Valor de `POSTGRES_PASSWORD` |

El host es `db`, no `localhost`, porque pgAdmin y PostgreSQL se comunican dentro de la red Docker `pos-network`.

## Detener pgAdmin

```bash
docker compose --profile tools stop pgadmin
```

Para detener todos los servicios sin borrar datos:

```bash
docker compose down
```

## Seguridad

No expongas pgAdmin directamente a Internet. Usa una contraseña única y limita el acceso por red o mediante un proxy autenticado.
