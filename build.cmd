Remove-Item -Recurse -Force build, dist, Pulsar.spec

flet pack `
    -i src\data\Logo.ico `
    -n "Pulsar" `
    --add-data "src\data;data" `
    --pyinstaller-build-args "--onedir" `
    src\app.py