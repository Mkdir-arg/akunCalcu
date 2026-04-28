-- MySQL dump 10.13  Distrib 8.0.40, for Linux (x86_64)
--
-- Host: AKUN.mysql.pythonanywhere-services.com    Database: AKUN$default
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=117 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add cotizacion',7,'add_cotizacion'),(26,'Can change cotizacion',7,'change_cotizacion'),(27,'Can delete cotizacion',7,'delete_cotizacion'),(28,'Can view cotizacion',7,'view_cotizacion'),(29,'Can add producto',8,'add_producto'),(30,'Can change producto',8,'change_producto'),(31,'Can delete producto',8,'delete_producto'),(32,'Can view producto',8,'view_producto'),(33,'Can add cotizacion item',9,'add_cotizacionitem'),(34,'Can change cotizacion item',9,'change_cotizacionitem'),(35,'Can delete cotizacion item',9,'delete_cotizacionitem'),(36,'Can view cotizacion item',9,'view_cotizacionitem'),(37,'Can add Provincia',10,'add_provincia'),(38,'Can change Provincia',10,'change_provincia'),(39,'Can delete Provincia',10,'delete_provincia'),(40,'Can view Provincia',10,'view_provincia'),(41,'Can add Venta',11,'add_venta'),(42,'Can change Venta',11,'change_venta'),(43,'Can delete Venta',11,'delete_venta'),(44,'Can view Venta',11,'view_venta'),(45,'Can add Cliente',12,'add_cliente'),(46,'Can change Cliente',12,'change_cliente'),(47,'Can delete Cliente',12,'delete_cliente'),(48,'Can view Cliente',12,'view_cliente'),(49,'Can add Cuenta',13,'add_cuenta'),(50,'Can change Cuenta',13,'change_cuenta'),(51,'Can delete Cuenta',13,'delete_cuenta'),(52,'Can view Cuenta',13,'view_cuenta'),(53,'Can add Compra',14,'add_compra'),(54,'Can change Compra',14,'change_compra'),(55,'Can delete Compra',14,'delete_compra'),(56,'Can view Compra',14,'view_compra'),(57,'Can add Tipo de Cuenta',15,'add_tipocuenta'),(58,'Can change Tipo de Cuenta',15,'change_tipocuenta'),(59,'Can delete Tipo de Cuenta',15,'delete_tipocuenta'),(60,'Can view Tipo de Cuenta',15,'view_tipocuenta'),(61,'Can add Factura',16,'add_factura'),(62,'Can change Factura',16,'change_factura'),(63,'Can delete Factura',16,'delete_factura'),(64,'Can view Factura',16,'view_factura'),(65,'Can add Punto de Venta',17,'add_puntoventa'),(66,'Can change Punto de Venta',17,'change_puntoventa'),(67,'Can delete Punto de Venta',17,'delete_puntoventa'),(68,'Can view Punto de Venta',17,'view_puntoventa'),(69,'Can add Libro IVA Ventas',18,'add_libroivaventas'),(70,'Can change Libro IVA Ventas',18,'change_libroivaventas'),(71,'Can delete Libro IVA Ventas',18,'delete_libroivaventas'),(72,'Can view Libro IVA Ventas',18,'view_libroivaventas'),(73,'Can add Item de Factura',19,'add_facturaitem'),(74,'Can change Item de Factura',19,'change_facturaitem'),(75,'Can delete Item de Factura',19,'delete_facturaitem'),(76,'Can view Item de Factura',19,'view_facturaitem'),(77,'Can add Pago de Venta',20,'add_pagoventa'),(78,'Can change Pago de Venta',20,'change_pagoventa'),(79,'Can delete Pago de Venta',20,'delete_pagoventa'),(80,'Can view Pago de Venta',20,'view_pagoventa'),(81,'Can add Sub Tipo de Cuenta',21,'add_subtipocuenta'),(82,'Can change Sub Tipo de Cuenta',21,'change_subtipocuenta'),(83,'Can delete Sub Tipo de Cuenta',21,'delete_subtipocuenta'),(84,'Can view Sub Tipo de Cuenta',21,'view_subtipocuenta'),(85,'Can add Tipo de Gasto',22,'add_tipogasto'),(86,'Can change Tipo de Gasto',22,'change_tipogasto'),(87,'Can delete Tipo de Gasto',22,'delete_tipogasto'),(88,'Can view Tipo de Gasto',22,'view_tipogasto'),(89,'Can add Intento de Login',23,'add_loginattempt'),(90,'Can change Intento de Login',23,'change_loginattempt'),(91,'Can delete Intento de Login',23,'delete_loginattempt'),(92,'Can view Intento de Login',23,'view_loginattempt'),(93,'Can add IP Bloqueada',24,'add_ipblacklist'),(94,'Can change IP Bloqueada',24,'change_ipblacklist'),(95,'Can delete IP Bloqueada',24,'delete_ipblacklist'),(96,'Can view IP Bloqueada',24,'view_ipblacklist'),(97,'Can add Log de Auditoría',25,'add_auditlog'),(98,'Can change Log de Auditoría',25,'change_auditlog'),(99,'Can delete Log de Auditoría',25,'delete_auditlog'),(100,'Can view Log de Auditoría',25,'view_auditlog'),(101,'Can add Configuración de Seguridad',26,'add_securitysettings'),(102,'Can change Configuración de Seguridad',26,'change_securitysettings'),(103,'Can delete Configuración de Seguridad',26,'delete_securitysettings'),(104,'Can view Configuración de Seguridad',26,'view_securitysettings'),(105,'Can add Backup',27,'add_backup'),(106,'Can change Backup',27,'change_backup'),(107,'Can delete Backup',27,'delete_backup'),(108,'Can view Backup',27,'view_backup'),(109,'Can add Retención',28,'add_retencion'),(110,'Can change Retención',28,'change_retencion'),(111,'Can delete Retención',28,'delete_retencion'),(112,'Can view Retención',28,'view_retencion'),(113,'Can add Percepción',29,'add_percepcion'),(114,'Can change Percepción',29,'change_percepcion'),(115,'Can delete Percepción',29,'delete_percepcion'),(116,'Can view Percepción',29,'view_percepcion');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$J4YklfDgq7nleGzgZkdOEA$l2Ov1DHqOVXSDVBVn9J0fHxI/ifgZSgoO4y4Fno0S5o=',NULL,1,'romina','','','',1,1,'2025-11-18 12:33:06.565171'),(2,'pbkdf2_sha256$600000$zHnsi98kR9J3BAmcHmXasQ$18gxwSxdIxsIrcMZBLBoBRHDOpxucqjFmXwogH9PBqs=','2026-02-26 23:07:56.986962',1,'admin','','','',1,1,'2025-11-18 13:36:40.485626'),(3,'pbkdf2_sha256$600000$7QQDRuDTZgerR4woV4kgZT$HWbw0skAbP5zov+lDnuozQk0fNPLT+sJSeXsW0SNlh8=',NULL,1,'akun','','','',1,1,'2025-11-18 15:11:47.759892'),(4,'pbkdf2_sha256$600000$lCZYffBtV1RvIRdWVql8Di$TsDdU7Hg81w5jcW3ymY/Dsskx/0tsUEm01mWHt1t9mA=','2026-02-23 19:21:57.655399',0,'Kiara','Kiara','kiki','',1,1,'2026-01-30 17:27:52.561138');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_cliente`
--

DROP TABLE IF EXISTS `comercial_cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_cliente` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `direccion` longtext NOT NULL,
  `localidad` varchar(100) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `condicion_iva` varchar(4) NOT NULL,
  `cuit` varchar(11) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cuit` (`cuit`)
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_cliente`
--

LOCK TABLES `comercial_cliente` WRITE;
/*!40000 ALTER TABLE `comercial_cliente` DISABLE KEYS */;
INSERT INTO `comercial_cliente` VALUES (7,'VIVIANA','GIOIA','','APOLINARIO FIGUEROA 1315','CABA','116166-0092','','2026-01-16 18:52:14.824293','CF',NULL,'',NULL),(8,'VICTORIA','GONZALEZ','','ANIBAL TROILO 913 TIMBRE 3','ALMAGRO','1158411181','','2026-01-16 19:03:39.022488','CF',NULL,'',NULL),(9,'CARLOS','ROMERO','','JUNCAL 3058 PISO 5','CABA','1141748756','','2026-01-16 19:08:28.509483','CF',NULL,'',NULL),(10,'NAZARETH','MIRANDA','','AZCUENAGA 936 PB','CABA','1162796207','','2026-01-16 19:21:46.585491','CF',NULL,'',NULL),(11,'JOSE','FRANZA','','MAIPU 1232 PISO1','CABA','1131720852','','2026-01-16 19:28:52.897417','CF',NULL,'',NULL),(12,'FACUNDO','FUEYO','','GALLARDO 577 PISO 5','CABA','1169284216','','2026-01-16 19:36:09.675478','CF',NULL,'',NULL),(13,'SANTIAGO','.','','BULNES 680 PISO 5 DPTO B','CABA','1149483878','','2026-01-16 19:41:52.078089','CF',NULL,'',NULL),(14,'CRISTINA','BRUNACCIO','','HONORIO PUEYRREDON 1438','CABA','','','2026-01-16 19:48:33.107857','CF',NULL,'',NULL),(15,'ANALIA','.','','SAN MARTIN 691 PISO 4 DPTO D','QUILMES CENTRO','1140466281','','2026-01-16 19:59:19.008438','CF',NULL,'',NULL),(16,'ANDREA','CASABAL','','ALTE.F.J. SEGUI 748 PISO 8 DPTO F','CABA','116368-3380','','2026-01-16 20:07:35.458167','CF',NULL,'',NULL),(17,'SEBASTIAN','SALAS','','MIRANDA 5114','CABA','115796-7005','','2026-01-16 20:13:00.709099','CF',NULL,'',NULL),(18,'CESAR','PACHECO','','ENTRE RIOS 521 PISO 3','CABA','117095-6336','','2026-01-16 20:17:04.483030','CF',NULL,'',NULL),(19,'GULIANA','PANIZZA','','CAMACUA 192 PISO 4 D','CABA','116948-1956','','2026-01-16 20:22:32.699891','CF',NULL,'',NULL),(20,'MARCELO','.','','NEW YORK 3369','CABA','116687-7785','','2026-01-16 20:37:49.245826','CF',NULL,'',NULL),(21,'MARCELA','ROSSI','','VERA 1464 1 2','CAPITAL FEDERAL','','','2026-01-19 16:29:58.201541','CF',NULL,'',NULL),(22,'NICOLAS','DERECHO','','LASCANO 6017','CAPITAL FEDERAL','','','2026-01-19 16:32:56.296791','CF',NULL,'',NULL),(23,'JOHANA','MENDOZA','','FRAGATA SARMIENTO 2054 PB A','CAPITAL FEDERAL','','','2026-01-19 16:38:48.035327','CF',NULL,'',NULL),(24,'AMELIA','PUGLIESE','','VIRREY OLAGER 3046','CAPITAL FEDERAL','','','2026-01-19 16:49:09.650489','CF',NULL,'',NULL),(25,'PATRICIA','RODRIGUEZ','','GAONA 4264','CAPITAL FEDERAL','','','2026-01-19 16:50:55.761458','CF',NULL,'',NULL),(26,'EDUARDO','FERNANDEZ','','JOSE CUBAS 3289','CAPITAL FEDERAL','','','2026-01-20 16:09:54.043432','CF',NULL,'',NULL),(27,'LORENA','GASTAL','','RIVADAVIA 5123 PISO 22 10','CABA','1159947906','','2026-01-30 17:39:30.517961','CF',NULL,'',NULL),(28,'PABLO','ALEMAN','','TUCUMAN 2361 BELLA VISTA','PROVINCIA DE BUENOS AIRES','1133640801','','2026-01-30 17:49:25.849324','CF',NULL,'17609711',NULL),(29,'TIZIANA','LA BANCA','','SALVADOR MARIA DEL CARRIL 3684 PISO 3','CABA','1130336658','','2026-01-30 17:59:30.892127','RI','30594322327','',NULL),(30,'HORACIO','.','','SANCHEZ DE BUSTAMANTE 2144 PISO 7 DEPTO A','CABA','1153250985','','2026-01-30 18:19:04.372390','CF','23101415449','',NULL),(31,'LUCILA','TARRICO','','PASAJE VIRASORO 2349 PISO 3 DPTO A','CABA','1137950068','','2026-01-30 18:33:28.873694','CF',NULL,'31234297',NULL),(32,'DANIEL','RODRIGUEZ','','LASCANO 5432 DEPTO A','CABA','1139404475','','2026-01-30 18:39:32.374572','CF',NULL,'18303999',NULL),(33,'MARCELO','FERNANDEZ BONFANTE','','ARTIGAS JOSE G 2643 PISO 1 DEPTO B','CABA','','','2026-01-30 18:47:51.247127','RI','20141522818','',NULL),(34,'PAULA','RODRIGUEZ','','BLANCO ENCALADA  5058 DEPTO 13','CABA','1169428684','','2026-01-30 18:53:17.962626','CF',NULL,'',NULL),(35,'FABIAN','YAJID','','MORON 2918 PISO 8','CABA','1154157981','','2026-01-30 19:01:58.701429','CF',NULL,'',NULL),(36,'PABLO','ONORATO','','BACACAY 4131 PISO 1 DEPTO D','CABA','113098 9915','','2026-01-30 19:07:20.282525','CF',NULL,'28325587',NULL),(37,'RAFAEL','SAENZ','','MUÑIZ 1125 PISO 8 DEPTO B','CABA','1123691199','','2026-01-30 19:30:50.418083','CF',NULL,'',NULL),(38,'CESAR','PACHECO','','ENTRE RIOS 521 PISO 3','CABA','1170956336','','2026-01-30 19:38:19.609874','CF',NULL,'',NULL),(39,'CARMEN','.','','FRENCH 2377 PISO 6 DEPTO D','CABA','1145325024','','2026-01-30 19:56:44.605772','CF',NULL,'',NULL),(40,'JESICA','MONTIEL','RAVA BURSATIL','25 DE MAYO 277 PISO 5 - 24','CAPITAL FEDERAL','','','2026-01-30 19:58:04.576701','RI','30595025024','',NULL),(41,'HERNAN','.','MARIA DEL CARMEN SANGUINETTI','EL MIRASOL 555','CAPITAL FEDERAL','','','2026-01-30 20:47:40.740662','CF','27048992310','',NULL),(42,'VANESA','FERRER','FERNANDEZ AMANDA DOLORES','LOS OLMOS 2365','CAPITAL FEDERAL','','','2026-01-30 20:53:41.609868','CF',NULL,'11231343',NULL),(43,'CRISTIAN','ORTIZ','CRISTEX','ESTOMBA 785','CABA','','','2026-01-31 12:25:30.641594','RI','33708625979','',NULL),(44,'GUILLERMO MIGUEL','RUBERTO','','25 DE MAYO 347','CABA','','','2026-01-31 14:45:30.743846','RI','20084471438','',NULL),(45,'ASOCIACION AMIGOS DEL MUSEO DE','ARTE MODERNO','ASOCIACION AMIGOS DEL MUSEO DE ARTE MODERNO','SAN JUAN 350','CAPITAL FEDERAL','','','2026-01-31 14:59:05.497793','EX','30625488490','',NULL),(46,'ADRIANA','SOTO','','MAIPU 388 PISO 14 B','CAPITAL','1159229871','','2026-02-04 17:16:11.556862','CF',NULL,'',NULL),(47,'GABRIELA','CABRONE','','MORON 5028 PISO 1','CABA','1135802189','','2026-02-04 17:45:11.415750','CF',NULL,'',NULL),(48,'GONZALO','DREISPIEL','DREISPIEL GUSTAVO ERNESTO','LUIS VIALE 3303','CAPITAL FEDERAL','','','2026-02-09 14:59:54.842863','RI','20142143268','',NULL),(49,'MARIANO','POBLET','POBLET MACHADO MARIANO ANDRES','SAN BLAS 4097','CAPITAL FEDERAL','','','2026-02-09 15:04:57.217831','CF','28589108','',NULL),(50,'EDGARDO GUSTAVO','BURKE','EDGARDO GUSTAVO BURKE','SAN NICOLAS 2490 2 C','CAPITAL FEDERAL','','','2026-02-09 15:11:34.903189','CF','24872523','',NULL),(51,'LUCAS','AROZA','','PIEDRAS 810 7MO A','CABA','1140988702','','2026-02-23 16:45:03.999768','CF',NULL,'',NULL),(52,'ANGELA','.','','ARREGUI 4186','MONTE CASTRO','1139238998','','2026-02-23 17:05:50.980232','CF',NULL,'',NULL),(53,'SUSANA','GOMEZ','','IBAÑEZ 1914','PROVINCIA DE BUENOS AIRES','1150031590','','2026-02-23 19:30:03.815640','RI','30535622767','',NULL),(54,'MARIA','BICETTI','','ESMERALDA 1020 PISO 2 DPTO 23','CABA','','','2026-02-23 19:37:12.780688','CF','27040727588','',NULL),(55,'CAROLINA','MELENCHINI','','CATAMARCA 4195','CABA','','','2026-02-23 19:42:13.629996','CF',NULL,'24227303',NULL),(56,'CECILIA','MALATESTA','','INDEPENDENCIA 6236','PROVINCIA DE BUENOS AIRES','1151023602','','2026-02-23 19:45:34.497032','CF',NULL,'',NULL),(57,'FELIPE','FRYDMAN','','AVENIDA SANTA FE 5280 PISO 3 DEPTO E','CABA','1162218111','','2026-02-23 19:49:05.467449','CF',NULL,'',NULL),(58,'CAROLINA','CHACARITA','','FITZ ROY 1333','CABA','','','2026-02-23 19:54:01.312139','CF',NULL,'',NULL),(59,'ANDRES','MARIN','','DOBLAS 1542','CABA','','','2026-02-23 19:56:43.532084','CF',NULL,'',NULL),(60,'YESICA','POGGIO','','PABLO POGGIO 993','VILLA BOSH','','','2026-02-23 20:07:35.117031','CF','27317506444','',NULL),(61,'PEDRO','BENEGAS','','JOSE ANTONIO CABRERA  3840 10C','CABS','','','2026-02-24 12:19:31.312132','CF',NULL,'',NULL),(62,'GIULIANA','/ARIEL','','JEAN JAURES 963 PB B','CABA','1157539693','','2026-02-24 12:24:11.474049','CF',NULL,'',NULL),(63,'CLAUDIA','VAZQUEZ','','AV DE MAYO 1316 4 D','CABA','','','2026-02-24 12:28:31.640288','CF',NULL,'',NULL),(64,'HERNAN','VALLEDOR','','JUNIN 1631 PB C','.','1151612959','','2026-02-24 12:34:56.914057','CF',NULL,'',NULL),(65,'DANIEL','RODRIGUEZ','','LASCANO 1260','CABA','','','2026-02-24 12:41:42.134042','CF',NULL,'',NULL),(66,'ESTELA','MAIDANA','','SARANDI 686 P2 DF','CABA','','','2026-02-24 12:50:09.898034','RI','27220052740','',NULL),(67,'MALE','OCCHIONE','','LARREA 1429','CABA','','','2026-02-24 13:07:18.952505','RI','27396254811','',NULL),(68,'JOSEFA','MENDOZA NIETO','','TORQUINST 2265 P3 DEPTO D','SANTOS LUGARES','1161437898','','2026-02-24 13:15:40.275922','CF',NULL,'',NULL),(69,'VANESA','FERRER','','LOS OLMOS 2365 BARRIO LA LONJA','PILAR','1168556957','','2026-02-24 13:25:21.166474','CF',NULL,'11231343',NULL);
/*!40000 ALTER TABLE `comercial_cliente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_compra`
--

DROP TABLE IF EXISTS `comercial_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_compra` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero_pedido` varchar(50) NOT NULL,
  `fecha_pago` date NOT NULL,
  `importe_abonado` decimal(12,2) NOT NULL,
  `descripcion` longtext NOT NULL,
  `comprobante` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `cuenta_id` bigint NOT NULL,
  `con_factura` tinyint(1) NOT NULL,
  `numero_factura` varchar(50) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `tipo_gasto_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_compra_created_by_id_907524cd_fk_auth_user_id` (`created_by_id`),
  KEY `comercial_compra_cuenta_id_93a3ebfa_fk_comercial_cuenta_id` (`cuenta_id`),
  KEY `comercial_compra_tipo_gasto_id_fk` (`tipo_gasto_id`),
  CONSTRAINT `comercial_compra_created_by_id_907524cd_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `comercial_compra_cuenta_id_93a3ebfa_fk_comercial_cuenta_id` FOREIGN KEY (`cuenta_id`) REFERENCES `comercial_cuenta` (`id`),
  CONSTRAINT `comercial_compra_tipo_gasto_id_fk` FOREIGN KEY (`tipo_gasto_id`) REFERENCES `comercial_subtipocuenta` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_compra`
