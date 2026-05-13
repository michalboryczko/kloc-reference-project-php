<?php

declare(strict_types=1);

namespace App\Service;

use App\Event\ReportGeneratedEvent;
use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

/**
 * Service for generating reports.
 *
 * Contract test patterns:
 * - Injects EventDispatcherInterface (trigger detection for event flows)
 * - Part of CLI flow: ProcessReportsCommand → ReportService
 * - Dispatches ReportGeneratedEvent → triggers event flow
 */
final readonly class ReportService
{
    public function __construct(
        private EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function generateReport(string $type): string
    {
        $reportId = uniqid('report_', true);

        $this->eventDispatcher->dispatch(
            new ReportGeneratedEvent($reportId, $type),
        );

        return $reportId;
    }
}
