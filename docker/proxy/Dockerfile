FROM nginx:1.23.0-alpine
COPY ./nginx/* /etc/nginx/
COPY ./run.sh /run.sh

ENV APP_HOST=app
ENV APP_PORT=9000

RUN apk add --no-cache openssl bash

USER root

RUN mkdir -p /vol/static /vol/web/media && \
    chmod 755 /vol/static vol/web/media && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh


VOLUME /vol/static
VOLUME /vol/www

CMD ["/run.sh"]