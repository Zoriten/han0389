@echo off
chcp 65001 >nul
call conda activate pgis2
set PROJ_DATA=C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\proj
set PROJ_LIB=C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\proj
set GDAL_DATA=C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\gdal
set PATH=C:\Users\Alttr\miniconda3\envs\pgis2\Library\bin;%PATH%
python main.py
pause