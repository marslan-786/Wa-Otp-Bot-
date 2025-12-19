# پائتھن کا مستحکم ورژن
FROM python:3.11-slim

# سسٹم لیول کی ضروری لائبریریز انسٹال کریں (libmagic کا مسئلہ یہاں حل ہوگا)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# کام کی جگہ (App Directory)
WORKDIR /app

# تمام فائلیں کاپی کریں
COPY . .

# پائتھن لائبریریز انسٹال کریں
RUN pip install --no-cache-dir -r requirements.txt

# بوٹ کو اسٹارٹ کرنے کی کمانڈ
CMD ["python", "main.py"]