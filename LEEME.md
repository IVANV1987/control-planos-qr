# ANTILLEAN — piloto de consulta QR con Excel maestro privado

## Estado
Paquete técnico para configurar. **No está conectado a OneDrive ni publicado**. El archivo original no se modifica ni se carga a GitHub.

## Adaptación a tu Excel real
- Se detectaron 26 hojas por proyecto.
- La mayoría tiene el encabezado `Codigo` en C y `Rev` en E (fila 5).
- `UASD-Azua` tiene `Codigo` en E y `Rev` en G.
- Hay hojas sin estructura típica o sin registros; el programa las reporta y las omite.
- Algunos códigos incorporan el sufijo de revisión: ANTES de imprimir QR, validar la regla de `codebase()` del programa.

## Paso A. Preparar SOLO los proyectos que se publicarán
1. Mantén el archivo en OneDrive/SharePoint.
2. En la fila de encabezados de cada hoja elegida agrega una columna titulada EXACTAMENTE `PUBLICAR_QR`.
3. Escribe `SI` en las filas cuya información puede publicarse libremente; deja otras vacías.
4. Revisa que `Rev` contenga la **última revisión autorizada** (no una versión en trabajo). **El script no puede comprobar aprobación automáticamente porque el archivo no tiene un campo uniforme de aprobación**.
5. El nombre del proyecto (nombre de la hoja) y el **código base sin revisión** no deben cambiar; son los elementos usados para generar el ID de QR.
6. No uses `SI` en documentos reservados, aun cuando solo aparezca el título.

## Paso B. Microsoft Entra / Graph (requiere administrador)
1. Registrar aplicación para acceso servidor a servidor.
2. Conceder permiso Graph `Sites.Selected` y acceso `read` explícito al sitio donde está el Excel (o una autorización de menor alcance compatible con la ubicación).
3. Crear un secreto de corta duración para el piloto. Guardarlo solo en GitHub Actions Secrets; considerar federación de identidad en producción.
4. Obtener Tenant ID, Client ID, Drive ID e Item ID. Nunca publicar esos datos junto con el secreto.

## Paso C. GitHub
1. Crear un repositorio público gratuito y cargar los archivos de este paquete (NO cargar el Excel).
2. Configurar Settings > Pages > Build and deployment: GitHub Actions.
3. Crear los secrets: `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_DRIVE_ID`, `MS_ITEM_ID`.
4. En Settings > Secrets and variables > Actions > Variables crear `PUBLIC_SITE_URL` con la URL definitiva de GitHub Pages (por ejemplo `https://usuario.github.io/control-planos-qr/`).
5. Ejecutar manualmente Actions > Publicar estado QR > Run workflow.
6. Revisar mensajes de error y abrir la página de consulta.
7. Para obtener direcciones por plano puedes ejecutar el script localmente (con credenciales bajo entorno seguro); produce `urls_qr.csv`. Nunca subas ese CSV si no deseas revelar la lista de documentos publicados.

## Paso D. Creación de QR
Generar QR a partir de cada `QR permanente URL` del CSV, e insertar la imagen en el cajetín DWG. Una vez generado, no cambiar ni el nombre del proyecto ni su código base. El QR no lleva la revisión, solo el ID fijo.

## Seguridad / límites
- El sitio y `planos.json` son **públicos**. Se expone todo registro marcado `SI`.
- El script se detiene si no hay documentos marcados o detecta códigos QR duplicados.
- Programación: aproximadamente cada 15 minutos; GitHub Actions puede sufrir retrasos u omisiones.
- La pantalla advierte si los datos llevan más de 60 minutos sin actualizarse.
- El campo `ESTADO` de esta versión solo indica `REGISTRADO`, NO "aprobado para construcción". Si lo deseas, debes añadir un campo uniforme de aprobación y lógica de publicación según ese campo.
- Si una fila cambia de código base o se mueve entre proyectos se generará OTRO ID: se debe establecer una columna `ID_QR` inmutable para evitarlo en implementaciones donde esto sea frecuente.
- GitHub Pages debe ser aprobado por TI si se publican datos de empresa.
