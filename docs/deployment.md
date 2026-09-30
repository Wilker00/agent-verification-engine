# Backend Deployment

The backend is a stateless FastAPI service. It requires no database, GPU, Nebius SDK, or NVIDIA package on the request path.

## Local container

```bash
docker build -t agent-verification-engine .
docker run --rm -p 8000:8000 agent-verification-engine
curl http://localhost:8000/health
```

The container reads `HOST` and `PORT`; their defaults are `0.0.0.0` and `8000`.

## Nebius path

1. Create a Nebius Container Registry and configure its Docker credential helper.
2. Tag and push the image to `cr.<region>.nebius.cloud/<registry>/<image>:<tag>`.
3. Create a Nebius Container VM using that custom image.
4. Expose container port `8000` only to the networks that need the analysis API.
5. Confirm `GET /health`, then submit a fixture to `POST /analyze`.

Nebius documents the registry workflow in its [Container Registry quickstart](https://docs.nebius.com/container-registry/quickstart) and custom-image deployment in [Container virtual machines](https://docs.nebius.com/compute/virtual-machines/containers).

No deployment is created automatically by this repository. Cloud authentication, project selection, networking, and resource lifecycle remain explicit operator actions.
