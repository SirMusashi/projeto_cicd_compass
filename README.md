# Projeto CI/CD com GitHub Actions e ArgoCD (Monorepo)
## Objetivo do Projeto

### Automatizar o ciclo completo de desenvolvimento, build, deploy e execução de uma aplicação FastAPI simples, utilizando uma abordagem de monorepo. As tecnologias chave incluem GitHub Actions para CI/CD , Docker Hub como registry , e ArgoCD para entrega contínua em Kubernetes.

---

## Pré-requisitos e Setup do Ambiente

* **Conta no Docker Hub e Token de Acesso** : O Docker Hub atua como nosso Container Registry, armazenando as imagens Docker da aplicação.  O token de acesso é crucial para permitir que o GitHub Actions autentique e envie as imagens de forma segura. 
       
     Acesse https://hub.docker.com/ e crie uma conta ou faça login.

    Para criar o token:

     * Clique no seu nome de usuário no canto superior direito e vá para Account Settings.

     * No menu à esquerda, clique em Security.

     * Clique no botão New Access Token.

     * Clique em Generate.

* **Git** : Sistema de controle de versão usado para gerenciar todo o código-fonte e histórico do projeto. 
    ```bash
        git --version
    ```    
* **Python 3 e Docker** : Ferramentas fundamentais para desenvolver a aplicação FastAPI e para construir e executar os contêineres da aplicação, respectivamente.
    ```bash
        python3 --version
    ```   
* **Rancher Desktop com Kubernetes** : Fornece um ambiente Kubernetes local, permitindo simular um ambiente de produção para deploy e testes. Adiquirir em https://rancherdesktop.io/ .
* **`kubectl`** : A ferramenta de linha de comando padrão para interagir com o cluster Kubernetes, usada para verificar o status dos deploys e outros recursos.
* **ArgoCD** : A ferramenta de GitOps que sincroniza o estado do cluster com os manifestos declarados no repositório, automatizando a entrega contínua.

    ```Bash
        # 1. Cria um "namespace" (uma área isolada) para o ArgoCD
        kubectl create namespace argocd

        # 2. Instala o ArgoCD nesse namespace
        kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    ```

    ![Kubectl](imagens/01_kubectl_01.jpg)


## Etapa 1: Estrutura do Projeto (Monorepo)

Este projeto utiliza uma abordagem de monorepo, onde todos os artefatos (código da aplicação e manifestos de deploy) residem em um único repositório Git. A estrutura é a seguinte:

*  Pasta **/app** : Contém todo o código-fonte da aplicação FastAPI, o `Dockerfile` para a containerização e as dependências Python.

```py
# main.py

from fastapi import FastAPI 

app = FastAPI() 

@app.get("/") 
async def root(): 
    return {"message": "Hello World"} 
```

```Dockerfile
# Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```
* Pasta **/manifests** : Conterá os manifestos do Kubernetes (`deployment.yaml`, `service.yaml`) que definem como a aplicação deve ser executada no cluster. Esta pasta é a "fonte da verdade" para o ArgoCD.

## Etapa 2: Automação com GitHub Actions (CI)

Foi configurado um workflow de Integração Contínua (`CI`) em `.github/workflows/ci-cd.yml`. Este processo é acionado automaticamente a cada `push` de alterações na pasta `/app` da branch `main`.

```YAML
name: CI/CD - Build e Push imagem de Docker e Update do Manifest

on:
  push:
    branches:
      - main
    paths:
      - 'app/**'

jobs:
  build-push-and-update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login no Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Gerar image tag
        id: generate_tag
        run: echo "tag=$(echo ${GITHUB_SHA} | cut -c1-7)" >> $GITHUB_OUTPUT

      - name: Build e push
        uses: docker/build-push-action@v5
        with:
          context: ./app
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:${{ steps.generate_tag.outputs.tag }}
          cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:buildcache
          cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:buildcache,mode=max

      - name: Update Kubernetes manifest
        run: |
          sed -i 's|image:.*|image: ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:${{ steps.generate_tag.outputs.tag }}|' manifests/deployment.yaml

      - name: Commit e push mudanças no manifest 
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add manifests/deployment.yaml
          git commit -m "ci: update image tag to ${{ steps.generate_tag.outputs.tag }}"
          git push
```

O workflow realiza as seguintes tarefas:
1.  Constrói uma imagem Docker da aplicação.
2.  Envia a imagem para o Docker Hub com uma tag única baseada no hash do commit.
3.  Atualiza o arquivo de manifesto (`manifests/deployment.yaml`) com a nova tag da imagem.
4.  Faz o commit e push da atualização do manifesto de volta para o repositório.

Para que o workflow se autentique no Docker Hub, os seguintes `secrets` foram configurados no repositório:
* `DOCKER_USERNAME`
* `DOCKER_PASSWORD`

![github01](imagens/02_github_01.jpg) 

![github02](imagens/03_github_02.jpg)