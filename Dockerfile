FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y --no-install-recommends locales python3 python3-pip tzdata

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV TZ=Europe/Kiev

ARG WORKDIR=/checkbox451_bot

ARG ADMIN
ARG DB_DIR=$WORKDIR

ARG TOKEN

ARG LOGIN
ARG PASSWORD
ARG LICENSE_KEY
ARG API_URL

ARG PRINTER_CONFIG
ARG PRINT_WIDTH
ARG PRINT_BOTTOM_MARGIN
ARG PRINT_LOGO_PATH
ARG PRINT_LOGO_IMPL

ARG GOOGLE_APPLICATION_CREDENTIALS
ARG GOOGLE_SPREADSHEET_KEY
ARG GOOGLE_WORKSHEET_TITLE

ENV ADMIN=$ADMIN
ENV DB_DIR=$DB_DIR

ENV TOKEN=$TOKEN

ENV LOGIN=$LOGIN
ENV PASSWORD=$PASSWORD
ENV LICENSE_KEY=$LICENSE_KEY
ENV API_URL=$API_URL

ENV PRINTER_CONFIG=$PRINTER_CONFIG
ENV PRINT_WIDTH=$PRINT_WIDTH
ENV PRINT_BOTTOM_MARGIN=$PRINT_BOTTOM_MARGIN
ENV PRINT_LOGO_PATH=$PRINT_LOGO_PATH
ENV PRINT_LOGO_IMPL=$PRINT_LOGO_IMPL

ENV GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
ENV GOOGLE_SPREADSHEET_KEY=$GOOGLE_SPREADSHEET_KEY
ENV GOOGLE_WORKSHEET_TITLE=$GOOGLE_WORKSHEET_TITLE

WORKDIR $WORKDIR
COPY . $WORKDIR
RUN pip3 install .

CMD python3 -m checkbox451_bot
