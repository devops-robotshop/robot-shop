# 
# Build the app
#
FROM php:8.2-apache-bookworm

RUN a2enmod rewrite && a2enmod status

RUN apt-get update && apt-get install -y \
    unzip libzip-dev git \
    && docker-php-ext-install pdo_mysql opcache zip

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

COPY html/ /var/www/html

RUN composer install --no-interaction --optimize-autoloader --ignore-platform-reqs --no-scripts

COPY status.conf /etc/apache2/mods-available/status.conf

RUN rm -rf /var/www/var/*
RUN chown -R www-data /var/www
RUN chmod -R 777 /var/www
