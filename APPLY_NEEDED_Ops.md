# перезапуск оркестратора/бэкенда
/opt/feature-factory/bin/ff-orch-restart-safe

# ожидаем x-correlation-id в заголовках:
curl -si https://etl-tst.chococraft.ru/health/live  | sed -n '1,15p'
curl -si https://etl-tst.chococraft.ru/health/ready | sed -n '1,15p'
curl -si https://etl-tst.chococraft.ru/openapi.json | sed -n '1,8p'

# проверка corr-id на «известной 500»:
curl -si "https://etl-tst.chococraft.ru/api/v1/index/calls?limit=1" | sed -n '1,20p'