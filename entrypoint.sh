#!/bin/sh

echo "--- Verificando variáveis de ambiente ---"
echo "DATABASE_URL encontrada: [${DATABASE_URL}]"
echo "--- Fim da verificação ---"

# Aplica as migrações do banco de dados
echo "Aplicando migrações do banco de dados..."
python manage.py migrate --no-input

# Coleta os arquivos estáticos para o Whitenoise servir
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

# Inicia o servidor Gunicorn
# O bind 0.0.0.0:10000 é o que o Render espera.
echo "Iniciando o servidor Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:10000