--

LOCK TABLES `comercial_compra` WRITE;
/*!40000 ALTER TABLE `comercial_compra` DISABLE KEYS */;
INSERT INTO `comercial_compra` VALUES (1,'01','2026-01-06',379800.00,'ENERO','5-574','2026-01-15 14:41:00.047202',2,1,1,'',NULL,NULL),(3,'01','2026-01-14',7857356.01,'ENERO','801','2026-01-15 14:54:06.417767',2,3,1,'',NULL,NULL),(4,'01','2026-01-14',1352175.00,'ENERO','185','2026-01-15 14:58:15.424895',2,4,1,'',NULL,NULL),(5,'01','2026-01-16',914221.31,'ENERO','11629','2026-01-16 18:34:18.637714',2,5,1,'',NULL,NULL),(6,'01','2026-01-07',2265150.21,'ENERO','5-57481','2026-01-16 18:36:38.319626',2,2,1,'',NULL,NULL),(7,'PVC','2026-01-30',1.00,'','','2026-01-30 17:41:08.374468',2,1,1,'','2026-01-30 17:59:38.408817',NULL),(8,'1','2026-02-03',10000.00,'','','2026-02-03 15:59:19.806060',2,7,0,'','2026-02-04 17:54:29.352710',15),(9,'01','2026-01-02',45000.00,'','','2026-02-04 14:26:38.123180',4,12,0,'',NULL,23),(10,'01','2026-01-05',560000.00,'','','2026-02-04 14:34:13.887488',4,13,0,'',NULL,9),(11,'01','2026-01-07',260000.00,'','','2026-02-04 14:35:30.854875',4,13,0,'',NULL,9),(12,'01','2026-01-08',260000.00,'','','2026-02-04 14:36:59.298334',4,13,0,'',NULL,9),(13,'01','2026-01-12',260000.00,'','','2026-02-04 14:37:58.766583',4,13,0,'',NULL,10),(14,'01','2026-01-09',150000.00,'','','2026-02-04 14:39:17.725854',4,13,0,'',NULL,9),(15,'01','2026-01-09',45000.00,'','','2026-02-04 14:41:30.922460',4,12,0,'',NULL,23),(16,'01','2026-01-09',200000.00,'','','2026-02-04 14:42:58.607689',4,9,0,'',NULL,16),(17,'01','2026-01-09',300000.00,'','','2026-02-04 14:45:05.777663',4,10,0,'',NULL,21),(18,'01','2026-01-15',600000.00,'','','2026-02-04 14:46:06.426183',4,7,0,'',NULL,15),(19,'01','2026-01-16',600000.00,'','','2026-02-04 14:47:36.619775',4,9,0,'',NULL,16),(20,'01','2026-01-16',300000.00,'','','2026-02-04 14:49:01.739052',4,10,0,'',NULL,21),(21,'01','2026-01-16',700000.00,'','','2026-02-04 14:50:28.869433',4,7,0,'',NULL,14),(22,'01','2026-01-16',1480000.00,'','','2026-02-04 14:53:32.843433',4,8,0,'',NULL,18),(23,'01','2026-01-19',240000.00,'','','2026-02-04 14:55:09.292151',4,13,0,'',NULL,9),(24,'01','2026-01-20',180000.00,'','','2026-02-04 14:59:43.331519',4,11,0,'',NULL,22),(25,'01','2026-01-20',64000.00,'','','2026-02-04 15:00:31.530488',4,12,0,'',NULL,23),(26,'01','2026-01-21',60000.00,'','','2026-02-04 15:01:39.111049',4,12,0,'',NULL,23),(27,'01','2026-01-24',1000000.00,'','','2026-02-04 15:02:49.351899',4,13,0,'',NULL,9),(28,'01','2026-01-24',900000.00,'','','2026-02-04 15:03:40.386153',4,14,0,'',NULL,10),(29,'01','2026-01-23',90000.00,'','','2026-02-04 15:04:48.244402',4,11,0,'',NULL,22),(30,'01','2026-01-23',300000.00,'','','2026-02-04 15:05:46.019930',4,10,0,'',NULL,21),(31,'01','2026-01-23',700000.00,'','','2026-02-04 15:07:21.670811',4,7,0,'',NULL,14),(32,'01','2026-01-26',120000.00,'','','2026-02-04 15:09:30.103726',4,11,0,'',NULL,22),(33,'25-12','2026-01-19',714663.62,'','','2026-02-04 15:11:30.271952',2,15,1,'',NULL,24),(34,'01','2026-01-27',40000.00,'','','2026-02-04 15:11:54.374710',4,11,0,'',NULL,22),(35,'25-12','2026-01-19',3779390.98,'','','2026-02-04 15:12:27.970356',2,16,1,'',NULL,27),(36,'01','2026-01-27',60000.00,'','','2026-02-04 15:12:43.856036',4,13,0,'',NULL,9),(37,'26-1','2026-02-04',62743.08,'','','2026-02-04 15:13:22.743867',2,19,1,'',NULL,26),(38,'01','2026-01-28',300000.00,'','','2026-02-04 15:13:53.251999',4,13,0,'',NULL,9),(39,'25-12','2026-01-12',61230.68,'','','2026-02-04 15:13:57.501752',2,19,1,'',NULL,26),(40,'01','2026-01-29',450000.00,'','','2026-02-04 15:15:05.797743',4,13,0,'',NULL,9),(41,'25-12','2026-01-12',765246.99,'','','2026-02-04 15:17:08.576995',2,20,1,'',NULL,28),(42,'01','2026-01-30',510000.00,'','','2026-02-04 15:18:39.432089',4,14,0,'',NULL,10),(43,'01','2026-01-30',300000.00,'','','2026-02-04 15:19:53.283852',4,10,0,'',NULL,21),(44,'01','2026-01-30',700000.00,'','','2026-02-04 15:21:05.396233',4,7,0,'',NULL,14),(45,'01','2026-01-26',4434245.00,'','','2026-02-04 15:25:57.707967',4,21,0,'',NULL,29),(46,'01','2026-01-30',280000.00,'','','2026-02-04 15:29:31.857136',4,13,0,'',NULL,9),(47,'37185','2026-01-27',250000.00,'','','2026-02-04 15:37:00.965748',4,22,0,'',NULL,30),(48,'37041','2026-01-19',997048.77,'','','2026-02-04 15:40:41.061594',4,22,0,'',NULL,30),(49,'20366 20364 20351','2026-01-19',3171423.55,'','','2026-02-04 15:45:46.953817',4,23,0,'',NULL,31),(50,'143','2026-02-04',2043360.00,'','','2026-02-04 17:39:08.000711',4,21,0,'',NULL,29),(51,'01','2026-02-04',442533.22,'','','2026-02-04 17:42:10.597549',4,5,1,'11685',NULL,12),(52,'01','2026-02-03',774171.00,'','','2026-02-04 18:15:10.480533',4,26,0,'',NULL,12),(53,'01','2026-02-14',620890.00,'','','2026-02-04 18:15:58.158872',4,26,0,'',NULL,12),(54,'01','2026-02-02',42700.00,'','','2026-02-04 18:21:56.991047',4,25,0,'',NULL,37),(55,'582','2026-02-06',390460.00,'','','2026-02-23 14:43:00.877728',4,1,1,'582',NULL,12),(56,'01','2026-02-04',105000.00,'','','2026-02-23 14:45:40.930777',4,11,1,'229',NULL,22),(57,'01','2026-02-18',105000.00,'','','2026-02-23 14:46:58.009650',4,11,1,'231',NULL,22),(58,'01','2026-02-05',90000.00,'','','2026-02-23 14:51:45.941099',4,11,0,'',NULL,22),(59,'01','2026-02-03',260000.00,'','','2026-02-23 14:52:41.459209',4,13,0,'',NULL,9),(60,'01','2026-02-06',1150000.00,'','','2026-02-23 15:08:02.456392',4,28,0,'',NULL,42),(61,'01','2026-02-09',50000.00,'','','2026-02-23 15:16:20.401920',4,29,0,'',NULL,43),(62,'01','2026-02-10',50000.00,'','','2026-02-23 15:17:57.227845',4,29,0,'',NULL,43),(63,'01','2026-02-10',120000.00,'','','2026-02-23 15:21:45.042279',4,30,0,'',NULL,44),(64,'01','2026-02-11',600000.00,'','','2026-02-23 15:22:46.511352',4,13,0,'',NULL,9),(65,'01','2026-02-11',500000.00,'','','2026-02-23 15:23:32.766816',4,13,0,'',NULL,9),(66,'01','2026-02-12',1700000.00,'','','2026-02-23 15:24:22.503010',4,13,0,'',NULL,9),(67,'01','2026-02-12',2507175.00,'','','2026-02-23 15:26:09.364712',4,4,0,'',NULL,12),(68,'01','2026-02-12',350000.00,'','','2026-02-23 15:27:17.665163',4,13,0,'',NULL,9),(69,'01','2026-02-13',3000000.00,'VACACIONES Y COMISION','','2026-02-23 15:30:07.160216',4,7,0,'',NULL,15),(70,'01','2026-02-17',380000.00,'','','2026-02-23 15:31:00.728477',4,13,0,'',NULL,9),(71,'01','2026-02-19',450000.00,'','','2026-02-23 15:32:01.891242',4,28,0,'',NULL,42),(72,'01','2026-02-20',43000.00,'','','2026-02-23 15:35:35.382946',4,8,0,'',NULL,45),(73,'01','2026-02-20',300000.00,'','','2026-02-23 15:36:48.795198',4,10,0,'',NULL,21),(74,'01','2026-02-20',250000.00,'','','2026-02-23 15:38:14.154556',4,9,0,'',NULL,16),(75,'01','2026-02-21',1800000.00,'','','2026-02-23 15:41:16.639777',4,13,0,'',NULL,42),(76,'01','2026-02-19',773746.80,'','','2026-02-23 15:45:05.817836',4,22,0,'',NULL,12),(77,'01','2026-01-27',4132.50,'','','2026-02-23 15:57:04.819852',4,21,0,'',NULL,13),(78,'01','2026-01-17',225.00,'','','2026-02-23 15:58:14.990658',4,21,0,'',NULL,13),(79,'01','2026-02-19',2267983.79,'','','2026-02-23 16:03:40.865940',4,31,1,'30808',NULL,12),(80,'01','2026-02-19',95422.27,'','','2026-02-23 16:09:56.422888',4,32,1,'65563',NULL,12),(81,'01','2026-02-12',1352175.00,'','','2026-02-23 16:13:49.688484',4,4,1,'',NULL,12),(82,'01','2026-02-10',116160.00,'','','2026-02-23 16:16:58.882724',4,33,1,'163',NULL,12),(83,'01','2026-01-30',1356165.27,'','','2026-02-23 16:18:14.229373',4,23,1,'5911',NULL,12),(84,'01','2026-02-18',2057000.00,'','','2026-02-23 16:20:30.787248',4,34,1,'148',NULL,12),(85,'01','2026-02-20',2495000.00,'','','2026-02-23 17:24:48.855219',4,8,0,'',NULL,18);
/*!40000 ALTER TABLE `comercial_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_cuenta`
--

DROP TABLE IF EXISTS `comercial_cuenta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_cuenta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `direccion` longtext NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `tipo_cuenta_id` bigint NOT NULL,
  `condicion_iva` varchar(4) NOT NULL,
  `cuit` varchar(11) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_cuenta_tipo_cuenta_id_7e67d018_fk_comercial` (`tipo_cuenta_id`),
  CONSTRAINT `comercial_cuenta_tipo_cuenta_id_7e67d018_fk_comercial` FOREIGN KEY (`tipo_cuenta_id`) REFERENCES `comercial_tipocuenta` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_cuenta`
--

LOCK TABLES `comercial_cuenta` WRITE;
/*!40000 ALTER TABLE `comercial_cuenta` DISABLE KEYS */;
INSERT INTO `comercial_cuenta` VALUES (1,'HERNAN MARIO BENITEZ','SIATINA MARKETING INTELIGENTE','','COMBATE DE LOS POZOS 1477',1,'2026-01-15 14:36:14.268888',1,'','',NULL),(2,'LUXE PERFILES','PERSIANAS IBERO AMERICANAS','+54351-4751050','.',1,'2026-01-15 14:44:29.093339',1,'','',NULL),(3,'SEQUEIRA TARDAO GUSTAVO HERNAN','SEQUEIRA TARDAO GUSTAVO HERNAN','','CURUPAYTI 1334 - MORON',1,'2026-01-15 14:52:13.984377',1,'','',NULL),(4,'AUSGAN SRL','AUSGAN SRL','','LOPE DE VEGA AV 1112 DPTO2',1,'2026-01-15 14:56:32.910266',1,'','',NULL),(5,'LILIANA MABEL GARCIA','METALES MATADEROS','','AV CARDENAS 2136',1,'2026-01-16 18:31:39.420715',1,'','',NULL),(6,'Servicio','','','',1,'2026-02-01 20:33:46.350193',2,'','',NULL),(7,'Cristian','','','',1,'2026-02-03 15:57:29.933484',12,'','',NULL),(8,'Veronica','','','',1,'2026-02-03 15:58:08.028811',12,'','',NULL),(9,'Juan','','','',1,'2026-02-03 15:58:16.156994',12,'','',NULL),(10,'Elias','','','',1,'2026-02-03 15:58:24.397621',12,'','',NULL),(11,'Milco','','','',1,'2026-02-03 15:58:34.529715',14,'','',NULL),(12,'Sergio','','','',1,'2026-02-03 15:58:44.049139',14,'','',NULL),(13,'Fredy','','','',1,'2026-02-04 14:32:43.483464',11,'','',NULL),(14,'COLOCADORES','COLOCADORES','','',0,'2026-02-04 14:33:04.507375',11,'','','2026-02-04 17:47:33.905636'),(15,'ARCA','ARCA','','',0,'2026-02-04 14:52:15.627755',15,'','','2026-02-04 17:14:27.023628'),(16,'ARCA','ARCA','','',0,'2026-02-04 14:52:27.235127',15,'','','2026-02-04 17:14:43.824748'),(17,'ARCA','ARCA','','',0,'2026-02-04 14:52:38.581812',15,'','','2026-02-04 17:14:49.091514'),(18,'ARCA','ARCA','','',0,'2026-02-04 14:52:49.993711',15,'','','2026-02-04 17:14:38.439576'),(19,'ARCA','ARCA','','',0,'2026-02-04 14:54:14.659583',15,'','','2026-02-04 17:14:55.076493'),(20,'ARCA','ARCA','','',1,'2026-02-04 14:55:06.804470',15,'','',NULL),(21,'PROALUM','PROALUM','','',1,'2026-02-04 15:24:51.583546',1,'','',NULL),(22,'ARVA','ARVA','','',1,'2026-02-04 15:35:26.797557',1,'','',NULL),(23,'CRISTALES SAENZ SRL','CRISTALEZ SAENZ SRL','','',1,'2026-02-04 15:44:25.059985',1,'','',NULL),(24,'ARCA','ARCA','','',0,'2026-02-04 16:29:35.257301',15,'','','2026-02-04 17:15:09.909023'),(25,'PAPELERA','PAPELERA','','',1,'2026-02-04 17:43:00.191632',16,'','',NULL),(26,'Humberto','Humberto','','',1,'2026-02-04 17:48:29.401049',1,'','',NULL),(27,'DARIO PONTORIERO','DARIO PONTORIERO','','',1,'2026-02-04 18:11:54.312206',17,'','',NULL),(28,'DIEGO','','','',1,'2026-02-23 15:02:02.322005',11,'','',NULL),(29,'MATIAS','','','',1,'2026-02-23 15:10:48.242655',14,'','',NULL),(30,'ENRIQUE','','','',1,'2026-02-23 15:20:19.478067',14,'','',NULL),(31,'ALUMINIO BROWN','','','',1,'2026-02-23 16:02:00.933536',1,'','',NULL),(32,'MARRA ALUMINIO','','','',1,'2026-02-23 16:07:28.101780',1,'','',NULL),(33,'INSUMOLOGISTIC','','','',1,'2026-02-23 16:15:44.184736',1,'','',NULL),(34,'CONSTRUCCION Y FERRETERIA','','','',1,'2026-02-23 16:19:27.973335',1,'','',NULL),(35,'Matias Fariña','','','',1,'2026-02-26 01:35:38.336949',1,'','',NULL);
/*!40000 ALTER TABLE `comercial_cuenta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_pagoventa`
--

DROP TABLE IF EXISTS `comercial_pagoventa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_pagoventa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `monto` decimal(12,2) NOT NULL,
  `fecha_pago` date NOT NULL,
  `forma_pago` varchar(20) NOT NULL,
  `observaciones` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `venta_id` bigint NOT NULL,
  `numero_factura` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_pagoventa_created_by_id_4de2011d_fk_auth_user_id` (`created_by_id`),
  KEY `comercial_pagoventa_venta_id_ccca6163_fk_comercial_venta_id` (`venta_id`),
  CONSTRAINT `comercial_pagoventa_created_by_id_4de2011d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `comercial_pagoventa_venta_id_ccca6163_fk_comercial_venta_id` FOREIGN KEY (`venta_id`) REFERENCES `comercial_venta` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_pagoventa`
--

LOCK TABLES `comercial_pagoventa` WRITE;
/*!40000 ALTER TABLE `comercial_pagoventa` DISABLE KEYS */;
INSERT INTO `comercial_pagoventa` VALUES (1,5.00,'2026-01-30','transferencia','','2026-01-30 17:02:35.977808',2,27,''),(2,300.00,'2026-01-30','efectivo','','2026-01-30 18:07:03.045805',2,31,''),(3,382562.00,'2026-01-23','efectivo','','2026-01-30 18:23:32.448825',4,32,''),(4,940988.00,'2026-01-30','efectivo','','2026-01-30 19:33:49.658396',4,39,''),(5,1020125.00,'2026-01-29','efectivo','','2026-01-30 19:42:47.574926',4,40,''),(6,825126.00,'2026-01-29','efectivo','','2026-01-30 19:53:37.195592',4,41,''),(7,1534069.00,'2026-01-27','efectivo','','2026-01-30 19:59:29.480586',4,42,''),(8,2208991.73,'2025-12-30','transferencia','','2026-01-31 12:28:59.956104',2,47,''),(9,11640141.99,'2026-01-20','transferencia','','2026-01-31 12:32:05.907961',2,47,''),(10,2672879.99,'2025-12-30','transferencia','','2026-01-31 12:46:52.566459',2,48,''),(11,11640141.99,'2026-01-20','transferencia','','2026-01-31 12:47:20.041191',2,48,''),(12,2165374.00,'2026-02-04','efectivo','','2026-02-04 17:21:05.476008',4,51,''),(13,651755.00,'2026-02-03','efectivo','efectivo','2026-02-04 17:47:26.481824',4,52,'efectivo'),(14,2100000.00,'2025-12-18','transferencia','','2026-02-09 15:02:52.344829',2,53,'173'),(15,8281396.49,'2026-02-06','transferencia','','2026-02-09 15:03:23.033430',2,53,'183'),(16,1858500.00,'2025-12-19','transferencia','','2026-02-09 15:10:29.888299',2,54,'110'),(17,1134678.78,'2025-12-02','transferencia','','2026-02-09 15:14:30.777868',2,55,'102'),(18,239203.00,'2026-02-12','efectivo','','2026-02-23 16:32:49.613054',4,20,''),(19,1014733.00,'2026-02-14','efectivo','','2026-02-23 16:36:06.248202',4,16,''),(20,1016264.48,'2026-02-12','transferencia','','2026-02-23 16:39:13.636938',4,30,''),(21,1375000.00,'2026-02-11','efectivo','','2026-02-23 16:51:45.973577',4,57,''),(22,1677102.00,'2026-02-10','efectivo','','2026-02-23 16:55:09.790933',4,29,''),(23,352393.00,'2026-02-09','efectivo','','2026-02-23 16:58:57.372991',4,14,''),(24,888480.00,'2026-02-14','efectivo','','2026-02-23 17:09:00.303824',4,58,'');
/*!40000 ALTER TABLE `comercial_pagoventa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_percepcion`
--

DROP TABLE IF EXISTS `comercial_percepcion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_percepcion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `observaciones` longtext NOT NULL,
  `importe` decimal(12,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `venta_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_percepcion_venta_id_2b83adc7_fk_comercial_venta_id` (`venta_id`),
  CONSTRAINT `comercial_percepcion_venta_id_2b83adc7_fk_comercial_venta_id` FOREIGN KEY (`venta_id`) REFERENCES `comercial_venta` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_percepcion`
--

LOCK TABLES `comercial_percepcion` WRITE;
/*!40000 ALTER TABLE `comercial_percepcion` DISABLE KEYS */;
/*!40000 ALTER TABLE `comercial_percepcion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_retencion`
--

DROP TABLE IF EXISTS `comercial_retencion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_retencion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `concepto` varchar(200) NOT NULL,
  `descripcion` longtext NOT NULL,
  `numero_comprobante` varchar(100) NOT NULL,
  `importe_isar` decimal(12,2) NOT NULL,
  `importe_retenido` decimal(12,2) NOT NULL,
  `fecha_comprobante` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `pago_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_retencion_pago_id_91ab2cbf_fk_comercial_pagoventa_id` (`pago_id`),
  CONSTRAINT `comercial_retencion_pago_id_91ab2cbf_fk_comercial_pagoventa_id` FOREIGN KEY (`pago_id`) REFERENCES `comercial_pagoventa` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_retencion`
--

LOCK TABLES `comercial_retencion` WRITE;
/*!40000 ALTER TABLE `comercial_retencion` DISABLE KEYS */;
/*!40000 ALTER TABLE `comercial_retencion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_subtipocuenta`
--

DROP TABLE IF EXISTS `comercial_subtipocuenta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_subtipocuenta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(200) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `tipo_cuenta_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_subtipocue_tipo_cuenta_id_068aae5d_fk_comercial` (`tipo_cuenta_id`),
  CONSTRAINT `comercial_subtipocue_tipo_cuenta_id_068aae5d_fk_comercial` FOREIGN KEY (`tipo_cuenta_id`) REFERENCES `comercial_tipocuenta` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_subtipocuenta`
--

LOCK TABLES `comercial_subtipocuenta` WRITE;
/*!40000 ALTER TABLE `comercial_subtipocuenta` DISABLE KEYS */;
INSERT INTO `comercial_subtipocuenta` VALUES (1,'luz','',0,'2026-01-30 19:20:40.619574','2026-01-30 18:08:35.992471',2),(2,'internet','',0,'2026-01-30 19:20:37.907516','2026-01-30 18:08:46.412107',2),(3,'Cristales Saenz','',0,'2026-01-30 19:21:32.388538','2026-01-30 19:20:31.441043',1),(4,'SERVICIOS','',0,'2026-01-30 19:43:58.548210','2026-01-30 19:32:47.273908',2),(5,'Edesur','Nro de cliente 04417017',1,NULL,'2026-01-30 19:43:19.337385',2),(6,'AYSA','NRO CLIENTE 464929',1,NULL,'2026-01-30 19:43:52.423523',2),(7,'Movistar linea celular','114482992',1,NULL,'2026-01-30 19:44:32.523748',2),(8,'GOOGLE','',1,NULL,'2026-01-30 19:46:03.668423',13),(9,'FREDY','',1,NULL,'2026-01-30 19:46:20.659568',11),(10,'DIEGO','',0,'2026-02-23 14:56:12.812452','2026-01-30 19:46:29.034960',11),(11,'Movista Linea Telefono','',1,NULL,'2026-02-02 22:04:50.485768',2),(12,'Pago','',1,NULL,'2026-02-02 22:15:19.268429',1),(13,'Pago en dolares','',1,NULL,'2026-02-02 22:15:52.677835',1),(14,'Cristian Semanal','',1,NULL,'2026-02-03 15:45:33.457121',12),(15,'Cristian comision','',1,NULL,'2026-02-03 15:45:43.436489',12),(16,'Juan Semanal','',1,NULL,'2026-02-03 15:45:54.856013',12),(17,'Juan extra','',1,NULL,'2026-02-03 15:46:04.003353',12),(18,'Veronica Comision','',1,NULL,'2026-02-03 15:46:13.815584',12),(19,'Veronica Extra','',1,NULL,'2026-02-03 15:46:23.689108',12),(20,'Elias Extra','',1,NULL,'2026-02-03 15:46:41.422113',12),(21,'Elias Semanal','',1,NULL,'2026-02-03 15:46:52.292869',12),(22,'Milco','',1,NULL,'2026-02-03 15:47:45.232654',14),(23,'Sergio','',1,NULL,'2026-02-03 15:47:53.879670',14),(24,'Convenio Multilateral','',1,NULL,'2026-02-04 15:09:43.957608',15),(25,'GANANCIAS','',1,NULL,'2026-02-04 15:09:56.779164',15),(26,'AUTONOMOS','',1,NULL,'2026-02-04 15:10:06.862409',15),(27,'IVA','',1,NULL,'2026-02-04 15:10:16.718466',15),(28,'Cargas Sociales','',1,NULL,'2026-02-04 15:16:10.911097',15),(29,'PROALUM','',1,NULL,'2026-02-04 15:24:11.745916',1),(30,'ARVA','',0,'2026-02-04 17:49:03.637925','2026-02-04 15:33:22.675860',1),(31,'CRISTALES SAENZ SRL','',1,NULL,'2026-02-04 15:43:47.089010',1),(32,'test','',0,'2026-02-04 17:01:05.837602','2026-02-04 16:55:43.633743',1),(33,'RETIRO CUENTA PROPIA','',1,NULL,'2026-02-04 17:45:25.424103',17),(34,'TARJETA BBVA','',1,NULL,'2026-02-04 17:45:38.476306',17),(35,'TARJETA GALICIA','',1,NULL,'2026-02-04 17:45:47.966342',17),(36,'COMBUSTIBLE','',1,NULL,'2026-02-04 17:45:58.164610',17),(37,'pago','',1,NULL,'2026-02-04 18:20:58.258554',16),(38,'DIEGO','',0,'2026-02-23 14:56:07.258597','2026-02-23 14:55:15.040426',11),(39,'DIEGO','',0,'2026-02-23 15:00:14.583557','2026-02-23 14:57:07.207927',11),(40,'DIEGO','',0,'2026-02-23 15:00:08.706068','2026-02-23 14:58:38.820780',11),(41,'DIEGO','',0,'2026-02-23 15:05:28.258565','2026-02-23 15:03:37.485985',12),(42,'Pago','',1,NULL,'2026-02-23 15:06:06.514946',11),(43,'MATIAS','',1,NULL,'2026-02-23 15:14:36.638580',14),(44,'ENRIQUE','',1,NULL,'2026-02-23 15:19:51.230048',14),(45,'MONOTRIBUTO VERO','',1,NULL,'2026-02-23 15:34:14.124293',12),(46,'ALUMINIO BROWN','',1,NULL,'2026-02-23 16:00:49.737657',1),(47,'MARRA ALUMINIO','',1,NULL,'2026-02-23 16:06:51.320702',1),(48,'ABL','',1,NULL,'2026-02-26 01:37:27.207652',2);
/*!40000 ALTER TABLE `comercial_subtipocuenta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_tipocuenta`
--

DROP TABLE IF EXISTS `comercial_tipocuenta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_tipocuenta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tipo` (`tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_tipocuenta`
--

LOCK TABLES `comercial_tipocuenta` WRITE;
/*!40000 ALTER TABLE `comercial_tipocuenta` DISABLE KEYS */;
INSERT INTO `comercial_tipocuenta` VALUES (1,'proveedores','PROVEEDORES',1,NULL),(2,'Servicios','SERVICIOS',1,NULL),(3,'Servicios akun','luz',0,'2026-01-30 19:19:07.468447'),(11,'Colocadores','COLOCADORES',1,NULL),(12,'Colaboradores','COLABORADORES',1,NULL),(13,'Publicidad','PUBLICIDAD',1,NULL),(14,'Flete','Flete',1,NULL),(15,'IMPUESTOS','IMPUESTOS',1,NULL),(16,'INSUMOS','INSUMOS',1,NULL),(17,'PERSONAL','PERSONAL',1,NULL);
/*!40000 ALTER TABLE `comercial_tipocuenta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comercial_venta`
--

DROP TABLE IF EXISTS `comercial_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comercial_venta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero_pedido` varchar(50) NOT NULL,
  `valor_total` decimal(12,2) NOT NULL,
  `sena` decimal(12,2) NOT NULL,
  `saldo` decimal(12,2) NOT NULL,
  `fecha_pago` date DEFAULT NULL,
  `forma_pago` varchar(20) NOT NULL,
  `con_factura` tinyint(1) NOT NULL,
  `tipo_factura` varchar(2) NOT NULL,
  `numero_factura` varchar(50) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `observaciones` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `cliente_id` bigint NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `monto_retenciones` decimal(12,2) NOT NULL,
  `tiene_retenciones` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comercial_venta_cliente_id_605488b5_fk_comercial_cliente_id` (`cliente_id`),
  CONSTRAINT `comercial_venta_cliente_id_605488b5_fk_comercial_cliente_id` FOREIGN KEY (`cliente_id`) REFERENCES `comercial_cliente` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comercial_venta`
--

LOCK TABLES `comercial_venta` WRITE;
/*!40000 ALTER TABLE `comercial_venta` DISABLE KEYS */;
INSERT INTO `comercial_venta` VALUES (6,'1205',4469430.00,0.00,0.00,'2026-01-02','efectivo',0,'','','colocado','','2026-01-16 18:56:44.390554','2026-01-16 18:58:25.899639',7,NULL,0.00,0),(7,'1222',1480967.00,0.00,0.00,'2026-01-07','efectivo',0,'','','colocado','','2026-01-16 19:06:10.308359','2026-01-16 19:06:10.308403',8,NULL,0.00,0),(8,'1211',409073.17,0.00,0.00,'2026-01-07','transferencia',1,'A','168-175','colocado','','2026-01-16 19:13:02.912603','2026-01-16 19:13:02.912646',9,NULL,0.00,0),(9,'1206',749864.82,0.00,0.00,'2026-01-06','transferencia',1,'B','98-115','colocado','','2026-01-16 19:26:10.856961','2026-01-16 19:26:10.856984',10,NULL,0.00,0),(10,'1219',918860.68,0.00,0.00,'2026-01-06','transferencia',1,'B','108-113','colocado','','2026-01-16 19:32:54.668897','2026-01-16 19:34:27.758539',11,NULL,0.00,0),(11,'1208',666015.00,0.00,0.00,'2026-01-09','transferencia',0,'','','colocado','','2026-01-16 19:39:06.122390','2026-01-16 19:39:06.122432',12,NULL,0.00,0),(12,'1223',1081293.00,0.00,0.00,'2026-01-08','efectivo',0,'','','colocado','','2026-01-16 19:44:43.217848','2026-01-16 19:44:43.217889',13,NULL,0.00,0),(13,'.',90750.00,0.00,0.00,'2026-01-07','transferencia',1,'B','114','entregado','','2026-01-16 19:50:04.964521','2026-01-16 19:50:04.964555',14,NULL,0.00,0),(14,'1227',704786.28,352393.14,0.14,NULL,'transferencia',1,'B','112','colocado','','2026-01-16 20:04:07.690613','2026-02-23 16:58:57.383725',15,NULL,0.00,0),(15,'1228',1636247.00,820000.00,816247.00,'2026-01-12','efectivo',0,'','','pendiente','','2026-01-16 20:10:58.783201','2026-01-16 20:10:58.783274',16,NULL,0.00,0),(16,'1229',2214733.00,1200000.00,0.00,NULL,'efectivo',0,'','','colocado','','2026-01-16 20:14:41.550691','2026-02-23 16:36:49.820688',17,NULL,0.00,0),(17,'1230',1108625.00,88500.00,1020125.00,'2026-01-10','efectivo',0,'','','pendiente','','2026-01-16 20:20:46.428620','2026-02-04 17:36:40.842672',18,'2026-02-04 17:36:40.838746',0.00,0),(18,'1231',4200000.00,1490000.00,2710000.00,'2026-01-12','efectivo',0,'','','pendiente','','2026-01-16 20:25:38.958721','2026-01-16 20:32:02.183542',19,NULL,0.00,0),(19,'1232',2598476.00,1039500.00,1558976.00,'2026-01-13','efectivo',0,'','','pendiente','','2026-01-16 20:36:01.002822','2026-01-16 20:36:01.002867',12,NULL,0.00,0),(20,'1233',439203.00,200000.00,0.00,NULL,'efectivo',0,'','','colocado','','2026-01-16 20:39:24.747891','2026-02-23 16:34:00.305475',20,NULL,0.00,0),(21,'HUMBERTO',1446458.00,720000.00,0.00,'2026-01-07','efectivo',0,'','','pendiente','','2026-01-19 16:31:41.343899','2026-01-19 16:31:41.343949',21,NULL,0.00,0),(22,'PVC',4608212.00,2235000.00,138212.00,'2026-01-12','efectivo',0,'','','pendiente','','2026-01-19 16:36:04.348919','2026-01-19 16:36:04.348957',22,NULL,0.00,0),(23,'PVC1',2469000.00,1192000.00,85000.00,'2026-01-12','efectivo',0,'','','pendiente','','2026-01-19 16:47:44.928155','2026-01-19 16:47:44.928186',23,NULL,0.00,0),(24,'PVC2',3407481.00,1490000.00,0.00,'2026-01-07','efectivo',0,'','','pendiente','','2026-01-19 16:50:23.127200','2026-01-19 16:50:23.127264',24,NULL,0.00,0),(25,'PERSIANA',1800000.00,900000.00,900000.00,'2026-01-08','efectivo',0,'','','pendiente','','2026-01-19 16:51:56.691828','2026-01-30 21:36:00.595427',25,'2026-01-30 21:36:00.591222',0.00,0),(26,'1224',472703.00,0.00,0.00,NULL,'transferencia',1,'A','176','colocado','','2026-01-20 16:11:04.320105','2026-01-20 16:11:20.059747',26,NULL,0.00,0),(27,'TEST',10.00,5.00,0.00,NULL,'',1,'','','pendiente','','2026-01-29 20:29:37.056905','2026-01-30 18:13:40.501817',26,'2026-01-30 18:13:40.492567',0.00,0),(28,'PVC',1.00,0.00,1.00,NULL,'',1,'','','pendiente','','2026-01-29 20:48:41.759428','2026-01-31 14:47:30.109963',7,'2026-01-31 14:47:30.105804',0.00,0),(29,'1234',3354302.00,1677200.00,0.00,NULL,'efectivo',0,'','','colocado','','2026-01-30 17:41:22.037718','2026-02-23 16:55:09.801536',27,NULL,0.00,0),(30,'1235',2032528.96,1016264.48,0.00,NULL,'transferencia',1,'B','118','colocado','','2026-01-30 17:54:58.634657','2026-02-23 16:39:13.656386',28,NULL,0.00,0),(31,'test1',1000.00,200.00,500.00,'2026-01-06','transferencia',1,'','','pendiente','','2026-01-30 18:06:17.780459','2026-01-30 18:07:40.588763',7,'2026-01-30 18:07:40.581788',0.00,0),(32,'1238',801466.00,418904.00,0.00,NULL,'transferencia',1,'B','119','colocado','','2026-01-30 18:22:32.060397','2026-02-23 17:15:55.444567',30,NULL,0.00,0),(33,'1239',6650574.00,3325287.51,3325286.49,'2026-01-20','transferencia',1,'B','120','pendiente','','2026-01-30 18:35:34.225648','2026-01-30 18:35:34.225675',31,NULL,0.00,0),(34,'1240',4060924.56,2030462.28,2030462.28,'2026-01-20','transferencia',1,'B','123','pendiente','','2026-01-30 18:41:10.683146','2026-01-30 18:41:10.683188',32,NULL,0.00,0),(35,'1241',6049075.56,3024537.78,3024537.78,'2026-01-23','transferencia',1,'A','181','pendiente','','2026-01-30 18:49:45.384915','2026-01-30 19:11:15.383976',33,NULL,0.00,0),(36,'1242',1810791.00,900000.00,910791.00,'2026-01-24','efectivo',0,'','','pendiente','','2026-01-30 18:55:08.889211','2026-01-30 18:58:09.228765',34,NULL,0.00,0),(37,'1243',1539877.00,700000.00,839877.00,'2026-01-26','efectivo',0,'','','pendiente','','2026-01-30 19:03:26.796604','2026-01-30 19:03:26.796644',35,NULL,0.00,0),(38,'1244',960513.73,480000.00,480513.73,'2026-01-26','transferencia',1,'B','122','pendiente','','2026-01-30 19:09:06.713979','2026-01-30 19:09:06.714006',36,NULL,0.00,0),(39,'1225',1540988.00,600000.00,0.00,'2025-12-30','efectivo',0,'','','colocado','','2026-01-30 19:32:15.838347','2026-01-30 19:34:25.339363',37,NULL,0.00,0),(40,'1230',2086157.37,1066032.37,0.00,'2026-01-10','efectivo',0,'','','colocado','','2026-01-30 19:41:44.004712','2026-01-30 19:42:47.583742',38,NULL,0.00,0),(41,'PERSIANAS',1725126.00,900000.00,0.00,'2026-01-08','efectivo',0,'','','colocado','','2026-01-30 19:52:59.109884','2026-01-30 19:53:37.204672',25,NULL,0.00,0),(42,'1221',2104069.18,570000.00,0.18,'2025-12-16','efectivo',0,'','','colocado','','2026-01-30 19:58:28.531966','2026-01-30 19:59:29.492787',39,NULL,0.00,0),(43,'1237',1662777.16,831388.58,831388.58,'2026-01-22','transferencia',1,'A','180','pendiente','Se aplica retencion de ganancias por $ 12.398.56','2026-01-30 20:00:21.904485','2026-01-30 20:00:21.904513',40,NULL,0.00,0),(44,'MOTOR',580800.00,290400.00,290400.00,'2026-01-26','transferencia',1,'B','121','pendiente','','2026-01-30 20:48:37.477716','2026-01-30 20:48:37.477741',41,NULL,0.00,0),(45,'PVC',3479136.72,1739568.60,1739568.12,NULL,'transferencia',1,'B','117','pendiente','','2026-01-30 20:55:30.446148','2026-02-26 22:36:14.231888',42,'2026-02-26 22:36:14.227902',0.00,0),(46,'1236',4906170.06,2453085.03,2453085.03,'2026-01-19','transferencia',1,'A','177','pendiente','SE APLICAN RETENCIONES','2026-01-30 21:32:49.365531','2026-01-30 21:32:49.365560',29,NULL,0.00,0),(47,'PVC',23439825.99,9126804.00,463888.27,'2025-12-16','transferencia',1,'A','170','pendiente','','2026-01-31 12:28:30.750926','2026-01-31 12:43:47.321264',43,'2026-01-31 12:43:47.310602',0.00,0),(48,'PVC',23439825.98,9126804.00,0.00,NULL,'transferencia',1,'A','170/178','pendiente','','2026-01-31 12:46:12.117955','2026-01-31 15:02:34.902693',43,NULL,0.00,0),(49,'1216',8588612.49,0.00,8588612.49,NULL,'',1,'A','179','pendiente','','2026-01-31 14:46:20.007607','2026-01-31 14:46:20.007656',44,NULL,0.00,0),(50,'1210',894023.02,894023.02,0.00,'2026-01-16','transferencia',1,'B','116','colocado','','2026-01-31 15:00:55.974557','2026-01-31 15:00:55.974583',45,NULL,0.00,0),(51,'1212',3165374.00,1000000.00,0.00,'2025-12-01','efectivo',0,'','','colocado','','2026-02-04 17:20:19.008961','2026-02-04 17:32:30.544870',46,'2026-02-04 17:32:30.529710',0.00,0),(52,'1220',1051755.00,400000.00,0.00,'2025-12-10','efectivo',0,'','','colocado','','2026-02-04 17:46:38.029608','2026-02-04 18:08:09.601215',47,NULL,0.00,0),(53,'pvc',15546596.49,5165200.00,0.00,'2025-12-18','transferencia',1,'A','172','colocado','','2026-02-09 15:02:13.492268','2026-02-09 15:03:23.044927',48,NULL,0.00,0),(54,'PVC',3686950.00,1828450.00,0.00,'2026-01-30','transferencia',1,'B','125','colocado','saldo en dolares usd 1261','2026-02-09 15:09:47.800564','2026-02-26 14:15:46.791052',49,NULL,0.00,0),(55,'PVC',2269375.57,1134696.79,0.00,'2026-01-28','transferencia',1,'B','126','colocado','','2026-02-09 15:13:48.086148','2026-02-26 16:28:07.898857',50,NULL,0.00,0),(56,'1206',374932.00,0.00,374932.00,'2026-01-26','',1,'NC','115','colocado','','2026-02-09 15:48:46.042340','2026-02-09 15:48:46.042383',10,NULL,0.00,0),(57,'HUMBERTO',2800000.00,1425000.00,0.00,'2025-12-03','efectivo',0,'','','colocado','','2026-02-23 16:50:50.599921','2026-02-23 16:51:45.981933',51,NULL,0.00,0),(58,'1226',1588480.60,700000.00,0.60,'2026-01-02','efectivo',0,'','','colocado','','2026-02-23 17:08:04.870751','2026-02-23 17:09:00.323252',52,NULL,0.00,0),(59,'1245',2118990.72,1060000.00,1058990.72,'2026-01-30','transferencia',1,'A','182','pendiente','','2026-02-23 19:33:45.854170','2026-02-23 19:33:45.854238',53,NULL,0.00,0),(60,'1247',1313048.44,656524.22,656524.22,'2026-02-06','',1,'B','129','pendiente','','2026-02-23 19:39:11.646850','2026-02-23 19:39:11.646886',54,NULL,0.00,0),(61,'1248',1543197.70,772000.00,771197.70,'2026-02-05','transferencia',1,'B','127','pendiente','','2026-02-23 19:43:17.584419','2026-02-23 19:43:17.584459',55,NULL,0.00,0),(62,'1250',725000.00,360000.00,365000.00,'2026-01-28','efectivo',0,'','','pendiente','','2026-02-23 19:46:51.064961','2026-02-23 19:46:51.066552',56,NULL,0.00,0),(63,'1251',758000.00,380000.00,378000.00,'2026-01-29','efectivo',0,'','','pendiente','','2026-02-23 19:50:38.032825','2026-02-23 19:50:38.032866',57,NULL,0.00,0),(64,'1252',1191725.00,550000.00,641725.00,'2026-02-09','efectivo',0,'','','pendiente','','2026-02-23 19:55:10.786045','2026-02-23 19:55:10.786083',58,NULL,0.00,0),(65,'1253',1532615.00,772615.00,760000.00,'2026-02-09','efectivo',0,'','','pendiente','','2026-02-23 19:59:11.188328','2026-02-23 19:59:11.188372',59,NULL,0.00,0),(66,'1254',5104331.76,2552000.00,2552331.76,'2026-02-10','transferencia',1,'A','184','pendiente','','2026-02-23 20:08:59.042213','2026-02-23 20:08:59.042253',60,NULL,0.00,0),(67,'1255',990952.00,500000.00,490952.00,'2026-02-11','efectivo',0,'','','pendiente','','2026-02-24 12:20:50.236869','2026-02-24 12:20:50.236923',61,NULL,0.00,0),(68,'1256',1431719.00,600000.00,831719.00,'2026-02-11','efectivo',0,'','','pendiente','','2026-02-24 12:25:29.714961','2026-02-24 12:25:29.715013',62,NULL,0.00,0),(69,'1257',2228000.00,1114000.00,1114000.00,'2026-02-11','efectivo',0,'','','pendiente','','2026-02-24 12:29:52.411710','2026-02-24 12:29:52.411734',63,NULL,0.00,0),(70,'1259',1783000.00,825000.00,958000.00,'2026-02-12','efectivo',0,'','','pendiente','','2026-02-24 12:36:19.513274','2026-02-24 12:36:19.513317',64,NULL,0.00,0),(71,'1260',3200000.00,1600000.00,1600000.00,'2026-02-06','efectivo',0,'','','pendiente','','2026-02-24 12:45:38.900242','2026-02-24 12:45:38.900265',65,NULL,0.00,0),(72,'????',2350000.00,2350000.00,0.00,NULL,'transferencia',1,'A','185','pendiente','','2026-02-24 12:51:21.019598','2026-02-24 12:54:04.620858',66,NULL,0.00,0),(73,'PERSIANA',580800.00,290400.00,290400.00,'2026-01-26','transferencia',1,'B','121','pendiente','','2026-02-24 12:58:59.069729','2026-02-26 14:05:28.592567',41,NULL,0.00,0),(74,'1249',1648854.90,825000.00,823854.90,'2026-02-05','transferencia',1,'B','128','pendiente','','2026-02-24 13:08:18.698974','2026-02-24 13:08:18.699012',67,NULL,0.00,0),(75,'.',2400000.00,1200000.00,1200000.00,'2026-02-16','efectivo',0,'','','pendiente','','2026-02-24 13:17:36.010349','2026-02-24 13:17:36.010385',68,NULL,0.00,0),(76,'PVC',3479136.00,1739568.00,1739568.00,'2026-01-15','transferencia',1,'B','117','pendiente','','2026-01-15 03:00:00.000000','2026-02-26 23:41:18.645500',69,NULL,0.00,0),(77,'01',10.00,5.00,5.00,'2026-02-25','efectivo',1,'','','pendiente','','2026-02-26 22:50:26.911296','2026-02-26 22:50:48.023708',42,'2026-02-26 22:50:48.013607',0.00,0);
/*!40000 ALTER TABLE `comercial_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_provincia`
--

DROP TABLE IF EXISTS `core_provincia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_provincia` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `codigo` varchar(10) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_provincia`
--

LOCK TABLES `core_provincia` WRITE;
/*!40000 ALTER TABLE `core_provincia` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_provincia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-01-15 14:32:44.835840','1','Proveedores',1,'[{\"added\": {}}]',15,2),(2,'2026-01-15 14:34:08.855188','1','Proveedores',2,'[{\"changed\": {\"fields\": [\"Descripcion\"]}}]',15,2),(3,'2026-01-15 15:07:38.199987','5','Pedido 1173 - DANIEL MONTIEL',3,'',11,2),(4,'2026-01-15 15:07:38.205394','4','Pedido 1197 - VIVIANA P',3,'',11,2),(5,'2026-01-15 15:07:38.209046','3','Pedido 1196 - PAOLA LORENA BARRA SANTAMARIA',3,'',11,2),(6,'2026-01-15 15:07:38.212439','2','Pedido 1195 - VALENTINA CIARLIERO',3,'',11,2),(7,'2026-01-15 15:07:38.216945','1','Pedido 1194 - MARA FINCIC',3,'',11,2),(8,'2026-01-16 18:45:09.538774','2','Compra 01 - LUXE PERFILES (Proveedores)',3,'',14,2),(9,'2026-01-16 19:52:20.191699','6','DANIEL MONTIEL',3,'',12,2),(10,'2026-01-16 19:52:20.196967','5','VIVIANA P',3,'',12,2),(11,'2026-01-16 19:52:20.205503','4','PAOLA LORENA BARRA SANTAMARIA',3,'',12,2),(12,'2026-01-16 19:52:20.212033','3','VALENTINA CIARLIERO',3,'',12,2),(13,'2026-01-16 19:52:20.216525','2','MARA FINCIC',3,'',12,2),(14,'2026-01-16 19:52:20.221098','1','Test Test',3,'',12,2);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(12,'comercial','cliente'),(14,'comercial','compra'),(13,'comercial','cuenta'),(20,'comercial','pagoventa'),(29,'comercial','percepcion'),(28,'comercial','retencion'),(21,'comercial','subtipocuenta'),(15,'comercial','tipocuenta'),(22,'comercial','tipogasto'),(11,'comercial','venta'),(5,'contenttypes','contenttype'),(10,'core','provincia'),(16,'facturacion','factura'),(19,'facturacion','facturaitem'),(18,'facturacion','libroivaventas'),(17,'facturacion','puntoventa'),(7,'productos','cotizacion'),(9,'productos','cotizacionitem'),(8,'productos','producto'),(25,'security','auditlog'),(27,'security','backup'),(24,'security','ipblacklist'),(23,'security','loginattempt'),(26,'security','securitysettings'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-11-18 12:32:23.658977'),(2,'auth','0001_initial','2025-11-18 12:32:25.415501'),(3,'admin','0001_initial','2025-11-18 12:32:25.804443'),(4,'admin','0002_logentry_remove_auto_add','2025-11-18 12:32:25.824530'),(5,'admin','0003_logentry_add_action_flag_choices','2025-11-18 12:32:25.842309'),(6,'contenttypes','0002_remove_content_type_name','2025-11-18 12:32:26.476402'),(7,'auth','0002_alter_permission_name_max_length','2025-11-18 12:32:26.668374'),(8,'auth','0003_alter_user_email_max_length','2025-11-18 12:32:26.810723'),(9,'auth','0004_alter_user_username_opts','2025-11-18 12:32:26.825385'),(10,'auth','0005_alter_user_last_login_null','2025-11-18 12:32:26.971368'),(11,'auth','0006_require_contenttypes_0002','2025-11-18 12:32:26.978516'),(12,'auth','0007_alter_validators_add_error_messages','2025-11-18 12:32:26.995851'),(13,'auth','0008_alter_user_username_max_length','2025-11-18 12:32:27.121840'),(14,'auth','0009_alter_user_last_name_max_length','2025-11-18 12:32:27.349679'),(15,'auth','0010_alter_group_name_max_length','2025-11-18 12:32:27.549115'),(16,'auth','0011_update_proxy_permissions','2025-11-18 12:32:27.585173'),(17,'auth','0012_alter_user_first_name_max_length','2025-11-18 12:32:27.735795'),(18,'productos','0001_initial','2025-11-18 12:32:28.203934'),(19,'productos','0002_alter_producto_categoria','2025-11-18 12:32:28.217118'),(20,'sessions','0001_initial','2025-11-18 12:32:28.314987'),(21,'productos','0003_add_formula_field','2025-11-18 21:50:48.101495'),(22,'comercial','0001_initial','2025-11-27 18:24:27.869886'),(23,'core','0001_initial','2025-11-27 18:24:27.913981'),(24,'comercial','0002_remove_venta_monto_cobrado_cliente_condicion_iva_and_more','2026-01-28 17:13:35.408254'),(25,'productos','0004_producto_alicuota_iva','2026-01-28 17:13:35.875622'),(26,'facturacion','0001_initial','2026-01-28 17:13:37.748606'),(27,'productos','0005_cotizacion_cliente_cotizacionitem_cantidad','2026-01-28 17:13:38.485261'),(28,'productos','0006_cotizacion_estado','2026-01-28 17:13:38.800810'),(29,'comercial','0003_pagoventa','2026-01-30 16:54:55.411526'),(30,'comercial','0004_cliente_deleted_at_compra_deleted_at_and_more','2026-01-30 16:54:56.311019'),(31,'comercial','0005_tipocuenta_deleted_at_subtipocuenta','2026-01-30 16:54:56.821207'),(34,'productos','0007_cotizacion_deleted_at','2026-01-30 16:56:40.310957'),(35,'comercial','0006_tipogasto_delete_subtipocuenta_compra_tipo_gasto','2026-01-30 17:21:30.307811'),(36,'comercial','0008_rename_subtipocuenta_to_tipogasto','2026-01-30 17:21:30.864061'),(37,'comercial','0007_compra_tipo_gasto','2026-01-30 17:23:00.544595'),(38,'comercial','0009_merge_20260130_1421','2026-01-30 17:23:01.337216'),(39,'comercial','0010_alter_tipogasto_table','2026-01-30 17:28:47.520730'),(40,'comercial','0009_pagoventa_numero_factura_alter_tipogasto_table','2026-02-03 11:30:50.841408'),(41,'comercial','0010_venta_monto_retenciones_venta_tiene_retenciones','2026-02-03 11:30:51.139886'),(42,'comercial','0011_merge_20260203_0830','2026-02-03 11:30:51.144272'),(43,'productos','0008_delete_cotizaciones','2026-02-03 11:30:51.294958'),(44,'comercial','0011_retencion_percepcion','2026-02-17 15:29:34.998987'),(45,'comercial','0012_merge_20260217_1229','2026-02-17 15:29:35.003803'),(46,'security','0001_initial','2026-02-17 15:29:35.966600'),(47,'security','0002_backup','2026-02-17 15:29:36.276609');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('3o6p99ui7k11r0xchdqb8qaycf2fpyxf','.eJxdkEFuwyAQRe_Cto0FuHaNl9l31z0aYKhpCViAo1ZR7l7sJFXSHXrz3xczJyJhKZNcMibpDBkJJ8_3TIH-wrAOzCeEj9joGEpyqlkjzXWam7do0O-v2YeCCfK02qwfhGGtYKDbVgxGq1b31nS0U1S_CsoodrwOlOJMifq2jENnLSgj1DDUUg-5SNDFHV35WX9Keb-jfMfEO3sZaT8y1vCW9qJ7onSktCoJ55gKSut8STGT8USKm6OMMybQLoZac8RQINewRT2BNJgNkjEs3t9QXaHADW2-XlZpO9iFau8qwTuC1TFRbu0Prq0rLOmPHeo9ozy48A_A9wWcz7_A9Y10:1vt4fT:9Y_rkCrfviXA10oqPKIEL32L0m59Gfv-QTQsJppUrDQ','2026-02-19 15:06:11.292011'),('3z1mqwnvwbtm9hp8xi0z6kaibfhdmxtf','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1viF1g:2pCjyZVzcY82h_HpwBa7n9YfYfabpOkFQyilfPLafVs','2026-02-03 16:56:20.793182'),('47pe3jx945b5iiikryxdas33sm3xjb8w','.eJxVjrEOwjAQQ_8lKzS6S0hoMrKzsUd3SUoLVSu1KRJC_DutxACb5WdbfolAS2nDMucpdEl4ocT-12OK9zxsIN1ouI4yjkOZOpZbRH7pLM9jyv3pm_0baGlutzba2iXUDilq7eoUWUfbJAOGIR4dIGSjVsCskN2qG1RkmoY4Oa7rdbSnuQSKpXt05bk9BWUrUJUyF7TeHLw2Ep2yaHYAHkC8P3Y-ROc:1vvI9j:a1Fm9RV9NgMD1FyF_8rvdzD9N14A9CiHHZ7OpmrSm2k','2026-02-25 17:54:35.296786'),('51hhvgyrc2v1271iq42qrbvpbgbks5kg','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vRVMk:lMh52XaGeT9yxhXuNSbY3Pa_rjCzV3C4VW79tYJ3Cx4','2025-12-19 12:56:54.998496'),('5hbspzle6uccoafe7d4m8m90jvq0mzwt','.eJxVjsEOgjAQRP-lV6XZbmlte_TuzTvZbUFQAgkUE2P8dyHhoLfJvJnJvEVFS26rZa6nqksiCBTHX48pPuphA-lOw22UcRzy1LHcInKns7yMqe7Pe_ZvoKW53drKOp-U9oqi1t6lyDraJhkwDPHkQUFtcAXMqNivulFIpmmIk2fn1tGe5lxRzN2zy6_tKaAtAAvUV2VDqQKepDVQojsABADx-QJ110Tj:1vuYzw:bhHmFAP5qDu-6obJeaIV1PcNmTNCQ7rgzIqeWClbm2k','2026-02-23 17:41:28.235641'),('60yp5pxzrxmy3b4zxh3iuajmg9b9ml1p','.eJxVjrEOwjAQQ_8lKzS6S0hIMrKzsUd3SUsLVSu1KRJC_DutxACb5WdbfolIS2njMtdT7LIIQon9r8eU7vWwgXyj4TrKNA5l6lhuEfmlszyPue5P3-zfQEtzu7XROp9Re6SktXc5sU62yQYMQzp6QKiNWgGzQvarblCRaRri7Nm5dbSnuURKpXt05bk9BWUrUBW6C5pwsAFBOmcM6B1AABDvD3ZLROc:1vsjkh:wC0ta5ItE5zhSp3qxPx6X3ah-z9EXJiSUX-0i1Gg3Vg','2026-02-18 16:46:11.071291'),('6b83gdct61kd1fzhvz5azs6hi1ytna5v','.eJxVjLsOgjAUht-lq9KcnrZYGN3d3MnpTVACCS0mxvjuloRBh3_4b9-bdbTmvltTWLrBs5YpdvzNLLlHmLbC32m6zdzNU14Gy7cJ39vEL7MP43nf_gF6Sn15R2HQ1boICbWQwovYwEnZRkUbhKLGRB9VY4w1oFGiIIBQo7MerAqnAh0p5Y5cHp5DfhUkAtYVYIXyitAKaEFzpaVEeYBigH2-RplEOA:1vucFp:cBfOaPoq9zCJRlzAye5C_8W7vD_NN07L8xuW0dcFwCY','2026-02-23 21:10:05.562072'),('7jzdrpf4uxtx6e1jgx6yq8wfp3ol3zn7','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vlW9H:VujHSkg59NO0NgtBZOrz-W8KobzbfPPFkW8GxHpvbiI','2026-02-12 17:49:43.585043'),('8zew4kq6jv7bs1irb6qpdntnt9qmxsis','.eJxdj8FuwyAQRP-Fc2QZW3ZNjr33G9AuLDUJZiPAUaTI_17cJFLa047ezI40d6FhLbNeMyXtrTiKThzeGYI5U9wNe4L4zY3hWJLHZo80Tzc3X2wpfD6zfwpmyPP-LcdJWdkrCabv1WQN9mZ0dmgHbM2HamVLQ1cNxE6iqtrJDgbnAK3CaaqliS6cCmnnQ0mcxfEuFqonriEcBETPL138hbVZKRb4HfWgJvhK6I1QLmBZX_fgiy11H-vFx38Abg-wbT8fTWn_:1vnxUB:YFT2rMhrds3ET_6lDzPX1xFLOt9AHAsxUcWL2VRfIB4','2026-02-19 11:25:23.024421'),('9wcygt9pvnzg4af1dc28l3i94dx6r910','.eJxVjD0PgkAQRP_Ltcplb1ng7kp7O3uy9yUogQQOE2P870JiocU0M2_eS7S85q5dlzi3fRBWkDj-do79PY77EG48XifppzHPvZM7Ir_rIs9TiMPpy_4JOl667Z2URl9XW5CxUqUKKhloyBlKLipio1NIZLR2GiosUTFArNG7AI5is0kHXnLLPvePPj83JQLWBWCB5UU1FsmSkaomIn0AsADi_QFIO0RS:1vuZft:lnZE6IRx-3SiSn-HA_Rc_vd9CRsOssUfssNPFt0d6Oc','2026-02-23 18:24:49.526253'),('b0zkszbpl0hearbatee2muusalx93jfa','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vWu5Q:tYAc03h-L6mXcD19-WiHiLqQs8fwRh02k7hrHZOR-mM','2026-01-03 10:21:20.274819'),('bi492qabhj3r3l5wsmsiyhwrczxr7uh1','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vRXN9:z70Y--SnhOZ5z6DcPQkmmcNKWz9Bi56vz4IPRoZKb9g','2025-12-19 15:05:27.785531'),('csw004psa2lnegbzq12eaqst654936hr','.eJxVkMtuwyAQRf-FbRNrwLFrvOy-u-6qCg2vmpZABDhqFeXfi92kcnfo3McwcyEC5zKJOZsknCYjYWS3ZRLVpwmLoD8wvMdGxVCSk81iaW5qbp6jNv7p5v1XMGGeljTtB65pyymqtuWDVrJVvdUddBLUIwcKpmNVkJJRyevbUoadtSg1l8NQSz3mIlAVd3ble_kpsH4PbM_6F2Bj146HQ8M49MPhAWAEqJFkTjEVI6zzJcVMxgsp7hRFPJmEysVQa84mFMzVbI2aUGiTtdm0A_2T6ioFt4O7Kq19al5K1gOG2fsdUd5VYjbE1KyOYp12Z2vW1pXmVNkrkR6DiuRtR471ylEcXbhbbwC_fsH1-gNuQ5AR:1vvRVY:WOMURCm6Wk8ZiS18dSkUrrys-K-exvklF6qL2AugyEA','2026-02-26 03:53:44.781929'),('fxnh2us237zywba1jfx4z5p3zw0brijm','.eJxVkMluwyAQht-FaxOLxXaMj7331ltVoWGraQlYgKNWUd692E2iVOKAvn-BmTMSsJRJLNkk4TQaEUW7RyZBfZmwCvoTwkdsVAwlOdmsluaq5uYlauOfr95_BRPkaU2TfuCaME5AMcYHrSRTvdUd7iRWB44JNh2tgpSUSF7vllDorAWpuRyGWuohFwGquJMrP-tPMe33mO4peyV8bNuRkaYjLcOHJ4xHjGskmTmmYoR1vqSY0XhGxc1RxNkkUC6GWnMyoUCuZmvUBEKbrM29ndRzl-ooBR4ktkpbn1rWkm2BYfF-h5R3lZgHYmpWR7G9dmNb1taRllTZG5IegorofYeOdctRHF24Wa8Avv_A5fILZJeQBA:1vubr5:6jCmnatOqgRQsrO8l0bfzdaYQli6ErdFaDZTlNPlpeE','2026-02-23 20:44:31.753344'),('i24khtid1obhrlp2bp3mt6gufbraqrky','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vRXNA:-DS57eQPTP7duARiZ-m2nWqyQjPg706ZCINfrMa4txs','2025-12-19 15:05:28.765038'),('iuw73sdbv7zi55qkomgsj36zuful3q5n','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vQmGD:LJswJtUU9GQzXiZHiISSirYgBlzUIf3ew0cQ5YdpwCA','2025-12-17 12:47:09.796262'),('jtnda1hkuygtvhmxyea2rxvu7tlokd2b','.eJxVjjEPwiAUhP8Lq5Y8oCB0dHdzJ-9BsWjTJi01Mcb_bpt00O1y393l3szjUjq_zO3kc2QNk-z46xGGRztsIN5xuI08jEOZMvEtwnc688sY2_68Z_8GOpy7rS2MdVEoJzAo5WwMpIJJUYMmCCcHAlotV0AkBblVJyFRp4QUHVm7jvY4F4-h5Gcur-0pSFOBrGR9FaqRptEnXrtaOXMAaADY5wt2iUTx:1vusRG:urGIRiiVHIr1dBD9vKpmWkSJ52VwFEgjkpACes3agHA','2026-02-24 14:26:58.215419'),('ml4rh9y20x27dnjq7ei63ilvsfrri6xb','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vLNcC:FEDvWpb5Y5bXm0zkm3RbY6nDC8i6wnirpQKI-gpd8IQ','2025-12-02 15:27:32.292517'),('mwc4oqulhmtkilhpniref41jlyqtmn19','.eJxVkM1OwzAQhN_FV9po7ZDUyZE7N24IWes_YrDsynYqQdV3Z6MWVG72fDOj0Z6ZwrUtaq2uqGDZzATb3WsazadLG7AfmN5zZ3JqJehus3Q3WrvnbF18unn_FSxYly3NRzlZ3k8cTd9P0hrdm9HbAQYN5jABBzcIAloLrid6ey5w8B61nbSUVBqxNoWmhVNoX9tSEOMexF4cXgBm3s9i6EBK-Xh4oD8ARYo75tKc8iG2kiubz8w7s6Cyrlp31wGc3FdEgxuyOa0x7piJwSUq2E5zVQp-56RqNgHjr-YoYbM6kfUv2cIxK09z10LaK9MRk8ns7XL5AdZ2eRI:1vvlTx:jshQkxUesFcpThK01sXclyt4JvMGrBWe9hXPsGH7sB0','2026-02-27 01:13:25.145782'),('ncbpmm4qe6fwrrr91hs64on51vd19k4u','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vWu5R:NiaHgCtRDnc598PILbxKomTeZyNp36Q93On4ny-HitI','2026-01-03 10:21:21.057175'),('o1o58ho5gdy40il90cuq0ja3v7sppg02','.eJxdkMtuwyAQRf-FbRMLcOwaL7vvrruqQgMMMakDEcZRqyj_3nEeVVOJBTr3oZk5MQ1zGfQ8YdbBsZ5JtvrLDNhPjIvgdhC3qbIplhxMtViqmzpVr8nh-HLzPhQMMA1LWrSdcqJWAmxdq85ZU9vWu4Y3httnxQXHRpJgjBRG0d8LCY33YJwyXUelI0xFgy3hGMr3MimX7ZrLtVBvYtPTazaVbHnX1U-c95xTJOMh5YLah7HkNLH-xEo4JJ0OmMGGFKlmS7UkrZhHO4B2ODlkfZzH8Y5ohQJ3dMnbGWOBy8HehfhYMTsGInghVx9SxiV9XIwPWU8rzPmX7emeSe9D_Afg6wrO5x-Kr4zb:1vt4nu:ubVK5s6yFpXxOdHYdrFqTqe0a4zzW9rva_O5Vor1QV0','2026-02-19 15:14:54.381402'),('oik964dnxfcf5vp5odwur3he2z1pn1eh','.eJxVjsEOgjAQRP-lV6XZbQu0PXr35r3ZbUFQAgkUE2P8dyHxoLfJvJnJvESgNXdhXZo59El4ocTx12OK92bcQbrReJ1knMY89yz3iPzSRZ6n1Aynb_ZvoKOl29tYWZdQO6SotbMpso5Vm0ooGWLtAKEp1QaYFbLbdIuKyrYlTo6t3UYHWnKgmPtHn5_7U1BVAapQ5oLoVe3RSG2cqe0BwAOI9wd18kTp:1vuqZO:KqtXLDhzTc55IF2S5AFnC5SpsybuO5Br0WXlHLwspxU','2026-02-24 12:27:14.489905'),('p571x9fg4agax4it6a9gacp43a7lbyjo','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vLO3V:MIoqbkKOAUsfzu5_RLdm4-K-pZtE4a076Ja5lSMmmss','2025-12-02 15:55:45.817922'),('q1gxdgx0iew01bkhxvukimrc8rvmolex','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vTlex:ptwsNsMLHg6nyfJkfZDx8x066caQpfKp5AY6JAfxxMQ','2025-12-25 18:45:03.935118'),('qjlpqgtddyhcplxhh3masvr32rwtmdt8','.eJxVjsEKwjAQRP8lV23YJE2a9Ojdm_ewm7Q2WlpoUkHEf7cFDwpzWObNDvNiHtcy-DV3i0-RtUyy469HGO7dtIN4w-k68zBPZUnE9wj_0szPc-zG0zf7VzBgHvZvYayLQjmBQSlnYyAVTB81aILQOBDQabkBIinIbXcvJOq-R4qOrN1KR8zFYyjpkcpzXwrSVCArqS9Ct_Umw-umMeAOAC0Ae38Adq5E8Q:1vvH58:G2ecauxoY_AdLm2N2ytZraXvBnz0lyNwhQ_8bHxvNus','2026-02-25 16:45:46.496405'),('tbzlmthiyo0v8bttgv8ixcb4oz4zwrkg','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vP74T:H9HBe6s3BKrojHsCuJmKLvRB2OrWs_eaBEqfKtym19s','2025-12-12 22:36:09.078730'),('tzwb6u5jncnonodvtu8djzcsph5dgjor','.eJxVkMtOxCAUht-FrTMNUKmlS_fu3BlDDjeLMtAAnWgm8-7S2jGdHfn-y-GcCxIwl1HM2SThNBoQRYc9k6C-TFgE_QnhIzYqhpKcbBZLs6m5eYna-OfNe1cwQh6XNOl6rknLCai25b1WslWd1QwzidUTxwQbRqsgJSWS17clFJi1IDWXfV9LPeQiQBV3duVn-Smm3RHTI2WvhA2PdGj7hveM8u4B4wHjGklmiqkYYZ0vKWY0XFBxUxRxMgmUi6HWnE0okKvZGjWC0CZrs2vH5F-qqxS4G1yltU_NS8l6wDB7f0DKu0rMjpia1VGs025szdq60pwqe0PSQ1ARvR_QqV45ipMLN-sG4PsPXK-_exSQHw:1vvH27:pSmulQzlZEFpqi57wYA_4-tLOlKw4CNKuUj80vZAfaI','2026-02-25 16:42:39.050943'),('umathgh7g446726vjh2rx9hsnosbbmw3','.eJxVjrEOwjAQQ_8lKzS6S0hIMrKzsVd3SUsLVSs1KRJC_DutxACb5WdbfomaltLVS27muk8iCCX2vx5TvDfjBtKNxusk4zSWuWe5ReSXZnmeUjOcvtm_gY5yt7XROp9Qe6SotXcpso62TQYMQzx6QGiMWgGzQvarblGRaVvi5Nm5dXSgXGqKpX_05bk9BWUrUJXSFzwErYOx0hmLzu8AAoB4fwB2aETw:1vuX0W:5sfcjJvjLpIV-Yasvh665HrrzkWQOTOvM8Z3DZslfTM','2026-02-23 15:33:56.987495'),('xig18kjs096aoo3lbmk44iwxcl88jfpo','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vLNnQ:L0et8vKSULenJD2FDAu6MHyK6-X0hIdbQuaCxSqmCU4','2025-12-02 15:39:08.016845'),('xktg2m3dvi9oquu4yqb34utc25mxq053','.eJxVjDEOwyAQBP9CHSHAhw0p0_sN6A6O4CTCkrGrKH-PLblIim12ZvctAm5rCVvjJUxJXAWIy29HGJ9cD5AeWO-zjHNdl4nkociTNjnOiV-30_07KNjKvs7amdjbPQaN1Z1OOns1AHnIxBrQu5wyeOfIKWs6o1Ep7k2kpAh4EJ8vy2o3aA:1vnhHk:wkdOx8B9M4fLs65aUqLXQrjxBMijtu_7GfzXPfy-yJM','2026-02-18 18:07:28.887609'),('y5y09xf1kyenvtt4315mqy7t1x9pwele','.eJxdkEtvwyAQhP8L1zoWj2CDj7n31jtaHq5pMUQGR4mi_PfiJpHSnnb0zexKs1ekYC2TWrNblLdoQBQ1r0yD-XZxM-wXxM_UmhTL4nW7RdqHm9v3ZF04PLJ_DkyQp22bdEJawiQBw5gU1mhmutFyzDU2vcQEO06roTUlWlY9Egp8HEFbqYWoRxd3TEtxavShLCmj4YpmV0dcQ2gQRJ-euvhjUmZ1scBvqTs1wVfiXojLBWxSpy34ZHPtl9Ts4z8A5zu4NShALgpM8SdfLtvLMO12mO5I_0H4wMRA9y0X_Z7RN4wHjNHtB7D8duo:1vsN9c:5YXz8LXO_6ADJT4k_eg696LaOC9JbTvGVLWG8-sDrQo','2026-02-17 16:38:24.646063'),('yaikr70gec9vwpsu0k95o4wskeoqjkph','.eJxdkEFuwyAQRe_Cto0FpjjGy-676x4NMNS0DliAo1ZR7l7sJFXSHXrz3xczJ6JgKaNaMiblLRlIS57vmQbzhWEd2E8IH7ExMZTkdbNGmus0N2_R4vR6zT4UjJDH1WZdLy3jkoHhXPbWaG46ZwUVmpq9pIyiaOtA65ZpWd-OtSCcA22l7vtaOkEuCkzxR19-1p_SttvRdsfkO-sHsR9eZLMXnAv-ROlAaVUSzjEVVM5PJcVMhhMpfo4qzpjA-BhqzRFDgVzDDs0IymK2SIawTNMN1RUK3NDmm2WVtoNdqJl8JXhHsDo2qq39wXV1hSX9sUO9Z1QHH_4B-L6A8_kX06SNig:1vt9Dh:0Hhf0Jsyl49vVwz1pXq_SuqFjuCflaaNySudV2C7qoA','2026-02-19 19:57:49.758416'),('ybhoafvl4b6nb70993l36251l0debax6','.eJxVkEtrAyEUhf-L2yaDj45Rl913l10ocn11bEWDOoES8t_rkFDS3eV85xwO94o0rH3Ra_NVR4cUomj3rBmw3z5vwH1B_iyTLbnXaKbNMj1om96L8-nt4f1XsEBbtjThQjrCJAHLmBTOGmZ5cDOeDbYHiQn2Mx3AGEqMHHcgFOYQwDhphBilCVrXYHu8xP6zLcWU7zHdU34kXL0eFGOTIIJx-YKxwnhEqj-X2r0OMfVaGlJXFLxdQDvfnH_qwGS472gM7oBUXlPaIZuiz6Nge81d8YO6oi9D_nP1eC46jGlrHdoJmQTZFvRxu_0CqapxtQ:1vveWU:3HKiuXLf4RD8AUSDhd2Xlkxr9AaZF_y7_Mt0Hr0vUT4','2026-02-26 17:47:34.105434'),('ymp8hkdc905sfvg6e28ugrfpp0uc4xqk','.eJxVj8tuwyAQRf-FtWUBll3jZfb5g0pogKEmwRDxqCJF-ffg1pXS3ejcM1czDyKhllXWjEk6QxbCSffOFOgrhj0wFwhfsdcxlORUvyv9keb-HA360-H-K1ghr_s2m2Zh2CAY6GEQs9Fq0JM1Ix0V1R-CMoojb4FSnCnRZss4jNaCMkLNcytNeIupoLTOlxQzWR5kw3ycDJ-VUssiWTjlU0eKu0WpK4YCP3-F6n1HtHeN4BvBXMBE-b2Lrao1be3BKDcX_pQDwP0XPJ8vd3hnQw:1vnIog:1-0_gUWGwbtNNKmij0Koiel7IW1GDMC23CZfQy2s_N8','2026-02-17 15:59:50.400909'),('yugl2o1wq8vbd4i0vrn23zgt0dgw529p','.eJxdkMtuwyAQRf-FbR0LsPzAy-y76x4NMMS0DliAo1ZR_r04jyrpbnTuvfM6EwlrnuSaMEpnyEg4qZ6ZAv2FfhPMJ_hDqHXwOTpVb5b6rqb6PRic93fvS4MJ0rSlWTcIwxrBQDeNGIxWje6saWmrqO4FZRRbXgSlOFOi1JZxaK0FZYQahtI04hJiRmndnGNIZDyT7JYgw4IRtAu-jDlAykWqiEU9gTSYDJLRr_P8QGWfDA90zesVfYbr9TeqZ1cIPhEsGRPkaTO-ZC3ovMY_dizPCfLo_D8A3zdwqchc5suScieXf7Z_U97tKN-x_oN1I6Mj6-pW9A3r3igdKSWXX0JUjXo:1vsNeT:5BHD9pQqKFWCxFRnQgTdHK4Ajd2eUTIs-bujTBH6haA','2026-02-17 17:10:17.000607'),('z2kumg00625re5kdflpei918kt8jbeq5','.eJxVUE1PxCAQ_S9c3W2A2m7p0bs3b8aQAQaLEtgA3UQ3-9-duqvR28z7yss7Mw1rW_Rasejg2Mwk2_3FDNh3TBvh3iC95s7m1Eow3SbpbmztHrPD-HDT_gtYoC6bW4yTcqJXAmzfq8lZ09vRu4EPhtuD4oLjIIkwRgqj6PZCwuA9GKfMNFFohNo02BZOoX1sTbkc91zu5eGJ81n2s5w6IQ9qvL-jn3OyFDzm0lD7EFvJlc1n5tEuoB1Wh38yuCD1laLCDdic1hh3zMaAiQK2aa5Igc-cdM02QPzBkBwu6xNJf50tHLP2VHcthD0zEyHZzF4uO7atth6_NyJHsNCQ4ltZ8fIFpvaDsg:1vvldg:4VMBDaS6a0iq_QYMxEeK5CLr2sReYvwvPCHFGiMDU68','2026-02-27 01:23:28.335072'),('zxw2gkmayfn3043tn868f0teojzsmbqn','.eJxVjMEOwiAQRP-FsyEshAoevfsNZJcFqRpISnsy_rsl6UFvk3lv5i0CbmsJW09LmFlchBan344wPlMdgB9Y703GVtdlJjkUedAub43T63q4fwcFexlrmJxnMB4wGuMdRzJxymyVJRXPXoFKVu-ASAP5PWfQaHNGYk_Oic8X2v84AQ:1vP75z:MoPbJbKFPfFt7-cWZCy_f8Gx4G5E9kGsA1l5GKhw8lY','2025-12-12 22:37:43.254124');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturacion_factura`
--

DROP TABLE IF EXISTS `facturacion_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturacion_factura` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo` varchar(1) NOT NULL,
  `numero` int NOT NULL,
  `fecha` date NOT NULL,
  `subtotal_neto` decimal(12,2) NOT NULL,
  `iva_21` decimal(12,2) NOT NULL,
  `iva_105` decimal(12,2) NOT NULL,
  `iva_27` decimal(12,2) NOT NULL,
  `exento` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `cae` varchar(14) NOT NULL,
  `cae_vencimiento` date DEFAULT NULL,
  `estado` varchar(20) NOT NULL,
  `observaciones_afip` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `cliente_id` bigint NOT NULL,
  `punto_venta_id` bigint NOT NULL,
  `venta_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `facturacion_factura_tipo_punto_venta_id_numero_570a0253_uniq` (`tipo`,`punto_venta_id`,`numero`),
  UNIQUE KEY `venta_id` (`venta_id`),
  KEY `facturacion_factura_punto_venta_id_3b8924bb_fk_facturaci` (`punto_venta_id`),
  KEY `facturacion_factura_cliente_id_a467a777_fk_comercial_cliente_id` (`cliente_id`),
  CONSTRAINT `facturacion_factura_cliente_id_a467a777_fk_comercial_cliente_id` FOREIGN KEY (`cliente_id`) REFERENCES `comercial_cliente` (`id`),
  CONSTRAINT `facturacion_factura_punto_venta_id_3b8924bb_fk_facturaci` FOREIGN KEY (`punto_venta_id`) REFERENCES `facturacion_puntoventa` (`id`),
  CONSTRAINT `facturacion_factura_venta_id_abf3f20d_fk_comercial_venta_id` FOREIGN KEY (`venta_id`) REFERENCES `comercial_venta` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturacion_factura`
--

LOCK TABLES `facturacion_factura` WRITE;
/*!40000 ALTER TABLE `facturacion_factura` DISABLE KEYS */;
/*!40000 ALTER TABLE `facturacion_factura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturacion_facturaitem`
--

DROP TABLE IF EXISTS `facturacion_facturaitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturacion_facturaitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(200) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `alicuota_iva` decimal(5,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `iva` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `factura_id` bigint NOT NULL,
  `producto_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `facturacion_facturai_factura_id_5cf164c9_fk_facturaci` (`factura_id`),
  KEY `facturacion_facturai_producto_id_8a3064f1_fk_productos` (`producto_id`),
  CONSTRAINT `facturacion_facturai_factura_id_5cf164c9_fk_facturaci` FOREIGN KEY (`factura_id`) REFERENCES `facturacion_factura` (`id`),
  CONSTRAINT `facturacion_facturai_producto_id_8a3064f1_fk_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos_producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturacion_facturaitem`
--

LOCK TABLES `facturacion_facturaitem` WRITE;
/*!40000 ALTER TABLE `facturacion_facturaitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `facturacion_facturaitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturacion_libroivaventas`
--

DROP TABLE IF EXISTS `facturacion_libroivaventas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturacion_libroivaventas` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `periodo` date NOT NULL,
  `neto_gravado_21` decimal(12,2) NOT NULL,
  `iva_21` decimal(12,2) NOT NULL,
  `neto_gravado_105` decimal(12,2) NOT NULL,
  `iva_105` decimal(12,2) NOT NULL,
  `neto_gravado_27` decimal(12,2) NOT NULL,
  `iva_27` decimal(12,2) NOT NULL,
  `exento` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `factura_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `facturacion_libroiva_factura_id_e459a54b_fk_facturaci` (`factura_id`),
  CONSTRAINT `facturacion_libroiva_factura_id_e459a54b_fk_facturaci` FOREIGN KEY (`factura_id`) REFERENCES `facturacion_factura` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturacion_libroivaventas`
--

LOCK TABLES `facturacion_libroivaventas` WRITE;
/*!40000 ALTER TABLE `facturacion_libroivaventas` DISABLE KEYS */;
/*!40000 ALTER TABLE `facturacion_libroivaventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturacion_puntoventa`
--

DROP TABLE IF EXISTS `facturacion_puntoventa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturacion_puntoventa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturacion_puntoventa`
--

LOCK TABLES `facturacion_puntoventa` WRITE;
/*!40000 ALTER TABLE `facturacion_puntoventa` DISABLE KEYS */;
/*!40000 ALTER TABLE `facturacion_puntoventa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos_producto`
--

DROP TABLE IF EXISTS `productos_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos_producto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `precio_m2` decimal(10,2) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `formula` varchar(20) NOT NULL,
  `alicuota_iva` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos_producto`
--

LOCK TABLES `productos_producto` WRITE;
/*!40000 ALTER TABLE `productos_producto` DISABLE KEYS */;
INSERT INTO `productos_producto` VALUES (1,'Laminado 3+3 (m²)','vidrios',81000.00,1,'2025-11-18 15:12:20.684572','2025-11-19 10:38:36.012704','area',21.00),(2,'DVH 4+9+4 (m²)','vidrios',86000.00,1,'2025-11-18 15:12:20.751745','2025-11-19 10:38:23.685801','area',21.00),(3,'DVH 3+3+9+4 (m²)','vidrios',143000.00,1,'2025-11-18 15:12:20.761233','2025-11-19 10:38:11.755691','area',21.00),(4,'DVH 3+3+9+3+3 (m²)','vidrios',201800.00,1,'2025-11-18 15:12:20.860979','2025-11-19 10:37:55.758698','area',21.00),(5,'Paño fijo Módena blanco (m²)','panos_fijos',24750.00,1,'2025-11-18 15:12:20.945638','2025-11-19 10:56:58.408868','perimetro',21.00),(6,'Paño fijo Módena negro (m²)','panos_fijos',29700.00,1,'2025-11-18 15:12:20.956650','2025-11-19 10:57:10.644790','perimetro',21.00),(7,'Paño fijo A30 blanco (m²)','panos_fijos',35000.00,1,'2025-11-18 15:12:21.046697','2025-11-19 10:38:50.810625','perimetro',21.00),(8,'Paño fijo A30 negro (m²)','panos_fijos',42000.00,1,'2025-11-18 15:12:21.058187','2025-11-19 10:39:25.365849','perimetro',21.00),(9,'Persiana PVC blanco (m²)','persianas',65000.00,1,'2025-11-18 15:12:21.142135','2025-11-19 10:57:29.512594','area',21.00);
/*!40000 ALTER TABLE `productos_producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `security_auditlog`
--

DROP TABLE IF EXISTS `security_auditlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_auditlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(150) NOT NULL,
  `action` varchar(20) NOT NULL,
  `level` varchar(10) NOT NULL,
  `model_name` varchar(100) NOT NULL,
  `object_id` varchar(100) NOT NULL,
  `object_repr` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `user_agent` longtext NOT NULL,
  `path` varchar(500) NOT NULL,
  `method` varchar(10) NOT NULL,
  `changes` json DEFAULT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `security_auditlog_timestamp_1c842a51` (`timestamp`),
  KEY `security_au_timesta_cbae00_idx` (`timestamp` DESC),
  KEY `security_au_user_id_6d8368_idx` (`user_id`,`timestamp` DESC),
  KEY `security_au_action_7867d2_idx` (`action`,`timestamp` DESC),
  CONSTRAINT `security_auditlog_user_id_69f912c9_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=264 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_auditlog`
--

LOCK TABLES `security_auditlog` WRITE;
/*!40000 ALTER TABLE `security_auditlog` DISABLE KEYS */;
INSERT INTO `security_auditlog` VALUES (1,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:30:06.719926',2),(2,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:30:09.168635',2),(3,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:30:19.884953',2),(4,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:30:39.257730',2),(5,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:31:47.355129',2),(6,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:32:03.270591',2),(7,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:41:22.645962',2),(8,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:58:21.678574',2),(9,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:58:44.745636',2),(10,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:58:52.357157',2),(11,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 15:59:10.426503',2),(12,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:07:06.926805',2),(13,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:07:15.252528',2),(14,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:07:21.919021',2),(15,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:09:55.319731',2),(16,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:09:58.009849',2),(17,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-17 16:10:16.984428',2),(18,'admin','CREATE','INFO','','','','POST /login/','190.48.205.77','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-18 15:44:32.071879',2),(19,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-19 13:53:15.245306',2),(20,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:53:39.605470',2),(21,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:53:59.361084',2),(22,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:56:24.553300',2),(23,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:56:42.084545',2),(24,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:56:51.479387',2),(25,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:57:04.737097',2),(26,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 13:57:09.701350',2),(27,'Anonymous','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-19 14:05:54.309724',NULL),(28,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-19 14:06:00.459850',2),(29,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:06:06.444930',2),(30,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:10:34.199507',2),(31,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:11:27.279611',2),(32,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:14:36.385247',2),(33,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:14:46.953596',2),(34,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 14:14:54.369004',2),(35,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-19 18:53:43.886708',2),(36,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-19 18:53:55.035978',2),(37,'Kiara','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 14:26:23.378427',4),(38,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 14:33:43.325240',2),(39,'Kiara','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 14:34:32.214981',4),(40,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 14:40:09.811986',2),(41,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 14:43:00.889654',4),(42,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 14:45:40.947295',4),(43,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 14:46:58.019158',4),(44,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 14:51:45.957865',4),(45,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 14:52:41.474534',4),(46,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 14:53:28.585687',2),(47,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 14:55:15.048070',2),(48,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 14:56:06.719275',4),(49,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/38/eliminar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/38/eliminar/','POST',NULL,'2026-02-23 14:56:07.279488',2),(50,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/10/eliminar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/10/eliminar/','POST',NULL,'2026-02-23 14:56:12.841753',2),(51,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 14:57:07.223956',4),(52,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 14:57:55.793968',4),(53,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 14:58:38.839426',2),(54,'admin','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 14:59:23.272860',2),(55,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/40/eliminar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/40/eliminar/','POST',NULL,'2026-02-23 15:00:08.727209',2),(56,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/39/eliminar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/39/eliminar/','POST',NULL,'2026-02-23 15:00:14.598565',2),(57,'admin','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 15:01:26.530165',2),(58,'admin','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 15:01:34.365442',2),(59,'admin','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 15:02:02.335587',2),(60,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 15:03:37.500692',2),(61,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/41/eliminar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/41/eliminar/','POST',NULL,'2026-02-23 15:05:28.279211',2),(62,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 15:06:06.557977',2),(63,'admin','CREATE','INFO','','','','POST /comercial/cuentas/28/editar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/28/editar/','POST',NULL,'2026-02-23 15:06:35.839832',2),(64,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:06:46.094612',2),(65,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:08:02.504539',4),(66,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:09:53.201163',2),(67,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 15:10:48.265232',4),(68,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:11:53.456080',2),(69,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:11:54.162600',2),(70,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:12:23.891042',2),(71,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:13:58.437141',2),(72,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 15:14:36.664480',2),(73,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:16:20.433692',4),(74,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:17:57.238556',4),(75,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 15:19:51.247456',4),(76,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 15:20:19.499809',4),(77,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:21:45.067202',4),(78,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:22:46.537891',4),(79,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:23:32.778804',4),(80,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:24:22.524899',4),(81,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:26:09.385042',4),(82,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:27:17.678152',4),(83,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:30:07.172403',4),(84,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:31:00.753891',4),(85,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:32:01.910320',4),(86,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 15:34:14.139425',4),(87,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:35:35.410745',4),(88,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:36:48.817935',4),(89,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:38:14.166612',4),(90,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:41:16.656789',4),(91,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 15:42:59.918540',2),(92,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:45:05.838526',4),(93,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:57:04.854602',4),(94,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 15:58:15.027488',4),(95,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 16:00:49.748072',4),(96,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/46/editar/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/46/editar/','POST',NULL,'2026-02-23 16:01:04.600899',4),(97,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 16:02:00.958568',4),(98,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:03:40.885767',4),(99,'Kiara','CREATE','INFO','','','','POST /login/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 16:06:10.104741',4),(100,'Kiara','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-23 16:06:51.333361',4),(101,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 16:07:28.114821',4),(102,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:09:56.433316',4),(103,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:13:49.709828',4),(104,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 16:15:44.199401',4),(105,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:16:58.892087',4),(106,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:18:14.255717',4),(107,'Kiara','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-23 16:19:27.984755',4),(108,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 16:20:30.800168',4),(109,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/20/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/20/pago/','POST',NULL,'2026-02-23 16:32:49.680612',4),(110,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/20/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/20/editar/','POST',NULL,'2026-02-23 16:34:00.314512',4),(111,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/16/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/16/pago/','POST',NULL,'2026-02-23 16:36:06.294997',4),(112,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/16/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/16/editar/','POST',NULL,'2026-02-23 16:36:49.834814',4),(113,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/30/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/30/editar/','POST',NULL,'2026-02-23 16:37:56.849773',4),(114,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/30/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/30/pago/','POST',NULL,'2026-02-23 16:39:13.668942',4),(115,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 16:45:04.017622',4),(116,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 16:50:50.619522',4),(117,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/57/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/57/pago/','POST',NULL,'2026-02-23 16:51:45.989174',4),(118,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/29/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/29/editar/','POST',NULL,'2026-02-23 16:54:21.675079',4),(119,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/29/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/29/pago/','POST',NULL,'2026-02-23 16:55:09.807225',4),(120,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/14/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/14/editar/','POST',NULL,'2026-02-23 16:56:28.280557',4),(121,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/14/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/14/pago/','POST',NULL,'2026-02-23 16:58:57.393799',4),(122,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 17:05:51.013300',4),(123,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 17:08:04.934266',4),(124,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/58/pago/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/58/pago/','POST',NULL,'2026-02-23 17:09:00.350758',4),(125,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/32/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/32/editar/','POST',NULL,'2026-02-23 17:09:48.983991',4),(126,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/32/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/32/editar/','POST',NULL,'2026-02-23 17:12:37.244623',4),(127,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/32/editar/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/32/editar/','POST',NULL,'2026-02-23 17:15:55.458376',4),(128,'Kiara','CREATE','INFO','','','','POST /comercial/compras/nueva/','128.1.179.150','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/compras/nueva/','POST',NULL,'2026-02-23 17:24:48.881022',4),(129,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 18:40:46.448623',2),(130,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 18:40:47.129153',2),(131,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 18:40:56.359650',2),(132,'Kiara','CREATE','INFO','','','','POST /login/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-23 19:21:57.695234',4),(133,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:30:03.829653',4),(134,'admin','CREATE','INFO','','','','POST /comercial/reportes/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-23 19:33:12.559917',2),(135,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:33:45.864795',4),(136,'admin','CREATE','INFO','','','','POST /comercial/reportes/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-23 19:34:00.710698',2),(137,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:37:12.810024',4),(138,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:39:11.662426',4),(139,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:42:13.637773',4),(140,'admin','CREATE','INFO','','','','POST /comercial/reportes/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-23 19:42:53.793966',2),(141,'admin','CREATE','INFO','','','','POST /comercial/reportes/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-23 19:43:00.494942',2),(142,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:43:17.608527',4),(143,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:45:34.506969',4),(144,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:46:51.085891',4),(145,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:49:05.479245',4),(146,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:50:38.042518',4),(147,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:54:01.320395',4),(148,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:55:10.793160',4),(149,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 19:56:43.559995',4),(150,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 19:59:11.200574',4),(151,'Kiara','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-23 20:07:35.141770',4),(152,'Kiara','CREATE','INFO','','','','POST /comercial/ventas/nueva/','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-23 20:08:59.063461',4),(153,'admin','CREATE','INFO','','','','POST /login/','181.238.52.32','Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36','/login/','POST',NULL,'2026-02-24 11:26:56.183745',2),(154,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-24 12:15:51.596828',2),(155,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:19:31.336730',2),(156,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:20:50.268160',2),(157,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:24:11.494319',2),(158,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:25:29.738574',2),(159,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:28:31.656644',2),(160,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:29:52.428909',2),(161,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:34:56.948297',2),(162,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:36:19.572703',2),(163,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:41:42.156154',2),(164,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:45:38.928644',2),(165,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:50:09.906430',2),(166,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:51:21.028460',2),(167,'admin','CREATE','INFO','','','','POST /comercial/ventas/72/editar/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/72/editar/','POST',NULL,'2026-02-24 12:54:04.695541',2),(168,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 12:57:14.299462',2),(169,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 12:58:59.078062',2),(170,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 13:07:18.960256',2),(171,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 13:08:18.717712',2),(172,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 13:15:40.295640',2),(173,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 13:17:36.028552',2),(174,'admin','CREATE','INFO','','','','POST /comercial/clientes/nuevo/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/clientes/nuevo/','POST',NULL,'2026-02-24 13:25:21.177469',2),(175,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-24 13:26:57.194475',2),(176,'admin','CREATE','INFO','','','','POST /login/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-25 15:35:46.469673',2),(177,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-25 15:37:53.299532',2),(178,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-25 15:38:01.887050',2),(179,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-25 15:40:46.309096',2),(180,'admin','CREATE','INFO','','','','POST /login/','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-25 16:54:34.908767',2),(181,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 01:29:06.262746',2),(182,'admin','CREATE','INFO','','','','POST /comercial/cuentas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/cuentas/nueva/','POST',NULL,'2026-02-26 01:35:38.350020',2),(183,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/nuevo/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/nuevo/','POST',NULL,'2026-02-26 01:37:27.220612',2),(184,'admin','CREATE','INFO','','','','POST /comercial/tipos-gasto/42/editar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/tipos-gasto/42/editar/','POST',NULL,'2026-02-26 01:41:25.684125',2),(185,'admin','CREATE','INFO','','','','POST /comercial/compras/75/editar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/compras/75/editar/','POST',NULL,'2026-02-26 01:48:32.607234',2),(186,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 01:51:32.809794',2),(187,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 01:51:55.384890',2),(188,'admin','CREATE','INFO','','','','POST /login/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 13:13:37.797645',2),(189,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 13:16:03.041356',2),(190,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 13:17:05.527616',2),(191,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/editar/','POST',NULL,'2026-02-26 14:04:05.956496',2),(192,'admin','CREATE','INFO','','','','POST /comercial/ventas/73/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/73/editar/','POST',NULL,'2026-02-26 14:05:28.614321',2),(193,'admin','CREATE','INFO','','','','POST /comercial/ventas/54/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/54/editar/','POST',NULL,'2026-02-26 14:15:46.840266',2),(194,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:16:06.900365',2),(195,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:16:15.921840',2),(196,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/editar/','POST',NULL,'2026-02-26 14:18:05.132200',2),(197,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:18:20.505755',2),(198,'admin','CREATE','INFO','','','','POST /login/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 14:33:56.810187',2),(199,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:34:05.966544',2),(200,'admin','CREATE','INFO','','','','POST /login/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 14:40:18.321654',2),(201,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:47:55.148039',2),(202,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 14:57:50.556179',2),(203,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:00:36.895527',2),(204,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:01:58.821598',2),(205,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:03:10.348629',2),(206,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:03:27.900693',2),(207,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:07:49.552792',2),(208,'admin','CREATE','INFO','','','','POST /login/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 15:41:56.708337',2),(209,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:42:41.000904',2),(210,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 15:54:12.758079',2),(211,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/editar/','POST',NULL,'2026-02-26 16:07:08.120752',2),(212,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 16:07:35.812442',2),(213,'admin','CREATE','INFO','','','','POST /comercial/ventas/55/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/55/editar/','POST',NULL,'2026-02-26 16:24:54.730342',2),(214,'admin','CREATE','INFO','','','','POST /comercial/ventas/55/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/55/editar/','POST',NULL,'2026-02-26 16:28:07.916661',2),(215,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/editar/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/editar/','POST',NULL,'2026-02-26 16:29:41.227764',2),(216,'admin','CREATE','INFO','','','','POST /comercial/reportes/','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 16:29:58.097730',2),(217,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 21:57:14.308770',2),(218,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 21:57:37.008246',2),(219,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:09:55.504361',2),(220,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:20:54.763359',2),(221,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:21:26.588457',2),(222,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:21:46.375927',2),(223,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:21:49.974435',2),(224,'admin','CREATE','INFO','','','','POST /comercial/ventas/45/eliminar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/45/eliminar/','POST',NULL,'2026-02-26 22:36:14.244026',2),(225,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:44:59.526749',2),(226,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:45:15.952859',2),(227,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:46:41.537862',2),(228,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:46:50.399614',2),(229,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:46:52.978292',2),(230,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:47:25.242929',2),(231,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/pago/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/pago/','POST',NULL,'2026-02-26 22:49:34.949387',2),(232,'admin','CREATE','INFO','','','','POST /comercial/ventas/nueva/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/nueva/','POST',NULL,'2026-02-26 22:50:26.957595',2),(233,'admin','CREATE','INFO','','','','POST /comercial/ventas/77/eliminar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/77/eliminar/','POST',NULL,'2026-02-26 22:50:48.033919',2),(234,'admin','CREATE','INFO','','','','POST /comercial/ventas/76/editar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/ventas/76/editar/','POST',NULL,'2026-02-26 22:51:30.542321',2),(235,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:52:42.972423',2),(236,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:52:59.573742',2),(237,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:53:09.145530',2),(238,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 22:55:04.041730',2),(239,'admin','CREATE','INFO','','','','POST /comercial/api/pago/25/editar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/api/pago/25/editar/','POST',NULL,'2026-02-26 22:58:07.553233',2),(240,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:04:06.326718',2),(241,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:04:26.952297',2),(242,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:05:53.969788',2),(243,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:06:28.523423',2),(244,'admin','CREATE','INFO','','','','POST /login/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/login/','POST',NULL,'2026-02-26 23:07:57.016121',2),(245,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:08:19.318684',2),(246,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:10:17.334954',2),(247,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:10:35.888323',2),(248,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:10:38.904420',2),(249,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:14:13.271062',2),(250,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:14:15.849835',2),(251,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:19:53.940857',2),(252,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:25:33.980386',2),(253,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:27:59.335933',2),(254,'admin','CREATE','INFO','','','','POST /comercial/api/venta/76/editar-fecha-sena/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/api/venta/76/editar-fecha-sena/','POST',NULL,'2026-02-26 23:34:56.379136',2),(255,'admin','CREATE','INFO','','','','POST /comercial/api/pago/25/eliminar/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/api/pago/25/eliminar/','POST',NULL,'2026-02-26 23:41:18.662840',2),(256,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:42:42.593777',2),(257,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:48:23.212415',2),(258,'admin','CREATE','INFO','','','','POST /comercial/reportes/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/comercial/reportes/','POST',NULL,'2026-02-26 23:48:53.750168',2),(259,'admin','CREATE','INFO','','','','POST /security/backups/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/security/backups/','POST',NULL,'2026-02-27 00:15:25.819171',2),(260,'admin','CREATE','INFO','','','','POST /security/backups/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/security/backups/','POST',NULL,'2026-02-27 00:17:41.385598',2),(261,'admin','CREATE','INFO','','','','POST /security/backups/create/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/security/backups/create/','POST',NULL,'2026-02-27 00:18:23.504714',2),(262,'admin','CREATE','INFO','','','','POST /security/backups/create/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/security/backups/create/','POST',NULL,'2026-02-27 00:18:57.040693',2),(263,'admin','CREATE','INFO','','','','POST /security/backups/create/','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36','/security/backups/create/','POST',NULL,'2026-02-27 00:21:39.143147',2);
/*!40000 ALTER TABLE `security_auditlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `security_backup`
--

DROP TABLE IF EXISTS `security_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_backup` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(500) NOT NULL,
  `size_bytes` bigint NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `error_message` longtext NOT NULL,
  `tables_count` int NOT NULL,
  `records_count` int NOT NULL,
  `created_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `security_backup_created_by_id_41e82d3b_fk_auth_user_id` (`created_by_id`),
  CONSTRAINT `security_backup_created_by_id_41e82d3b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_backup`
--

LOCK TABLES `security_backup` WRITE;
/*!40000 ALTER TABLE `security_backup` DISABLE KEYS */;
INSERT INTO `security_backup` VALUES (1,'','',0,'failed','2026-02-27 00:18:23.445692',NULL,'Error en mysqldump: mysqldump: [ERROR] mysqldump: Empty value for \'port\' specified.\n',0,0,NULL),(2,'','',0,'failed','2026-02-27 00:18:57.005061',NULL,'Error en mysqldump: mysqldump: [ERROR] mysqldump: Empty value for \'port\' specified.\n',0,0,NULL),(3,'','',0,'failed','2026-02-27 00:21:39.087948',NULL,'Error en mysqldump: mysqldump: [Warning] Using a password on the command line interface can be insecure.\nmysqldump: [ERROR] unknown option \'--skip-ssl\'.\n',0,0,NULL),(4,'','',0,'running','2026-02-27 00:23:33.683904',NULL,'',0,0,NULL);
/*!40000 ALTER TABLE `security_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `security_ipblacklist`
--

DROP TABLE IF EXISTS `security_ipblacklist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_ipblacklist` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ip_address` char(39) NOT NULL,
  `reason` longtext NOT NULL,
  `blocked_at` datetime(6) NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `blocked_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_address` (`ip_address`),
  KEY `security_ipblacklist_blocked_by_id_15db8a99_fk_auth_user_id` (`blocked_by_id`),
  CONSTRAINT `security_ipblacklist_blocked_by_id_15db8a99_fk_auth_user_id` FOREIGN KEY (`blocked_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_ipblacklist`
--

LOCK TABLES `security_ipblacklist` WRITE;
/*!40000 ALTER TABLE `security_ipblacklist` DISABLE KEYS */;
/*!40000 ALTER TABLE `security_ipblacklist` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `security_loginattempt`
--

DROP TABLE IF EXISTS `security_loginattempt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_loginattempt` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(150) NOT NULL,
  `ip_address` char(39) NOT NULL,
  `user_agent` longtext NOT NULL,
  `success` tinyint(1) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `security_loginattempt_timestamp_9b315407` (`timestamp`),
  KEY `security_lo_ip_addr_622cb0_idx` (`ip_address`,`timestamp` DESC),
  KEY `security_lo_usernam_6d99d9_idx` (`username`,`timestamp` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_loginattempt`
--

LOCK TABLES `security_loginattempt` WRITE;
/*!40000 ALTER TABLE `security_loginattempt` DISABLE KEYS */;
INSERT INTO `security_loginattempt` VALUES (1,'admin','190.48.205.77','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-18 15:44:32.038022'),(2,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-19 13:53:15.180257'),(3,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',0,'2026-02-19 14:05:54.272718'),(4,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-19 14:06:00.438305'),(5,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-19 18:53:43.846698'),(6,'kiara','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-23 14:26:23.297205'),(7,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 14:33:43.305461'),(8,'kiara','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-23 14:34:32.197581'),(9,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 14:40:09.792267'),(10,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 14:53:28.575543'),(11,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:06:46.051612'),(12,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:09:53.180618'),(13,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:11:53.437142'),(14,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:11:54.147021'),(15,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:12:23.867583'),(16,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:13:58.420094'),(17,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 15:42:59.868281'),(18,'kiara','104.166.164.25','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-23 16:06:10.070023'),(19,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 18:40:46.377872'),(20,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',0,'2026-02-23 18:40:47.096543'),(21,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-23 18:40:56.332415'),(22,'kiara','104.166.164.38','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',1,'2026-02-23 19:21:57.664409'),(23,'Admin','181.238.52.32','Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36',1,'2026-02-24 11:26:56.124581'),(24,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-24 12:15:51.527862'),(25,'admin','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-25 15:35:46.412073'),(26,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-25 15:40:46.296760'),(27,'admin','190.48.203.234','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-25 16:54:34.875400'),(28,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 01:29:06.128561'),(29,'admin','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 13:13:37.673939'),(30,'admin','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 14:33:56.785262'),(31,'admin','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 14:40:18.313802'),(32,'admin','181.30.1.45','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 15:41:56.658983'),(33,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 21:57:14.254434'),(34,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 21:57:36.992912'),(35,'admin','152.168.206.173','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',1,'2026-02-26 23:07:56.993026');
/*!40000 ALTER TABLE `security_loginattempt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `security_securitysettings`
--

DROP TABLE IF EXISTS `security_securitysettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_securitysettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `max_login_attempts` int NOT NULL,
  `lockout_duration` int NOT NULL,
  `session_timeout` int NOT NULL,
  `force_password_change_days` int NOT NULL,
  `min_password_length` int NOT NULL,
  `require_uppercase` tinyint(1) NOT NULL,
  `require_lowercase` tinyint(1) NOT NULL,
  `require_numbers` tinyint(1) NOT NULL,
  `require_special_chars` tinyint(1) NOT NULL,
  `log_all_actions` tinyint(1) NOT NULL,
  `log_retention_days` int NOT NULL,
  `auto_backup_enabled` tinyint(1) NOT NULL,
  `backup_frequency_hours` int NOT NULL,
  `backup_retention_days` int NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `security_securitysettings_updated_by_id_b50801eb_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `security_securitysettings_updated_by_id_b50801eb_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_securitysettings`
--

LOCK TABLES `security_securitysettings` WRITE;
/*!40000 ALTER TABLE `security_securitysettings` DISABLE KEYS */;
INSERT INTO `security_securitysettings` VALUES (1,5,30,60,90,8,1,1,1,0,1,365,0,24,30,'2026-02-17 15:29:59.975973',NULL);
/*!40000 ALTER TABLE `security_securitysettings` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-26 21:23:35
