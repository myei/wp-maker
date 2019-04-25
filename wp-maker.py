import random
import string

from os import system, makedirs, rename, remove
from os.path import exists
from shutil import move, chown
from sys import argv as args
from blessings import Terminal
from sqlalchemy import create_engine
from pathlib2 import Path
from wget import download
from zipfile import ZipFile


class WPMaker:

    APACHE = {
        'path': '/var/www/html/',
        'port': 80,
        'sa': '/etc/apache2/sites-available/'
    }

    DB = {
        'user': 'root',
        'psw': '12345',
        'host': 'localhost',
        'port': 3306,
        'driver': 'mysql'
    }

    WP_PATH = 'https://ve.wordpress.org/latest-es_VE.zip'

    def __init__(self, site_name):
        self._name = site_name
        self._db = self._name.split('.')[0]

        if not self.check_prerequisites():
            exit(6)

    def _connect(self):
        try:
            engine = create_engine('{driver}://{user}:{psw}@{host}:{port}/{driver}'.format(**self.DB))
            self._conn = engine.connect()
            self._conn.execute('commit')
        except Exception as e:
            print(e)
            print(t.bold_red('Error trying to connect to {}, please verify your credentials'.format(self.DB['driver'])))
            exit(1)

    @staticmethod
    def _random_str(limit=18):
        text = ''.join([random.choice(string.ascii_letters + string.digits + string.punctuation) for n in range(limit)])
        return text.replace('%', '').replace('\\', '').replace('"', '').replace('\'', '')

    def _build_db(self):
        self._connect()

        try:
            self._psw = self._random_str()

            self._conn.execute('CREATE DATABASE {}'.format(self._db))
            self._conn.execute('CREATE USER {}@{} IDENTIFIED BY "{}"'.format(self._db, self.DB['host'], self._psw))
            self._conn.execute('GRANT ALL PRIVILEGES ON {db} . * TO {db}@{host}'.format(db=self._db, host=self.DB['host']))
        except Exception as e:
            print(t.bold_red('Error trying to build database'), e)
            exit(2)

    def _rollback(self):
        self._conn.execute('DROP DATABASE {}'.format(self._db))
        self._conn.execute('DROP USER {}@{}'.format(self._db, self.DB['host']))

    def _build_apache(self):
        try:
            with open('{}{}.conf'.format(self.APACHE['sa'], self._name), 'a') as vh:
                vh.write('<VirtualHost *:{port}> \n'
                         '\tServerAdmin webmaster@getout.com \n'
                         '\tServerName {page} \n'
                         '\tServerAlias www.{page} \n\n'
                         '\tDocumentRoot {path}{page} \n\n'
                         '\t<Directory /> \n'
                         '\t\tOptions FollowSymLinks \n'
                         '\t\tAllowOverride All \n'
                         '\t</Directory> \n'
                         '\t<Directory {path}{page}> \n'
                         '\t\tOptions Indexes FollowSymLinks MultiViews \n'
                         '\t\tAllowOverride All \n'
                         '\t\tOrder allow,deny \n'
                         '\t\tallow from all \n'
                         '\t</Directory> \n'
                         '</VirtualHost>'.format(page=self._name, **self.APACHE))

            system('a2ensite {} 1>/dev/null'.format(self._name))
            system('service apache2 restart 2>/dev/null')
        except Exception as e:
            self._rollback()
            print(t.bold_red('Error trying to build apache context, rolling back database changes...'), e.args)
            exit(3)

    def _build_wp(self):
        try:
            path = '{}{}/'.format(self.APACHE['path'], self._name)

            print(t.bold_yellow('> getting wordpress'))
            download(self.WP_PATH, self._name)
            print(t.bold_yellow('> uncompressing'))
            ZipFile(self._name, 'r').extractall()
            remove(self._name)
            print(t.bold_yellow('> setting up site'))
            move('wordpress', path)
            chown(path, 'www-data', 'www-data')

            rename('{}wp-config-sample.php'.format(path), '{}wp-config.php'.format(path))

            path = Path('{}wp-config.php'.format(path))
            text = path.read_text()
            text = text.replace('database_name_here', self._name)
            text = text.replace('username_here', self._name)
            text = text.replace('password_here', self._psw)
            text = text.replace('put your unique phrase here', self._random_str(50))
            path.write_text(text)
        except Exception as e:
            self._rollback()
            print(t.bold_red('Error trying to build wordpress context, rolling back database changes...'), e)
            exit(3)

    @staticmethod
    def yes_or_no(question):
        try:
            choices = {'y': True, 'n': False}
            choice = str(input(t.bold_yellow(question + ' (y/n): '))).lower().strip()

            return choices.get(choice) if choice in choices else WPMaker.yes_or_no(question)
        except:
            print(t.bold_red('\n\nERROR: you must type y or n'))
            exit(4)

    def _clean(self):
        self._conn.close()
        system('clear')

    def check_prerequisites(self):
        if exists(self.APACHE['path'] + self._name):
            print(t.bold_red('The path: {}{} already exists'.format(self.APACHE['path'], self._name)))
        elif not exists(self.APACHE['sa']):
            print('The path: {} doesn\'t exists, needed for VirtualHost'.format(self.APACHE['sa']))
        else:
            return True

    def make(self):
        if not self.yes_or_no('Are you sure about creating this site: ' + t.bold_blue_italic(self._name) + '?'):
            exit(5)

        print(t.bold_blue("\nBuilding {}...\n".format(self._name)))

        self._build_db()
        self._build_wp()
        self._build_apache()

        self._clean()

        print(t.bold_green('Successfully created context for:\n'))
        print(t.bold('  Site:'), t.bold_cyan('\t' + self._name))
        print(t.bold('  Path:'), t.bold_cyan('\t' + self.APACHE['path'] + self._name))
        print(t.bold('  VirtualHost:'), t.bold_cyan('\t {}{}.conf'.format(self.APACHE['sa'], self._name)), '\n')
        print('', t.bold_underline('Database:\n'))
        print(t.bold('  You can check the details on:'), t.bold_yellow('wp-config.php'))


if __name__ == '__main__':
    t = Terminal()

    if len(args) is 1:
        print('Usage of wp-maker:\n')
        print('\twp-maker [site-name]\n')
    else:
        maker = WPMaker(args[1])
        maker.make()
