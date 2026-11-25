# fonzeka-observatorio

Sitio público del Observatorio Inteligente del Sector Eléctrico Mexicano | fonzeka® Insights.

## Catálogo público del DOF

Los expedientes se ofrecen en un catálogo único (publicaciones y análisis, monitor y página del Observatorio). El catálogo `publicaciones/dof/catalogo.json` utiliza el esquema 2 y comienza vacío; las fichas de pruebas anteriores se retiran de la publicación. La ruta estable de cada expediente es `publicaciones/dof/expediente.html?codigo=<código DOF>`. Cada ficha tendrá un archivo público `expediente-<código>.json`.

El contrato público excluye prompts, observaciones internas, aprobaciones, versiones y datos de la mesa privada. `scripts/publico_v2.py` valida el catálogo y la correspondencia con cada expediente. `scripts/empaquetar_publico.py` despliega solo los archivos explícitamente permitidos. No incluye bandejas, historial, manifiestos de aprobación antiguos ni expedientes de prueba.

## Separación editorial y transición

La mesa privada recibe y analiza las publicaciones. Detectar una publicación no equivale a autorizarla ni publicarla. El monitor de índices oficiales continúa sincronizándose con la mesa privada mediante el puente de servicio existente.

El receptor de fichas del esquema antiguo queda desactivado para evitar que se reincorporen análisis de prueba. La nueva salida no recibirá resultados de la mesa privada hasta que el mecanismo de autorización independiente y el puente del nuevo contrato estén implementados y probados. Los cambios en la lista pública se desplegarán por GitHub Pages a partir del catálogo autorizado.

Los scripts antiguos se conservan únicamente como referencia interna de migración y no se ejecutan en el despliegue de la nueva salida pública. El historial de Git no se reescribe.

No se modifica el portal institucional ni sus recursos ajenos al DOF. La antigua liga del expediente 001 redirige al catálogo.
