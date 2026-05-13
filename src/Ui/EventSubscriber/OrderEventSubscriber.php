<?php

declare(strict_types=1);

namespace App\Ui\EventSubscriber;

use App\Event\OrderCreatedEvent;
use App\Service\NotificationService;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

/**
 * Subscribes to order domain events.
 *
 * Contract test patterns:
 * - EventSubscriberInterface implementation (detected via kernel.event_subscriber tag)
 * - getSubscribedEvents() resolves event → method mapping
 * - Creates event flow: Subscriber → NotificationService → Repository
 * - Cross-flow target: triggered by HTTP flow via EventDispatcherInterface
 */
final readonly class OrderEventSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private NotificationService $notificationService,
    ) {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            OrderCreatedEvent::class => 'onOrderCreated',
        ];
    }

    public function onOrderCreated(OrderCreatedEvent $event): void
    {
        $this->notificationService->notifyOrderCreated($event->orderId);
    }
}
