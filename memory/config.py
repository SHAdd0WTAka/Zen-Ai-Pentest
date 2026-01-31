"""
Memory system configuration
"""
MEMORY_CONFIG = {
    'default_storage': 'sqlite',
    'sqlite': {
        'db_path': 'data/memory.db'
    },
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    },
    'conversation_memory': {
        'max_history': 20,
        'persist': True
    },
    'working_memory': {
        'max_items': 50,
        'persist': False
    },
    'cleanup': {
        'auto_cleanup': True,
        'max_session_age_hours': 24
    }
}
