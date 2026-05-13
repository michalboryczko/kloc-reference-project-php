<?php

declare(strict_types=1);

namespace App\Ui\EventSubscriber;

use App\Event\ReportGeneratedEvent;
use App\Service\NotificationService;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

/**
 * Subscribes to report domain events.
 *
 * Contract test patterns:
 * - EventSubscriberInterface implementation (detected via kernel.event_subscriber tag)
 * - getSubscribedEvents() resolves event → method mapping
 * - Creates event flow: Subscriber → NotificationService → Repository
 * - Cross-flow target: triggered by CLI flow via EventDispatcherInterface
 */
final readonly class ReportEventSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private NotificationService $notificationService,
    ) {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            ReportGeneratedEvent::class => 'onReportGenerated',
        ];
    }

    public function onReportGenerated(ReportGeneratedEvent $event): void
    {
        $this->notificationService->notifyOrderCreated(0);
    }
}
