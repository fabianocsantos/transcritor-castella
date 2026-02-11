\# Transcritor Castella (Local)



\## O que faz

Transcreve vídeos (Upload, YouTube e Google Drive) gerando:

\- transcript\_raw.txt

\- transcript\_clean.md

\- subtitles.srt

\- meta.json



Organiza por fonte e data automaticamente.



\## Estrutura

\- entrada/    (uploads)

\- saida/      (resultados por job)

\- temp/       (arquivos temporários)

\- docs/       (documentação)

\- releases/   (backups de versões)

\- tools/      (scripts de manutenção)



\## Uso (BAT 1 clique)

Execute: TRANSCRITOR.bat



Opções:

1\) Upload (coloque o vídeo em entrada/)

2\) YouTube (cole link)

3\) Drive (cole link liberado como "qualquer um com o link")



\## Uso (PowerShell)

Ativar venv:

cd C:\\transcritor

.\\.venv\\Scripts\\Activate.ps1



Upload:

python app.py



YouTube:

python app.py --url "LINK"



Drive:

python app.py --drive "LINK"



Modo mais fiel:

--accurate



\## Troubleshooting

\- YouTube 403: o app usa fallback automático.

\- Drive falhando: garantir permissão "qualquer um com o link".



