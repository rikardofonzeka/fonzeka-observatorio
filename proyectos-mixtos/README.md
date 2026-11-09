# Proyectos Mixtos CFE — Exportación para GitHub Pages

Exportación completa de la aplicación «Proyectos Mixtos CFE», sin claves privadas ni credenciales.

## Contenido
- `index.html` — página completa exportada, autocontenida. El CSS y el JavaScript de la aplicación están incluidos dentro de este archivo (no hay archivos CSS/JS externos en la versión original), por lo que funciona tal cual en GitHub Pages.
- `data/proyectos.json` — los 37 proyectos adjudicados el 5 de junio de 2026, con todos los campos de la tabla: numero, proyecto, desarrollador, zona, tecnologia, mw_generacion, almacenamiento, ubicacion, inversion_estimada, cim, ppa, entrada_en_operacion_prevista. ND = no disponible públicamente.
- `data/proyectos.csv` — misma tabla de 37 proyectos en CSV, mismos campos y valores.
- `data/plan-expansion-2026-2030.json` y `.csv` — los 4 proyectos del Plan de Expansión 2026-2030 (Termosolar I El Crucero, Termosolar II Comondú, Cogeneración Tula, Central Híbrida Oasis), aún sin adjudicar a 9 nov 2026.
- `data/fuentes.json` y `.csv` — referencias documentales con URL y nota.

No se modificó ni resumió la información: los valores ND se conservan tal cual.

## Publicar en GitHub Pages
1. Crea un repositorio nuevo en GitHub.
2. Sube todo el contenido de esta carpeta a la rama principal.
3. En Settings > Pages, elige Deploy from a branch, rama main, carpeta / (root).
4. Abre la URL que te dé GitHub Pages. La página es estática, no necesita servidor ni base de datos.

Nota: la verificación en la Plataforma Nacional de Transparencia no encontró registros titulados «proyecto mixto»; la lista proviene de las fuentes citadas en `data/fuentes.json`.
