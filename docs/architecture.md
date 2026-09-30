[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-verification-engine"
version = "0.1.0"
description = "Evidence-backed verification and debugging platform for autonomous coding agents"
readme = "README.md"
requires-python = ">=3.10"
authors = [{ name = "Wilker00" }]
license = { text = "MIT" }
classifiers = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Framework :: FastAPI",
]

dependencies = [
  "fastapi>=0.110.0",
  "uvicorn[standard]>=0.29.0",
  "pydantic>=2.7.0",
  "httpx>=0.27.0",
]

[project.optional-dependencies]
agent = [
  "nvidia-nat>=1.0.0",
  "wandb>=0.16.0",
  "opentelemetry-api>=1.25.0",
]

dev = [
  "pytest>=8.0.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.5.0",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
