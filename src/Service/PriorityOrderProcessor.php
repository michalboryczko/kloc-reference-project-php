<?php

declare(strict_types=1);

namespace App\Service;

use App\Entity\Order;

/**
 * Priority order processor with elevated processing.
 *
 * Contract test patterns:
 * - Chain of extends: PriorityOrderProcessor -> StandardOrderProcessor -> AbstractOrderProcessor
 * - Method override from non-direct parent
 * - Class with extends and extended (StandardOrderProcessor is middle of chain)
 */
final class PriorityOrderProcessor extends StandardOrderProcessor
{
    /**
     * Override preProcess to mark as priority.
     */
    protected function preProcess(Order $order): void
    {
        $order->status = 'priority_processing';
    }

    /**
     * Override getName for priority processor identification.
     */
    public function getName(): string
    {
        return 'priority';
    }
}
