import logging
import logging.config


def configure_logger(no_rich, cqrs_ids=[]):
    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '%(asctime)s %(name)s %(levelname)s PID_%(process)d %(message)s',
                },
                'rich': {
                    'format': '%(cqrs_signal)s %(cqrs_id)s [%(cqrs_instance_pk)s] %(message)s',
                },
            },
            'filters': {},
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
                'rich': {
                    'class': 'rich.logging.RichHandler',
                    'formatter': 'rich',
                    'log_time_format': lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'rich_tracebacks': False,
                    'show_level': False,
                    'show_time': False,
                    'show_path': False,
                    'keywords': ['SAVE', 'SYNC', 'DELETE'] + list(cqrs_ids),


                },
            },
            'loggers': {
                'cqrscap': {
                    'handlers': ['console'] if no_rich else ['rich'],
                    'level': 'INFO',
                },
            },
        },
    )