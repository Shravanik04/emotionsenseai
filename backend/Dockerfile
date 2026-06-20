FROM python:3.10-slim

# Create user first to set up directories
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface

# Set up working directory inside user home
WORKDIR /home/user/app

# Copy requirements and install
COPY --chown=user requirements.txt /home/user/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy all application code
COPY --chown=user . /home/user/app

# Expose Hugging Face Space port
EXPOSE 7860

# Start FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
