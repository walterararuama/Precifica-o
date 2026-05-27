@echo off
title Compilando Precificacao...
echo.
echo ============================================
echo  Compilando Bruno Eletromoveis - Precificacao
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Limpando builds anteriores...
if exist "dist\Precificacao.exe" del /f /q "dist\Precificacao.exe"
if exist "build\Precificacao" rmdir /s /q "build\Precificacao"

echo [2/2] Compilando (aguarde, pode demorar alguns minutos)...
python -m PyInstaller Precificacao.spec --clean --noconfirm

echo.
if exist "dist\Precificacao.exe" (
    echo ============================================
    echo  SUCESSO! Executavel gerado em:
    echo  dist\Precificacao.exe
    echo ============================================
    echo.
    echo Copie APENAS o arquivo Precificacao.exe
    echo para a pasta onde os usuarios usam o sistema.
) else (
    echo ============================================
    echo  ERRO: O executavel nao foi gerado.
    echo  Verifique as mensagens acima.
    echo ============================================
)
echo.
pause
