# Connectinno Case Study

## Technologies Used

- Python 3.11
- Docker
- FastAPI
- Firebase Storage (GCS)
- SQLAlchemy

## Getting started

### Development Environment
1. Install poetry `curl -sSL https://install.python-poetry.org | python3 -`
2. Install uv package manager `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. RUN `poetry install --only-root` to create a new poetry environment
4. RUN `uv pip install -r pyproject.toml`
5. Install pre-commit and ruff linter `uv pip install pre-commit ruff`
6. RUN `pre-commit install`
7. RUN `pre-commit run`

### Running inside Docker Engine
**Install Docker Engine**
```bash
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```
Verify that Docker Engine is installed correctly by running the `hello-world` image.
```bash
sudo docker run hello-world
```

**Compile Images**

After you have installed docker-engine and docker-compose,

```bash
cp .env.example .env
sudo docker compose build
```
> **Note:** make sure to tweak .env file according to your preferences

### Running Services

After you have compiled the images successfully do the following:

1. Add service account JSON file to resources folder and make sure to exclude the file from git, you just have to include `firebase-adminsdk` in file name.
2. Update `GOOGLE_APPLICATION_CREDENTIALS` environment variable and point it to service account JSON filepath.
3. Run the following commands
    ```bash
    sudo docker compose up -d
    sudo docker compose exec web alembic upgrade head
    ```
Now you can access the API [documentation](http://localhost:20002/api/v1/docs/) in your browser.

### Common errors
- An error related to `*.sh` script not found
  1. Change line endings for the related script in `docker` directory to LF(Unix)
  2. Rebuild the image

### Running Tests
```bash
sudo docker compose up -d
sudo docker compose exec web pytest
```

## System Design

- **Repository pattern:** A simplifying abstraction over data storage that hide the complexity of DB operations from the client.
- **UoW pattern:** It’s a nice place to put all your repositories so client code can access them. It helps to enforce the consistency of our domain model, and improves performance, by letting us perform a single flush operation at the end of an operation
- **Inverting the Dependency:** ORM Depends on Model not the other way around i.e. high-level modules (the domain) should not depend on low-level ones (the infrastructure)
- **Dependency Injection**: It adds flexibility as the components are loosely coupled and can be easily swapped with mocks or fakes. Also, enhances code maintainability by clearly defining where dependencies are used and making it easier to identify and update them when needed.
- **Factory pattern:** Use factory method to abstract filesystems behaviour and let the client rely on a single interface `AbstractFileSystem`. Hence, we can easily migrate to `s3` or `local` simply by changing the injected factory
