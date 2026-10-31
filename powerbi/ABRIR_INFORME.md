# Abrir Power BI con datos

El PBIP de la carpeta principal es una definición portátil: no incluye datos ni rutas de tu ordenador. Puede abrirse con todos los gráficos vacíos.

1. Cierra el informe vacío.
2. Desde la raíz del repositorio ejecuta `python -m tools.prepare_powerbi`.
3. Abre **powerbi/.local/BankingCustomerAnalytics.pbip**. Es la entrada local estable.
4. Selecciona **Inicio → Actualizar** y espera a que termine.
5. Guarda con **Ctrl+S**. Cierra y vuelve a abrir para comprobar que conserva los datos.

La preparación comprueba que los conjuntos Gold, sintético, ML y analítico sean compatibles y configura sus cuatro rutas. Ahora también reutiliza una caché local guardada cuando coinciden las rutas, las tablas y las medidas. Si no hay una caché compatible, Actualizar debe importar los datos. No mezcles archivos de distintas compilaciones.

En el caso revisado, la copia preparada no tenía cache.abf. Se restauró una copia local guardada de 3.672.881 bytes correspondiente a las mismas cuatro rutas, 35 tablas y 209 medidas. Esto corrige la ausencia de datos guardados; falta confirmar visualmente la apertura en Desktop. La herramienta de control de Windows falló antes de conectarse.

Si Actualizar muestra un error, copia su texto completo. Comprueba primero las rutas en **Transformar datos → Editar parámetros**: GoldDataPath, SyntheticGoldDataPath, MLGoldDataPath y AnalyticsGoldDataPath. Usa los valores preparados automáticamente; no sustituyas rutas al azar ni cambies los controles de seguridad para ocultar el error.

[Microsoft explica que un PBIP sin cache.abf abre el modelo sin datos](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset/). Restaurar la caché en disco requiere cerrar y abrir el proyecto; un informe ya abierto no la recarga automáticamente.
