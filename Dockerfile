FROM python
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["deleteRunPods.py"]
ENTRYPOINT ["python3"]