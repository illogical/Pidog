# Docker Deployment Instructions for Whisper Voice-to-Text Server

This guide explains how to deploy your Whisper voice-to-text server using Docker, making it accessible from any device on your local network.

## Prerequisites

1. Install Docker on your host system
   - Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: Follow the [official installation guide](https://docs.docker.com/engine/install/)

2. If you have an NVIDIA GPU and want to use it (recommended for better performance):
   - Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## Project Structure

Create a new directory for the Docker project and set up the following files:

```
whisper-server/
├── Dockerfile
├── requirements.txt
├── server.py
└── docker-compose.yml
```

Copy the content of each file from the provided artifacts.

## Deployment Options

### Option 1: Using Docker Compose (Recommended)

1. Navigate to your project directory:
   ```bash
   cd whisper-server
   ```

2. Build and start the container:
   ```bash
   docker-compose up -d
   ```

3. To change the Whisper model, edit the `WHISPER_MODEL` environment variable in `docker-compose.yml` or override it:
   ```bash
   WHISPER_MODEL=medium docker-compose up -d
   ```

### Option 2: Using Docker Directly

1. Build the Docker image:
   ```bash
   docker build -t whisper-server .
   ```

2. Run the container:
   ```bash
   docker run -d -p 5000:5000 -e WHISPER_MODEL=base --name whisper-server whisper-server
   ```

3. For GPU support:
   ```bash
   docker run -d -p 5000:5000 -e WHISPER_MODEL=base --gpus all --name whisper-server whisper-server
   ```

## Accessing the Server

Once the container is running, the server will be accessible at:
```
http://<your-host-ip>:5000
```

Where `<your-host-ip>` is the IP address of the computer running Docker. You can find this by running `ipconfig` (Windows) or `ip addr` (Linux).

## Testing the Server

From any device on your network:

1. Visit `http://<your-host-ip>:5000` in a web browser to see the server welcome page

2. Test with curl:
   ```bash
   curl -X POST -F "audio=@your-audio-file.wav" http://<your-host-ip>:5000/transcribe
   ```

3. Use the client script from your main guide (adjust the URL to point to your server's IP)

## Monitoring and Management

- View logs:
  ```bash
  docker logs -f whisper-server
  ```

- Stop the server:
  ```bash
  docker-compose down
  ```
  or
  ```bash
  docker stop whisper-server
  ```

## Notes on Model Selection

Choose your model based on available resources:

| Model | VRAM Required | Accuracy | Disk Space |
|-------|--------------|----------|------------|
| tiny  | ~1GB         | Basic    | ~75MB      |
| base  | ~1.5GB       | Good     | ~145MB     |
| small | ~2.5GB       | Better   | ~465MB     |
| medium| ~5GB         | Excellent| ~1.5GB     |
| large | ~10GB        | Best     | ~3GB       |

For CPU-only systems, stick with `tiny` or `base` models as larger models will be extremely slow without GPU acceleration.

## Troubleshooting

1. **Out of memory errors**: 
   - Try a smaller model by changing `WHISPER_MODEL` environment variable
   - Increase Docker's memory allocation in Docker Desktop settings

2. **GPU not being used**:
   - Verify NVIDIA Container Toolkit is properly installed
   - Run `nvidia-smi` to check if your GPU is detected
   - Ensure docker-compose.yml contains the proper GPU configuration

3. **Container exits immediately**:
   - Check logs with `docker logs whisper-server`
   - Verify Python dependencies are correct in requirements.txt

4. **Can't connect from other devices**:
   - Check your firewall settings and allow port 5000
   - Verify you're using the correct host IP address
   - Try pinging the host from the client device
