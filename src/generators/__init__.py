"""Code generators for Ethereum clients."""

from .geth import GethGenerator

GENERATORS = {
    "geth": GethGenerator,
}


def get_generator(client_name: str):
    """Get generator instance for a client.

    Args:
        client_name: Name of the client (e.g., 'geth')

    Returns:
        Generator instance

    Raises:
        ValueError: If client is not supported
    """
    generator_class = GENERATORS.get(client_name)
    if not generator_class:
        raise ValueError(f"Unknown client: {client_name}")
    return generator_class()
