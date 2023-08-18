# syntax=docker/dockerfile:1
## 1. Start with Python in Debian 12
FROM python:3.11-bookworm
## 2. Add a non-root user (from https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user#_creating-a-nonroot-user)
#    a. Set parameters
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
#    b. Create the user and allow it to use sudo without a password
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && mkdir /etc/sudoers.d \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME