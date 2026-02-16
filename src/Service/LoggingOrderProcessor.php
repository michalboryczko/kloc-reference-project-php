<?php

declare(strict_types=1);

namespace App\Service;

use App\Component\AuditableInterface;
use App\Entity\Order;

/**
 * Order processor with audit logging.
 *
 * Contract test patterns:
 * - Class with extends + implements (AbstractOrderProcessor + AuditableInterface)
 * - Override abstract methods from parent
 * - Implement interface methods not from parent
 */
final class LoggingOrderProcessor extends AbstractOrderProcessor implements AuditableInterface
{
    /** @var array<string> */
    private array $auditLog = [];

    protected function preProcess(Order $order): void
    {
        $this->auditLog[] = 'preProcess:' . $order->id;
        $order->status = 'logging_preprocess';
    }

    protected function doProcess(Order $order): void
    {
        $this->auditLog[] = 'doProcess:' . $order->id;
        $order->status = 'logged_completed';
    }

    public function getName(): string
    {
        return 'logging';
    }

    /**
     * @return array<string>
     */
    public function getAuditLog(): array
    {
        return $this->auditLog;
    }
}
