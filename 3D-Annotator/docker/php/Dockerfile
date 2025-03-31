# Usa l'immagine ufficiale di PHP con Apache
FROM php:8.2-apache

# Installa estensioni e moduli PHP necessari
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Abilita i moduli di Apache se necessario
RUN a2enmod rewrite

# Copia il file di configurazione PHP personalizzato
COPY ./docker/php/custom-php.ini /usr/local/etc/php/conf.d/

# Imposta la directory di lavoro
WORKDIR /var/www/html

# Copia i file del progetto nella directory di Apache
COPY ./src /var/www/html/src
COPY ./public /var/www/html/public
COPY ./views /var/www/html/views
RUN chmod -R 0777 /var/www/html/src
