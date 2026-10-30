# fonzeka-observatorio
Observatorio Inteligente del Sector Eléctrico Mexicano | fonzeka® Insights. Plataforma de análisis, seguimiento regulatorio y consulta de fuentes oficiales. 

## Bandeja histórica del 29 de octubre de 2026

[Abrir bandeja histórica](monitor-dof/historico/2026-10-29/bandeja.html).
Contiene los 20 enlaces de la bandeja original y destaca el Acuerdo SENER
5802463, único candidato por palabras clave. La clasificación es preliminar,
sin aprobación editorial ni certificación de vigencia jurídica.

Se recuperaron los siete archivos de la carpeta local `dof-consulta-29`.
Se conservan sin cambios en `monitor-dof/historico/2026-10-29/originales/`.
`procedencia.json` registra las huellas individuales y separa la consulta original
(29 de octubre) de la integración posterior. El estado original coincide con el
historial del repositorio. La API de GitHub confirmó la ejecución #29 como
`schedule` y el artefacto 12928365248. Sin el ZIP original no se ha verificado
la huella del paquete declarado por GitHub; las huellas locales no sustituyen esa
verificación ni acreditan el contenido jurídico de los documentos enlazados.

Para regenerar la presentación: `python3 scripts/generar_historica.py`.
No ejecuta el monitor ni modifica sus originales, el historial, las portadas,
los workflows o la bandeja vigente. La ruta histórica queda separada de la
publicación automática ordinaria.

## Bandeja integrada manualmente · 30 de octubre de 2026

La primera entrega en `monitor-dof/bandeja.html` incorpora 19 documentos únicos:
15 de la edición matutina y 4 de la vespertina. Identifica la integración manual,
la fecha consultada, la hora de verificación y la procedencia por documento.
No representa una ejecución programada ni certificación de vigencia jurídica.

Los índices archivados y sus huellas están en
`data/integraciones_dof/2026-10-30/`. La copia histórica está en
`monitor-dof/historico/2026-10-30/`; conserva esta entrega cuando la publicación
ordinaria posterior reemplace la bandeja vigente.

No se modifican portadas, historial técnico, generadores existentes ni workflows.
Esta publicación manual se revisa mediante PR y no cambia el bloqueo de publicación
del monitor para ejecuciones manuales. El validador ordinario rechaza el estado
`INTEGRACION_MANUAL_DE_EDICIONES`, como corresponde. La integración distingue dos
ediciones porque el índice sin parámetro devolvió la vespertina; no garantiza que
la publicación automática actual reúna todas las ediciones de un día.
