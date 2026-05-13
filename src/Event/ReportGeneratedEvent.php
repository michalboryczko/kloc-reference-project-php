<?php

declare(strict_types=1);

namespace App\Event;

/**
 * Domain event dispatched when a report is generated.
 *
 * Contract test patterns:
 * - Event class used with EventDispatcherInterface
 * - Triggers event flow: ReportEventSubscriber listens for this
 */
final readonly class ReportGeneratedEvent
{
    public function __construct(
        public string $reportId,
        public string $reportType,
    ) {
    }
}
