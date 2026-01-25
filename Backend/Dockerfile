# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Run the application
# Using python -m flask run or directly python app.py if it has app.run
# app.py has app.run(debug=True, port=5000)
CMD ["python", "app.py"]
