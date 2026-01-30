FROM python:3.12-slim

WORKDIR /app

COPY quiz_gen.py /app/quiz_gen.py
COPY questions.json /app/questions.json
COPY README.md /app/README.md

# (optional) folder pt rezultate în container
RUN mkdir -p /app/results

# Programul pornește ca un CLI tool
ENTRYPOINT ["python", "quiz_gen.py"]
CMD ["--help"]
