import abc

class BaseDevice(abc.ABC):
    """Abstract base class for all device types."""

    @abc.abstractmethod
    async def connect(self, client):
        """Connect to the device."""
        raise NotImplementedError

    @abc.abstractmethod
    async def disconnect(self):
        """Disconnect from the device."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_data(self):
        """Get data from the device."""
        raise NotImplementedError 