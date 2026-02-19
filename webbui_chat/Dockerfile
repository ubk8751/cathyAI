FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY users.py .
COPY auth_api.py .
COPY bootstrap_admin.py .
COPY chainlit.md .
COPY ../.chainlit ./.chainlit
EXPOSE 8000
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
