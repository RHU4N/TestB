# Use uma imagem base Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo de requisitos e instale as dependências
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da sua aplicação para o contêiner
COPY . .

# Exponha a porta que a aplicação Flask usa
EXPOSE 5000

# Comando para rodar a aplicação quando o contêiner iniciar
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]