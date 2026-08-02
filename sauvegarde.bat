@echo off
REM Sauvegarde automatique de la base de donnees TechShop
REM Pour programmer: Planificateur de taches Windows -> Nouvelle tache
REM   Programme : C:\techshop\sauvegarde.bat
REM   Declencheur: Quotidien (ex: 02:00)

cd /d C:\techshop
venv\Scripts\python.exe manage.py backup_db >> backups\sauvegarde.log 2>&1
