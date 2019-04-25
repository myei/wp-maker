# wp-maker

This is a util script written in python3 for building the context for wordpress applications, considering:

* Database (MySQL or PostgreSQL):
    * Create table
    * Create user with only access to this table
* Apache:
    * VirtualHost
    * Project created under /var/www/html/ with www-data:www-data permissions
* WordPress:
    * Downloading the latest version of WordPress
    * Auto-configuring the wp-config.php file


```shell
Usage of wp-maker:

    wp-maker [site-name]
```

> In order to avoid security issues, it's highly recommended to obfuscate this script once it changes the database parameters on ```WPMaker.DB```. I suggest to use ```pyminifier``` as follows:

```shell
pip3 install pyminifier
pyminifier --pyz wp-maker wp-maker.py
```