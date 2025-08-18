# Dockerfile (Version V7 - Standardization and FreeCAD Installation Fix)
FROM ubuntu:22.04

# Setup to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary system packages
# IMPORTANT: Install FreeCAD from Ubuntu's apt-get repository
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    freecad \
    python3.10-venv \
    python3-pip \
    xvfb \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create Python virtual environment
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Update pip and install Python libraries
# NOTE: "freecad" has been removed from this list
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    ezdxf \
    matplotlib \
    svgutils

# Set the working directory
WORKDIR /app

# Copy scripts into the container
# These are the scripts you wrote, they will be packaged into the image
COPY scripts/ /app/scripts/

# Grant execute permissions to the scripts
RUN chmod +x /app/scripts/*.py

# Define the default command to be run when the container starts.
# This command will be executed by "docker run" in the run.sh file
CMD ["python", "/app/scripts/pipeline.py"]