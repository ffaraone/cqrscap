import click

from cqrscap.capturer import CapturerApp
from cqrscap.logger import Logger
from cqrscap.utils import configure_logger


@click.command()
@click.argument(
    'cqrs_ids',
    nargs=-1,
)
@click.option(
    '-H',
    '--host',
    default='localhost',
    help='RabbitMQ host',
)
@click.option(
    '-P',
    '--port',
    default=5672,
    help='RabbitMQ port',
)
@click.option(
    '-u',
    '--username',
    default='admin',
    help='RabbitMQ username',
)
@click.option(
    '-p',
    '--password',
    help='RabbitMQ password',
)
@click.option(
    '-e',
    '--exchange',
    default='cqrs',
    help='RabbitMQ exchange',
)
@click.option(
    '-c',
    '--capture',
    default=False,
    is_flag=True,
    help='Show capture console',
)
def start(cqrs_ids, host, port, username, password, exchange, capture):
    if capture:
        app = CapturerApp(cqrs_ids or ['*'], host, port, username, password, exchange)
        app.run()
    else:
        configure_logger(False, cqrs_ids or [])
        logger = Logger(cqrs_ids or ['*'], host, port, username, password, exchange)
        logger.run()



def main(
):
    """
    Tail the log of pods that match the given PATTERNS.
    """
    try:
        start(prog_name='cqrstail', standalone_mode=False)
    except click.Abort:
        pass
    except Exception as e:
        click.secho(f'\n{e}', fg='red', err=True)


if __name__ == '__main__':  # pragma: no cover
    main()



