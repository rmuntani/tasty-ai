FROM python:3.11-slim-bookworm

WORKDIR /code

# COPY requirements.txt .

RUN pip3 install -U langgraph "langchain[anthropic]"
RUN pip3 install -U langchain-google-genai
RUN pip3 install -U fastmcp
RUN pip3 install -U chromadb
RUN pip3 install -U genai
RUN pip3 install -U pillow
RUN pip3 install -U google-genai


COPY . .

CMD ["python", "main.py"]
