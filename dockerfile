# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

COPY requirements.txt ./requirements.txt

RUN apt-get update
RUN apt-get install -y libgl1

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "final.py", "--server.port", "8501", "--server.address", "0.0.0.0"]