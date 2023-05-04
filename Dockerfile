# syntax=docker/dockerfile:1
## 1. Start with Python in Debian 11
FROM python:3.11-bullseye
## 2. Install TeX Live
#    a. Work in the /tmp folder
WORKDIR /tmp
#    b. Download installer and extract
RUN wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz -O - | tar -xz
#    c. Install TeX Live
RUN perl install-tl-*/install-tl --no-interaction --no-doc-install --no-src-install --texdir=/usr/local/texlive
#RUN perl install-tl-*/install-tl --no-interaction --paper=letter --no-doc-install --no-src-install --texdir=/usr/local/texlive
#    d. Add TeX Live binaries to $PATH
ENV PATH "/usr/local/texlive/bin/x86_64-linux:$PATH"
#    e. Set default paper size to letter. It currently seems to error for ConTeXt, so added '|| true' to continue. Remove if 'tlmgr paper letter' succeeds without errors.
RUN texconfig paper letter || true
## 3. Install ImageMagick (workaround for no AppImage in Docker containers)
#    a. Install Ghostscript for PDF support
RUN apt update && apt install ghostscript -y
#    b. Make a folder for the program files
WORKDIR /usr/local/bin/magick.d
#    c. Download the program, make it executable, and extract (making folder squashfs-root)
RUN wget https://imagemagick.org/archive/binaries/magick && chmod +x magick && ./magick --appimage-extract
#    d. Work in the user local binaries folder
WORKDIR /usr/local/bin
#    e. Add a soft link to run ImageMagick
RUN ln -s magick.d/squashfs-root/AppRun magick
## 4. Set working directory
WORKDIR /code
## 5. Copy files (will be overwritten by mount)
COPY . .
## 6. Install packages from requirements.txt
RUN pip install -r requirements.txt
## 7. Set startup command
CMD ["python3", "lrbot.py"]