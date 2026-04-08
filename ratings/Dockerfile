# 
# Build the app
#
FROM php:8.2-apache-bookworm

RUN a2enmod rewrite && a2enmod status

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -yqq unzip libzip-dev git && \
    docker-php-ext-install pdo_mysql opcache zip

RUN echo "instana.enable_auto_profile=1" > "/usr/local/etc/php/conf.d/zzz-instana-extras.ini"

COPY status.conf /etc/apache2/mods-available/status.conf
RUN a2enmod rewrite && a2enmod status

WORKDIR /var/www/html

COPY html/ /var/www/html

COPY --from=composer /usr/bin/composer /usr/bin/composer

RUN composer install --no-interaction --optimize-autoloader

RUN rm -Rf /var/www/var/*
RUN chown -R www-data /var/www
RUN chmod -R 777 /var/www
