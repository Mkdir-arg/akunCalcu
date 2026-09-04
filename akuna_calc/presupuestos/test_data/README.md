# PDF de muestra para el test de importación REHAU (REQ-049)

Copiá acá los PDF reales que genera el software de REHAU (por ejemplo
`presupuesto_hernan braberman.pdf`). El test `ParserRehauTest.test_pdfs_reales_de_la_carpeta`
recorre todos los `.pdf` de esta carpeta y verifica que se detecten ítems y que
unitario × unidades cierre con el total de cada uno.

Los `.pdf` de esta carpeta están en `.gitignore` porque traen nombre y teléfono de clientes
reales: quedan solo en la máquina de quien los copia.
