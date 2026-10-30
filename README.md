# fonzeka-observatorio

Sitio público del Observatorio Inteligente del Sector Eléctrico Mexicano | fonzeka® Insights.

## Separación editorial

Este repositorio se destina a contenidos autorizados para consulta pública.
Las detecciones, bandejas preliminares, evidencias y revisiones manuales se gestionan
en el espacio privado. No se publican automáticamente por haber pasado una validación técnica.
Una publicación requiere autorización editorial expresa con documento, versión,
responsable y fecha. Los scripts que permanezcan aquí son código de referencia,
no una autorización para publicar sus resultados.

Se retiraron de la versión actual las bandejas y datos de revisión del 29 y 30 de
octubre de 2026, conservados en el repositorio privado con manifiesto de huellas.
Se retiró el workflow de consulta del repositorio público; su continuidad se gestiona
en el privado sin pasos de publicación pública. No se reescribió el historial Git:
las versiones que ya fueron públicas siguen siendo recuperables en commits anteriores.

## Publicación desde la mesa privada

El receptor `publicar-aprobados.yml` consulta exclusivamente versiones aprobadas y
expresamente enviadas. Requiere el secreto Actions `FONZEKA_MESA_SERVICE_TOKEN` y
GitHub Pages configurado con origen GitHub Actions. Nunca incluye la bandeja ni el
historial privado en el artefacto público: `empaquetar_publico.py` usa una lista
explícita de archivos autorizados.

Las nuevas fichas usan la estructura de `expediente-001.html`: resumen, cambios,
antecedentes, transitorios, implicaciones y evidencia. La plantilla se conserva en
`scripts/publication-template.json`; su huella forma parte de cada aprobación.
El expediente CNE original no se modifica. Cada versión nueva tiene una ruta propia.
Los responsables de aprobación y motivos internos permanecen en la mesa privada.

La cola se incorpora con commit y despliegue explícito de Pages. Solo se confirma
PUBLICADO tras completar el despliegue. Las ejecuciones programadas vacías no
modifican contenido ni despliegan. Sin secreto, únicamente los eventos de push/manual
pueden desplegar la versión pública existente; no se obtiene material privado.
