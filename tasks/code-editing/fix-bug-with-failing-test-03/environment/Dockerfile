FROM harbor-agents-prebaked:latest

COPY palindrome.py /app/palindrome.py
COPY tests/test_palindrome.py /app/tests/test_palindrome.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_palindrome.py /opt/canonical/test_palindrome.py

RUN pip install --no-cache-dir pytest==8.4.1
