@echo off
setlocal enabledelayedexpansion

set "SRC=%~dp0skills"
set "DEST=%USERPROFILE%\.claude\skills"

echo Instalando Offers RAG Search...

if not exist "%SRC%\offers-rag-search\SKILL.md" (
    echo ERRO: nao encontrei skills\offers-rag-search\SKILL.md ao lado deste instalador.
    pause
    exit /b 1
)

if not exist "%DEST%" (
    mkdir "%DEST%"
)

if exist "%DEST%\offers-rag-search" (
    rmdir /s /q "%DEST%\offers-rag-search"
)
xcopy "%SRC%\offers-rag-search" "%DEST%\offers-rag-search" /e /i /y >nul

if exist "%DEST%\offers-rag-search\SKILL.md" (
    echo.
    echo Offers RAG Search instalado com sucesso!
    echo Disponivel em qualquer pasta/sessao do Claude Code a partir de agora.
    echo O indice em si (dados + venv) fica em Ferramentas\offers-rag\ - a skill so aponta pra la.
) else (
    echo ERRO: falha ao copiar os arquivos da skill.
)

pause
