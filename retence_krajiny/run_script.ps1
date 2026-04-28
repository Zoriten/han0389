# PowerShell script to run the landscape retention script
# This script activates the conda environment and runs main.py with proper environment variables

# Set execution policy if needed (uncomment if required)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate conda environment
& 'C:\Users\Alttr\miniconda3\shell\condabin\conda-hook.ps1'
conda activate pgis2

# Set environment variables for PROJ and GDAL
$env:PROJ_DATA = 'C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\proj'
$env:PROJ_LIB = 'C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\proj'
$env:GDAL_DATA = 'C:\Users\Alttr\miniconda3\envs\pgis2\Library\share\gdal'
$env:PATH = 'C:\Users\Alttr\miniconda3\envs\pgis2\Library\bin;' + $env:PATH

# Set console to UTF-8 for proper diacritics display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Run the main Python script
python main.py

# Pause to keep window open
Read-Host 'Stlačte Enter pre ukončenie'
