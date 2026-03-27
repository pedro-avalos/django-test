from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.people.models import Person


class Subscription(models.Model):
    """Model representing a subscription to another object."""

    modified_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    subscriber = models.ForeignKey(Person, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "subscriber"],
                name="unique_subscription_per_subscriber_and_object",
            )
        ]

    def __str__(self):
        return f"Subscription of {self.subscriber} to {self.content_object}"


class Notification(models.Model):
    """Shared notification content for all subscribers of an object."""

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    title = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return f"Notification for {self.content_object}: {self.title}"

    @classmethod
    def send_to_subscribers(cls, content_object, *, title: str, message: str):
        """Create one shared notification and deliver it to matching subscribers."""

        content_type = ContentType.objects.get_for_model(
            content_object, for_concrete_model=False
        )
        subscriptions = Subscription.objects.filter(
            content_type=content_type,
            object_id=content_object.pk,
        )

        notification = cls.objects.create(
            content_type=content_type,
            object_id=content_object.pk,
            title=title,
            message=message,
        )

        NotificationDelivery.objects.bulk_create(
            [
                NotificationDelivery(
                    notification=notification, subscription=subscription
                )
                for subscription in subscriptions
            ]
        )
        return notification


class NotificationDelivery(models.Model):
    """Delivery state for each subscriber receiving a shared notification."""

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
    )
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "subscription"],
                name="unique_delivery_per_subscription",
            )
        ]

    def __str__(self):
        return f"Delivery for {self.subscription}: {self.notification}"
