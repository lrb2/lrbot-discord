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
RUN apt update && apt upgrade -y && apt install ghostscript -y
#    b. Make a folder for the program files
WORKDIR /usr/local/bin/magick.d
#    c. Download the program, make it executable, and extract (making folder squashfs-root)
RUN wget https://imagemagick.org/archive/binaries/magick && chmod +x magick && ./magick --appimage-extract
#    d. Work in the user local binaries folder
WORKDIR /usr/local/bin
#    e. Add a soft link to run ImageMagick
RUN ln -s magick.d/squashfs-root/AppRun magick
## 4. Install Google Chrome for Testing
#    a. Work in the /tmp folder
WORKDIR /tmp
#    b. Get the latest version number and save it to a file
RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json | grep -Po '\d+\.\d+\.\d+\.\d+' | head -1 > chrome-version
#    c. Download the chrome and chromedriver binaries
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/`cat chrome-version`/linux64/chrome-linux64.zip
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/`cat chrome-version`/linux64/chromedriver-linux64.zip
#    d. Unzip archives
RUN unzip chrome-linux64.zip
RUN unzip chromedriver-linux64.zip
#    e. Copy to user local binaries folder
RUN cp -r chrome-linux64 chromedriver-linux64 /usr/local/
#    f. Add chrome to $PATH
ENV PATH "/usr/local/chrome-linux64:$PATH"
ENV PATH "/usr/local/chromedriver-linux64:$PATH"
#    g. Install dependencies (from https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md#chrome-doesnt-launch-on-linux)
RUN apt install -y ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils
#    h. Set display port (from https://stackoverflow.com/a/51266278)
ENV DISPLAY=:0
## 5. Set working directory
WORKDIR /code
## 6. Copy files (will be overwritten by mount)
COPY . .
## 7. Install packages from requirements.txt
RUN pip install -r requirements.txt
## 8. Set startup command
CMD ["python3", "lrbot.py"]