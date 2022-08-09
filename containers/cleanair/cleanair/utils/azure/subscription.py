"""Finding the Urbanair Azure subscription"""

from azure.identity import AzureCliCredential
from azure.mgmt.subscription.models import Subscription
from azure.mgmt.resource.subscriptions import SubscriptionClient
from ...exceptions.exceptions import UrbanairAzureException


URBANAIR_AZURE_SUBSCRIPTION_DISPLAY_NAME = "UrbanAir"


def get_urbanair_az_subscription(credential: AzureCliCredential) -> Subscription:
    """Get a dictionary containing details of the urbanair azure subscriptions

    Args:
        credential: An object used for checking Azure credentials via the Azure CLI

    Returns:
        Dictionary contains subscription information

    Raises:
        UrbanairAzureException: If the urbanair subscription was not found
    """
    subscription_client = SubscriptionClient(credential)
    for subscription in subscription_client.subscriptions.list():
        if subscription.display_name == URBANAIR_AZURE_SUBSCRIPTION_DISPLAY_NAME:
            return subscription
    raise UrbanairAzureException(
        f"The {URBANAIR_AZURE_SUBSCRIPTION_DISPLAY_NAME} Azure subscription was not in the list of your subscriptions"
    )


def get_urbanair_az_subscription_id(credential: AzureCliCredential) -> str:
    """Get the ID of the Urbanair Azure subscription

    Args:
        credential: An object used for checking Azure credentials via the Azure CLI

    Returns:
        ID of the subscription
    """
    return get_urbanair_az_subscription(credential).subscription_id
