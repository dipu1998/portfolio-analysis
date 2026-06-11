# =============================================================
# Dockerfile — WealthTech Portfolio Service
# =============================================================
# A Dockerfile is a recipe. It tells Docker step-by-step how
# to build a "container image" of your app.
#
# ANALOGY: Think of it like packing a tiffin box.
# You put rice, dal, sabzi in a specific order.
# Anyone who gets that tiffin box gets the exact same meal.
# Docker image = that tiffin box. Your app + everything it needs.
# =============================================================


# -------------------------------------------------------------
# INSTRUCTION 1: FROM
# -------------------------------------------------------------
# FROM = "start with this base image"
# A base image is a pre-built starting point. Like choosing
# which type of empty tiffin box to use.
#
# python:3.11-slim = official Python image, "slim" version
#   - "3.11"  = Python version 3.11 (stable, not 3.13 to avoid issues)
#   - "slim"  = minimal Ubuntu with only Python installed
#               (no extra bloat — keeps image small)
#
# We use 3.11 here specifically because it avoids the pydantic
# compatibility issues we saw with 3.13 on your laptop.
# In Docker, we control the Python version — so we pick 3.11.
# -------------------------------------------------------------
FROM python:3.11-slim


# -------------------------------------------------------------
# INSTRUCTION 2: WORKDIR
# -------------------------------------------------------------
# WORKDIR = sets the "current directory" inside the container.
# Like doing: cd /app
# All following commands (COPY, RUN) happen inside this folder.
#
# /app is the standard convention for Python web apps in Docker.
# The /app folder is created automatically if it doesn't exist.
# -------------------------------------------------------------
WORKDIR /app


# -------------------------------------------------------------
# INSTRUCTION 3: COPY requirements.txt FIRST (before code)
# -------------------------------------------------------------
# COPY <source on your laptop> <destination inside container>
#
# WHY copy requirements.txt separately before the rest of code?
# This is a Docker optimization called LAYER CACHING.
#
# Docker builds in layers. Each instruction = one layer.
# If a layer hasn't changed, Docker reuses the cached version.
#
# requirements.txt changes rarely (only when you add packages).
# Your code (main.py) changes often.
#
# By copying requirements.txt first and running pip install,
# Docker caches the "installed packages" layer.
# Next time you build (after changing main.py only),
# Docker skips re-installing packages — much faster builds!
#
# If you copied everything together first, every code change
# would trigger a full pip install. Slow.
# -------------------------------------------------------------
COPY requirements.txt .


# -------------------------------------------------------------
# INSTRUCTION 4: RUN pip install
# -------------------------------------------------------------
# RUN = execute a shell command during the BUILD phase.
# (Not when the container runs — during building the image.)
#
# pip install -r requirements.txt = install all packages listed
# --no-cache-dir = don't store pip's download cache inside image
#                  saves ~50MB of unnecessary space in image
#
# After this step, fastapi and uvicorn are installed
# inside the container's Python environment.
# -------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt


# -------------------------------------------------------------
# INSTRUCTION 5: COPY the rest of the application code
# -------------------------------------------------------------
# COPY . . = copy EVERYTHING from your current folder (laptop)
#            into the WORKDIR (/app) inside the container.
#
# First  "." = source  (your laptop's current directory)
# Second "." = destination (container's /app directory)
#
# This copies: main.py, and any other files you have.
# It does NOT copy files listed in .dockerignore (see that file).
# -------------------------------------------------------------
COPY . .


# -------------------------------------------------------------
# INSTRUCTION 6: EXPOSE
# -------------------------------------------------------------
# EXPOSE = tells Docker "this container listens on port 8000"
#
# IMPORTANT: EXPOSE is just documentation. It doesn't actually
# open the port by itself. The actual port opening happens when
# you run the container with -p flag.
#
# But it's important for:
# 1. Other developers reading the Dockerfile to know the port
# 2. Kubernetes — it reads EXPOSE to configure services
# 3. Docker Compose — uses it for automatic port linking
# -------------------------------------------------------------
EXPOSE 8000


# -------------------------------------------------------------
# INSTRUCTION 7: CMD
# -------------------------------------------------------------
# CMD = the command that runs when the container STARTS.
# This is your app's startup command.
#
# Format: CMD ["executable", "arg1", "arg2"]
# (Using JSON array format — the recommended way)
#
# uvicorn main:app = run uvicorn server, pointing to
#   "main"    = the file main.py
#   "app"     = the FastAPI object named "app" inside main.py
#
# --host 0.0.0.0 = listen on ALL network interfaces
#   Inside a container, 127.0.0.1 (localhost) only accepts
#   connections from INSIDE the container.
#   0.0.0.0 means "accept connections from outside too"
#   (i.e., from your laptop, from Kubernetes, from internet)
#   Without this, your app runs but NOBODY can reach it!
#
# --port 8000 = listen on port 8000
#
# NOTE: No "reload=True" here! reload is for development only.
# In production containers, we don't use reload.
# -------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]